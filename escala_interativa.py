
import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

st.set_page_config(layout="centered")
st.title("🧾 Teste de Exportação Excel - Estrutura Limpa")

# Exemplo de dados simulados para exportar
df = pd.DataFrame([
    {"Dia": "Segunda (01/04)", "Turno": "Manhã", "Agentes": "Ana, João, Carla, Leo", "Anhanguera": "Ana, João", "Dom Pedro": "Carla, Leo"},
    {"Dia": "Segunda (01/04)", "Turno": "Tarde", "Agentes": "Marcelo, Jack", "Anhanguera": "", "Dom Pedro": ""},
    {"Dia": "Terça (02/04)", "Turno": "Manhã", "Agentes": "Ana, João", "Anhanguera": "", "Dom Pedro": ""}
])

contagem_df = pd.DataFrame([
    {"Agente": "Ana", "Turnos": 2},
    {"Agente": "João", "Turnos": 2},
    {"Agente": "Carla", "Turnos": 1},
    {"Agente": "Leo", "Turnos": 1},
    {"Agente": "Marcelo", "Turnos": 1},
    {"Agente": "Jack", "Turnos": 1},
])

st.markdown("### 🔍 Escala simulada")
st.dataframe(df)

st.markdown("### 📊 Turnos por agente")
st.dataframe(contagem_df)

output = BytesIO()
wb = Workbook()
ws = wb.active
ws.title = "Escala de Campo"

# Cabeçalho
titulo = "Escala Semanal (01/04 - 05/04/2025)"
ws.merge_cells("A1:E1")
ws["A1"] = titulo
ws["A1"].font = Font(bold=True)
ws["A1"].alignment = Alignment(horizontal='center')

headers = ["Dia", "Turno", "Agentes", "Anhanguera", "Dom Pedro"]
ws.append(headers)

# Preencher escala
for i, row in df.iterrows():
    linha = [row["Dia"], row["Turno"], row["Agentes"], row["Anhanguera"], row["Dom Pedro"]]
    ws.append(linha)
    for col in range(1, 6):
        ws.cell(row=ws.max_row, column=col).alignment = Alignment(horizontal='center', vertical='center')

# Espaço e tabela AACA
ws.append([])
ws.append(["Agente", "Turnos"])
for i, row in contagem_df.iterrows():
    ws.append([row["Agente"], row["Turnos"]])

wb.save(output)
output.seek(0)

st.download_button("📥 Baixar planilha de exemplo", data=output, file_name="escala_modelo_limpo.xlsx")
