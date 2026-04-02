import streamlit as st
import xml.etree.ElementTree as ET
from datetime import datetime
import io

def procesar_pcb(xml_content):
    # Cargar el contenido XML
    root = ET.fromstring(xml_content)
    board = root.find('board')
    board_name = board.get('name') if board is not None else "Unknown_PCB"
    width = board.get('w') if board is not None else "0"
    height = board.get('h') if board is not None else "0"
    
    componentes_reales = []
    fiduciales = []
    
    # 1. Clasificación: Componentes vs Fiduciales
    for comp in root.findall('.//component'):
        datos = {
            'id': comp.get('name'),
            'part': comp.get('part'),
            'x': comp.get('x'),
            'y': comp.get('y'),
            'rot': comp.get('rot').split('.')[0]
        }
        
        # Filtro de Fiduciales
        if "FID" in datos['id'].upper() or "FID" in datos['part'].upper():
            fiduciales.append(datos)
        else:
            componentes_reales.append(datos)

    # --- GENERAR ISS (XML) ---
    iss_root = ET.Element("productionProgram")
    header = ET.SubElement(iss_root, "headerData")
    ET.SubElement(header, "targetMachine").text = "ISS"
    ET.SubElement(header, "targetVersion", revision="15", version="3", level="0")
    ET.SubElement(header, "lastEdit").text = datetime.now().strftime("%Y-%m-%dT%H:%M:%S-07:00")
    
    line_cfg = ET.SubElement(header, "lineConfiguration")
    line_name = ET.SubElement(line_cfg, "lineName", id="2")
    line_name.text = "Line 2"
    
    core = ET.SubElement(iss_root, "core")
    pwb_data = ET.SubElement(core, "pwbData")
    pwb = ET.SubElement(pwb_data, "pwb")
    ET.SubElement(pwb, "pwbId").text = board_name
    ET.SubElement(pwb, "outline", x=width, y=height)
    
    placement = ET.SubElement(core, "placementData")
    for i, c in enumerate(componentes_reales):
        item = ET.SubElement(placement, "item", no=str(i+1))
        ET.SubElement(item, "placementId").text = c['id']
        ET.SubElement(item, "componentName").text = c['part']
        ET.SubElement(item, "x").text = c['x']
        ET.SubElement(item, "y").text = c['y']
        ET.SubElement(item, "angle").text = c['rot']
        ET.SubElement(item, "nozzleType").text = "110"
        ET.SubElement(item, "feederNo").text = str((i % 40) + 1)

    iss_string = ET.tostring(iss_root, encoding='utf-8', method='xml')

    # --- GENERAR TXT (DATOS LIMPIOS) ---
    txt_output = io.StringIO()
    for c in componentes_reales:
        txt_output.write(f"{c['id']},{c['part']},{c['x']},{c['y']},{c['rot']}\n")
    
    # --- GENERAR FIDU ---
    fidu_output = io.StringIO()
    for f in fiduciales:
        fidu_output.write(f"{f['id']},{f['part']},{f['x']},{f['y']},{f['rot']}\n")

    return iss_string, txt_output.getvalue(), fidu_output.getvalue()

# --- INTERFAZ STREAMLIT ---
st.set_page_config(page_title="Convertidor ISS Dialight", page_icon="⚙️")
st.title("⚙️ Convertidor KYPcb a ISS (Janet)")
st.write("Sube tu archivo Koh Young para generar los formatos necesarios.")

uploaded_file = st.file_uploader("Elige un archivo .KYPcb", type="KYPcb")

if uploaded_file is not None:
    content = uploaded_file.read()
    iss_file, txt_file, fidu_file = procesar_pcb(content)
    
    st.success("¡Archivo procesado con éxito!")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            label="Descargar .ISS",
            data=iss_file,
            file_name=uploaded_file.name.replace(".KYPcb", ".iss"),
            mime="application/xml"
        )
    
    with col2:
        st.download_button(
            label="Descargar DATOS .TXT",
            data=txt_file,
            file_name=uploaded_file.name.replace(".KYPcb", "_DATOS.txt"),
            mime="text/plain"
        )
        
    with col3:
        st.download_button(
            label="Descargar FIDU .TXT",
            data=fidu_file,
            file_name=uploaded_file.name.replace(".KYPcb", "_FIDU.txt"),
            mime="text/plain"
        )

    st.divider()
    st.subheader("Previsualización de Componentes")
    st.text(txt_file[:500] + "...")