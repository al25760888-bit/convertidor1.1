import streamlit as st
from datetime import datetime
import io

def formatear_iss_exacto(nombre_pwb, ancho, alto, componentes):
    """Genera el XML con la sintaxis exacta de los archivos de Dialight."""
    ahora = datetime.now().strftime("%Y-%m-%dT%H:%M:%S-07:00")
    
    # Encabezado idéntico a tus muestras
    xml_header = f"""<?xml version="1.0" encoding="utf-8"?>
<productionProgram>
  <headerData>
    <targetMachine>ISS</targetMachine>
    <targetVersion revision="15" version="3" level="0" />
    <programMode>0</programMode>
    <editMachine>ISS</editMachine>
    <editVersion revision="10" version="0" level="0" />
    <lastEdit>{ahora}</lastEdit>
    <lastOptimized>{ahora}</lastOptimized>
    <lineConfiguration>
      <lineName id="2">Line 2</lineName>
      <configuration>
        <machine no="1">
          <typeCode>3020VA</typeCode>
          <subTypeId>75</subTypeId>
          <name>3020VAL</name>
          <typeName />
          <conveyorLane>SINGLE</conveyorLane>
          <relationStringUse>1</relationStringUse>
          <machineRelationString />
          <stationUnit id="1">
            <bankUnit kind="1" position="1" drivingType="1" bankOption="1" attributeIndex="1" />
            <bankUnit kind="2" position="1" drivingType="1" bankOption="1" attributeIndex="1" />
          </stationUnit>
        </machine>
      </configuration>
    </lineConfiguration>
  </headerData>
  <core>
    <pwbData>
      <pwb>
        <pwbId>{nombre_pwb}</pwbId>
        <outline x="{ancho}" y="{alto}" />
      </pwb>
    </pwbData>
    <placementData>"""

    # Generación de items de componentes
    items_xml = ""
    for i, c in enumerate(componentes, 1):
        items_xml += f"""
      <item no="{i}">
        <placementId>{c['id']}</placementId>
        <componentName>{c['part']}</componentName>
        <x>{c['x']}</x>
        <y>{c['y']}</y>
        <angle>{c['rot']}</angle>
        <machineNo>1</machineNo>
        <headNo>1</headNo>
        <nozzleType>110</nozzleType>
        <feederNo>{(i % 40) + 1}</feederNo>
        <supplySide>LF</supplySide>
      </item>"""

    # Cierre del archivo
    xml_footer = """
    </placementData>
  </core>
</productionProgram>"""

    return xml_header + items_xml + xml_footer

def procesar_archivo(content):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(content)
    board = root.find('board')
    
    comp_reales = []
    fidus = []
    
    for comp in root.findall('.//component'):
        datos = {
            'id': comp.get('name'),
            'part': comp.get('part'),
            'x': comp.get('x'),
            'y': comp.get('y'),
            'rot': str(int(float(comp.get('rot'))))
        }
        if "FID" in datos['id'].upper() or "FID" in datos['part'].upper():
            fidus.append(datos)
        else:
            comp_reales.append(datos)
            
    iss_final = formatear_iss_exacto(board.get('name'), board.get('w'), board.get('h'), comp_reales)
    
    txt_out = "\n".join([f"{c['id']},{c['part']},{c['x']},{c['y']},{c['rot']}" for c in comp_reales])
    fidu_out = "\n".join([f"{f['id']},{f['part']},{f['x']},{f['y']},{f['rot']}" for f in fidus])
    
    return iss_final, txt_out, fidu_out

# --- INTERFAZ STREAMLIT ---
st.title("Generador ISS Universal (Sintaxis Real)")

archivo = st.file_uploader("Sube tu archivo .KYPcb", type=["KYPcb"])

if archivo:
    iss_content, txt_content, fidu_content = procesar_archivo(archivo.read())
    
    st.download_button("Descargar .ISS (Sintaxis Dialight)", iss_content, file_name="PROGRAMA_OK.iss")
    st.download_button("Descargar DATOS .TXT (Sin encabezado)", txt_content, file_name="DATOS.txt")
    st.download_button("Descargar FIDUCIALES .TXT", fidu_content, file_name="FIDUS.txt")
