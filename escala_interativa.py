import streamlit as st
import pandas as pd
import random
from collections import defaultdict
from io import BytesIO

st.title("Gerador de Escala de Turnos Personalizado")

st.write("Preencha os dados abaixo para gerar sua escala semanal.")

# Entradas básicas
dias_semana = st.number_input("Quantos dias de escala?", min_value=1, max_value=7, value=5)
turnos_por_dia = st.number_input("Quantos turnos por dia?", min_value=1, max_value=4, value=2)
pessoas_por_turno = st.number_input("Quantas pessoas por turno?", min_value=1, max_value=10, value=2)
num_pessoas = st.number_input("Quantos participantes?", min_value=2, max_value=20, value=6)

# Informar nomes e turnos por pessoa
st.subheader("Participantes e seus turnos semanais")
nomes = []
limites = {}

with st.form("form_participantes"):
    for i in range(int(num_pessoas)):
        col1, col2 = st.columns([2, 1])
        nome = col1.text_input(f"Nome do participante {i+1}", key=f"nome_{i}")
        turnos = col2.number_input(f"Turnos semanais para {nome or 'participante'}", min_value=1, max_value=dias_semana*turnos_por_dia, value=1, key=f"turno_{i}")
        if nome:
            nomes.append(nome)
            limites[nome] = turnos
    submitted = st.form_submit_button("Gerar Escala")

if submitted:
    dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'][:dias_semana]
    turnos = [f"Turno {i+1}" for i in range(turnos_por_dia)]

    def gerar_escala():
        escala = {(dia, turno): [] for dia in dias for turno in turnos}
        contagem = defaultdict(int)

        for dia in dias:
            for turno in turnos:
                while len(escala[(dia, turno)]) < pessoas_por_turno:
                    candidatos = [p for p in nomes if contagem[p] < limites[p] and p not in escala[(dia, turno)]]
                    if not candidatos:
                        return None, None
                    escolhido = random.choice(candidatos)
                    escala[(dia, turno)].append(escolhido)
                    contagem[escolhido] += 1
        return escala, contagem

    escala, contagem = gerar_escala()

    if escala:
        st.success("Escala gerada com sucesso!")

        data = []
        for dia in dias:
            linha = {'Dia': dia}
            for turno in turnos:
                linha[turno] = ', '.join(escala[(dia, turno)])
            data.append(linha)
        df = pd.DataFrame(data)
        st.dataframe(df.set_index('Dia'))

        contagem_df = pd.DataFrame.from_dict(contagem, orient='index', columns=['Turnos']).sort_index()
        st.subheader("Turnos por pessoa")
        st.dataframe(contagem_df)

        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Escala')
            contagem_df.to_excel(writer, sheet_name='Turnos_por_Pessoa')
        output.seek(0)

        st.download_button("Baixar escala em Excel", data=output, file_name="escala_personalizada.xlsx")
    else:
        st.error("Não foi possível gerar uma escala válida com os parâmetros informados. Tente ajustar os valores.")
