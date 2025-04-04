
import streamlit as st
import pandas as pd
import random
from collections import defaultdict
from io import BytesIO

st.title("Gerador de Escala de Turnos Personalizado")

st.write("Preencha os dados abaixo para gerar sua escala semanal.")

# Entradas fixas
dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']
turnos = ['Manhã', 'Tarde']

pessoas_manha = st.number_input("Pessoas por turno da Manhã", min_value=2, max_value=10, value=4)
pessoas_tarde = st.number_input("Pessoas por turno da Tarde", min_value=2, max_value=10, value=2)

capacidade = {'Manhã': pessoas_manha, 'Tarde': pessoas_tarde}

num_pessoas = st.number_input("Quantos participantes?", min_value=2, max_value=20, value=6)

# Participantes
st.subheader("Participantes e seus turnos semanais")
nomes = []
limites = {}
restricao_dia = {}

with st.form("form_participantes"):
    for i in range(int(num_pessoas)):
        col1, col2, col3 = st.columns([2, 1, 2])
        nome = col1.text_input(f"Nome do participante {i+1}", key=f"nome_{i}")
        turnos_semanais = col2.number_input(f"Turnos", min_value=1, max_value=50, value=1, key=f"turno_{i}")
        unica_vez = col3.checkbox("Máx. 1 turno por dia", value=True, key=f"restricao_{i}")
        if nome:
            nomes.append(nome)
            limites[nome] = turnos_semanais
            restricao_dia[nome] = unica_vez
    submitted = st.form_submit_button("Confirmar Participantes")

# Dicionário de turnos fixos
fixos = {}

if nomes:
    st.subheader("Fixar pessoas em turnos específicos (opcional)")
    with st.form("form_fixos"):
        for dia in dias:
            for turno in turnos:
                chave = (dia, turno)
                pessoa_fixa = st.selectbox(f"{dia} - {turno}", options=[""] + nomes, key=f"fixo_{dia}_{turno}")
                if pessoa_fixa:
                    fixos[chave] = pessoa_fixa
        gerar = st.form_submit_button("Gerar Escala")

    if gerar:
        def gerar_escala():
            escala = {(dia, turno): [] for dia in dias for turno in turnos}
            contagem = defaultdict(int)

            # Preencher os turnos fixos
            for (dia, turno), nome in fixos.items():
                escala[(dia, turno)].append(nome)
                contagem[nome] += 1

            for dia in dias:
                for turno in turnos:
                    while len(escala[(dia, turno)]) < capacidade[turno]:
                        candidatos = []
                        for pessoa in nomes:
                            if contagem[pessoa] >= limites[pessoa]:
                                continue
                            if pessoa in escala[(dia, turno)]:
                                continue
                            if restricao_dia.get(pessoa, False):
                                if any(pessoa in escala[(dia, t)] for t in turnos):
                                    continue
                            candidatos.append(pessoa)

                        if not candidatos:
                            return None, None

                        escolhido = random.choice(candidatos)
                        escala[(dia, turno)].append(escolhido)
                        contagem[escolhido] += 1
            return escala, contagem

        for tentativa in range(1000):
            escala, contagem = gerar_escala()
            if escala:
                break

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

            st.download_button("Baixar escala em Excel", data=output, file_name="escala_com_restricoes.xlsx")
        else:
            st.error("Não foi possível gerar uma escala válida com os parâmetros informados.")
