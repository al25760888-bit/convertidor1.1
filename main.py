import streamlit as st
import xml.etree.ElementTree as ET
import datetime
import io
import re

def clean_placement_data(components):
    """"""
    return [c for c in components if "FIDU" not in c['name'].upper()]

def parse_txt_coordinates(content):
    """
    Intenta parsear un archivo TXT de coordenadas. 
    Busca patrones comunes: Designator X Y Angle Part
    """
    components = []
    lines = content.decode('utf-8').splitlines()
    for line in lines:
        # Dividir por espacios, comas o tabs
        parts = re.split(r'\s+|,\s*', line.strip())
        if len(parts) >= 4:
            # Intento básico de identificar si la línea tiene coordenadas numéricas
            try:
                # Ejemplo esperado: C1 10.5 20.2 90 ComponentName
                name = parts[0]
                x = parts[1]
                y = parts[2]
                rot = parts[3]
                part = parts[4] if len(parts) > 4 else "UNKNOWN"
                
                # Validar que X e Y sean números
                float(x)
                float(y)
                
                components.append({'name': name, 'x': x, 'y': y, 'rot': rot, 'part': part})
            except ValueError:
                continue # Saltar líneas de encabezado
    return components

def generate_iss_xml(components, board_info):
    production_program = ET.Element("productionProgram")
    header = ET.SubElement(production_program, "headerData")
    ET.SubElement(header, "targetMachine").text = "ISS"
    ET.SubElement(header, "lastEdit").text = datetime.datetime.now().isoformat()
    
    core = ET.SubElement(production_program, "core")
    pwb_data = ET.SubElement(core, "pwbData")
    ET.SubElement(pwb_data, "pwbId").text = board_info.get('name', 'Board')
    pwb_config = ET.SubElement(pwb_data, "pwbConfiguration")
    ET.SubElement(pwb_config, "outline", x=board_info.get('w', '0'), y=board_info.get('h', '0'))

    placement_data = ET.SubElement(core, "placementData")
    for index, comp in enumerate(components):
        placement = ET.SubElement(placement_data, "placement", index=str(index))
        ET.SubElement(placement, "placementId").text = comp['name']
        ET.SubElement(placement, "baseCircuitId").text = "A"
        ET.SubElement(placement, "componentName").text = comp['part']
        ET.SubElement(placement, "placementPosition", x=comp['x'], y=comp['y'], rangeOver="False")
        ET.SubElement(placement, "placementAngle", angle=comp['rot'])
        attr = ET.SubElement(placement, "attribute")
        ET.SubElement(attr, "skip", placement="NO", adhesive="NO")

    output_tree = ET.ElementTree(production_program)
    ET.indent(output_tree, space="  ", level=0)
    buffer = io.BytesIO()
    output_tree.write(buffer, encoding="utf-8", xml_declaration=True)
    return buffer.getvalue()

def generate_txt_report(components, board_info):
    output = io.StringIO()
    output.write(f"REPORTE DE MONTAJE - JANET\n")
    output.write(f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    output.write(f"Placa: {board_info.get('name', 'N/A')}\n")
    output.write("-" * 50 + "\n")
    output.write(f"{'Designator':<15} {'X':<10} {'Y':<10} {'Rot':<10} {'Part':<20}\n")
    output.write("-" * 50 + "\n")
    for c in components:
        output.write(f"{c['name']:<15} {c['x']:<10} {c['y']:<10} {c['rot']:<10} {c['part']:<20}\n")
    return output.getvalue()

# --- Interfaz Streamlit ---
st.set_page_config(page_title="Convertidor Universal Dialight", layout="wide")
st.title("⚙️ Convertidor Universal (KYPcb / TXT) a Janet ISS")
st.info("Este programa filtra automáticamente los componentes 'FIDU' y genera archivos listos para producción.")

uploaded_file = st.file_uploader("Sube tu archivo (.KYPcb o .txt)", type=["KYPcb", "txt", "xml"])

if uploaded_file:
    components = []
    board_info = {'name': uploaded_file.name, 'w': '200', 'h': '200'}
    content = uploaded_file.read()

    try:
        if uploaded_file.name.lower().endswith(('.kypcb', '.xml')):
            root = ET.fromstring(content)
            board_node = root.find('board')
            if board_node is not None:
                board_info['w'] = board_node.get('w', '200')
                board_info['h'] = board_node.get('h', '200')
            
            raw_comps = root.findall('.//component')
            for c in raw_comps:
                components.append({
                    'name': c.get('name', ''),
                    'x': c.get('x', '0'),
                    'y': c.get('y', '0'),
                    'rot': c.get('rot', '0'),
                    'part': c.get('part', 'UNKNOWN')
                })
        else:
            # Procesar como TXT
            components = parse_txt_coordinates(content)

        # APLICAR FILTRO FIDU
        final_components = clean_placement_data(components)
        
        st.success(f"Procesados {len(final_components)} componentes (Se eliminaron {len(components) - len(final_components)} Fiduciales).")

        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Generar Archivos")
            if st.button("Preparar Descargas"):
                iss_file = generate_iss_xml(final_components, board_info)
                report_file = generate_txt_report(final_components, board_info)
                
                st.download_button("📥 Descargar Archivo .ISS", data=iss_file, 
                                   file_name=uploaded_file.name.rsplit('.', 1)[0] + ".iss")
                
                st.download_button("📥 Descargar Reporte .TXT (Para Imprimir)", data=report_file, 
                                   file_name="Reporte_Montaje_" + uploaded_file.name.rsplit('.', 1)[0] + ".txt")

        with col2:
            st.subheader("Vista Previa")
            st.dataframe(final_components, height=300)

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")