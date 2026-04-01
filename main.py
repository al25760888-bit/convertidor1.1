import streamlit as st
import xml.etree.ElementTree as ET
import datetime
import io

def convert_kypcb_to_iss(xml_content):
    # Parsear el contenido del archivo subido
    root = ET.fromstring(xml_content)

    # Extraer datos básicos de la placa (KohYoung)
    board_node = root.find('board')
    board_name = board_node.get('name', 'Converted_Board')
    width = board_node.get('w', '0')
    height = board_node.get('h', '0')

    # Crear la estructura raíz del archivo .iss (Juki ISS)
    production_program = ET.Element("productionProgram")
    
    # Cabecera
    header = ET.SubElement(production_program, "headerData")
    ET.SubElement(header, "targetMachine").text = "ISS"
    ET.SubElement(header, "lastEdit").text = datetime.datetime.now().isoformat()
    
    # Cuerpo del programa
    core = ET.SubElement(production_program, "core")
    
    # Datos del panel
    pwb_data = ET.SubElement(core, "pwbData")
    ET.SubElement(pwb_data, "pwbId").text = board_name
    pwb_config = ET.SubElement(pwb_data, "pwbConfiguration")
    ET.SubElement(pwb_config, "outline", x=width, y=height)

    # Datos de colocación (Placement)
    placement_data = ET.SubElement(core, "placementData")
    
    # Buscar todos los componentes en el KYPcb
    components = root.findall('.//component')
    
    for index, comp in enumerate(components):
        placement = ET.SubElement(placement_data, "placement", index=str(index))
        
        designator = comp.get('name', f'COMP{index}')
        part_name = comp.get('part', 'UNKNOWN')
        pos_x = comp.get('x', '0')
        pos_y = comp.get('y', '0')
        angle = comp.get('rot', '0')

        ET.SubElement(placement, "placementId").text = designator
        ET.SubElement(placement, "baseCircuitId").text = "A"
        ET.SubElement(placement, "componentName").text = part_name
        ET.SubElement(placement, "placementPosition", x=pos_x, y=pos_y, rangeOver="False")
        ET.SubElement(placement, "placementAngle", angle=angle)
        
        attr = ET.SubElement(placement, "attribute")
        ET.SubElement(attr, "skip", placement="NO", adhesive="NO")

    # Generar el XML final
    output_tree = ET.ElementTree(production_program)
    ET.indent(output_tree, space="  ", level=0)
    
    # Guardar en un buffer de memoria para la descarga
    buffer = io.BytesIO()
    output_tree.write(buffer, encoding="utf-8", xml_declaration=True)
    return buffer.getvalue()

# --- Interfaz de Streamlit ---
st.set_page_config(page_title="Convertidor KYPcb a ISS", page_icon="⚙️")

st.title("🔄 Convertidor Universal de Archivos SMT")
st.write("Sube tu archivo **.KYPcb** de KohYoung para generar el archivo **.iss** compatible con Janet.")

uploaded_file = st.file_uploader("Selecciona el archivo .KYPcb", type=["KYPcb", "xml"])

if uploaded_file is not None:
    try:
        # Leer el archivo
        file_bytes = uploaded_file.read()
        
        if st.button("Generar archivo .iss"):
            iss_data = convert_kypcb_to_iss(file_bytes)
            
            # Nombre del archivo de salida basado en el original
            output_filename = uploaded_file.name.replace(".KYPcb", "").replace(".xml", "") + ".iss"
            
            st.success(f"✅ Conversión exitosa para: {uploaded_file.name}")
            
            st.download_button(
                label="📥 Descargar archivo .iss para Janet",
                data=iss_data,
                file_name=output_filename,
                mime="application/octet-stream"
            )
            
    except Exception as e:
        st.error(f"Hubo un error al procesar el archivo: {e}")

st.divider()
st.info("Nota: Este programa mapea automáticamente coordenadas X, Y, Rotación y Nombres de componentes.")