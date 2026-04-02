import streamlit as st
from datetime import datetime
import io

def generar_iss_identico(nombre_pwb, ancho, alto, componentes):
    ahora = datetime.now().strftime("%Y-%m-%dT%H:%M:%S-07:00")
    total_comp = len(componentes)
    
    # ESTRUCTURA EXACTA BASADA EN TUS ARCHIVOS ORIGINALES
    xml_content = f"""<?xml version="1.0" encoding="utf-8"?>
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
    <headPlacement total="{total_comp}" completion="0" />
  </headerData>
  <core>
    <pwbData>
      <pwb>
        <pwbId>{nombre_pwb}</pwbId>
        <outline x="{ancho}" y="{alto}" />
        <origin x="0" y="0" />
        <posOffset x="0" y="0" />
        <angle>0</angle>
        <fIdMarkUse>0</fIdMarkUse>
        <badMarkUse>0</badMarkUse>
      </pwb>
    </pwbData>
    <placementData>"""

    for i, c in enumerate(componentes, 1):
        xml_content += f"""
      <item no="{i}">
        <placementId>{c['id']}</placementId>
        <componentName>{c['part']}</componentName>
        <x>{c['x']}</x>
        <y>{c['y']}</y>
        <angle>{c['rot']}</angle>
        <machineNo>1</machineNo>
        <headNo>1</headNo>
        <nozzleType>110</nozzleType>
        <feederNo>{(i % 50) + 1}</feederNo>
        <supplySide>LF</supplySide>
        <headPlacement total="1" completion="0" />
      </item>"""

    xml_content += """
    </placementData>
    <componentData />
    <feederSetup>
      <machine no="1">"""

    # Bloque de Feeders con contadores de error en cero (Requerido por Janet)
    for i in range(1, 51):
        xml_content += f"""
        <feeder no="{i}">
          <supplySide>LF</supplySide>
          <numberOfError>
            <pick success="0" error="0" retryOver="0" />
            <place success="0" />
            <compo error="0" scrap="0" angle="0" takeOut="0" fall="0" />
            <dimension error="0" />
            <laser error="0" />
            <vision error="0" />
            <copla error="0" />
            <colinearity error="0" />
            <verify error="0" />
            <tombstone error="0" />
            <leadBend error="0" />
            <pickPos error="0" />
            <posture error="0" />
            <other error="0" />
          </numberOfError>
        </feeder>"""

    xml_content += """
      </machine>
    </feederSetup>
  </core>
</productionProgram>"""
    return xml_content

def extraer_datos(xml_content):
    import xml.etree.ElementTree as ET
    root = ET.fromstring(xml_content)
    board = root.find('board')
    comp_reales, fidus = [], []
    for comp in root.findall('.//component'):
        d = {'id': comp.get('name'), 'part': comp.get('part'), 'x': comp.get('x'), 'y': comp.get('y'), 'rot': str(int(float(comp.get('rot'))))}
        if "FID" in d['id'].upper() or "FID" in d['part'].upper(): fidus.append(d)
        else: comp_reales.append(d)
    return board, comp_reales, fidus

# --- INTERFAZ ---
st.title("Generador ISS Dialight (Identidad Total)")
file = st.file_uploader("Archivo .KYPcb", type=["KYPcb"])

if file:
    board, componentes, fidus = extraer_datos(file.read())
    iss_final = generar_iss_identico(board.get('name'), board.get('w'), board.get('h'), componentes)
    
    txt_datos = "\n".join([f"{c['id']},{c['part']},{c['x']},{c['y']},{c['rot']}" for c in componentes])
    txt_fidu = "\n".join([f"{f['id']},{f['part']},{f['x']},{f['y']},{f['rot']}" for f in fidus])

    st.download_button("Descargar .ISS Idéntico", iss_final, file_name="PROGRAMA_GENERADO.iss")
    st.download_button("Descargar DATOS .TXT", txt_datos, file_name="DATOS_LIMPIOS.txt")
    st.download_button("Descargar FIDU .TXT", txt_fidu, file_name="FIDUCIALES.txt")
