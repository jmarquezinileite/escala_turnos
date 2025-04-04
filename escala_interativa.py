
import streamlit as st
import pandas as pd
import random
from collections import defaultdict
from io import BytesIO

st.title("Gerador de Escala de Turnos Personalizado")

st.write("Preencha os dados abaixo para gerar sua escala semanal.")

# Configurações fixas
dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']
turnos = ['Manhã', 'Tarde']
vies_turno = {'Jack': 'Tarde'}  # tendência invisível

# Entradas
pessoas_manha = st.number_input("Pessoas por turno da Manhã", min_value=2, max_value=10, value=4)
pessoas_tarde = st.number_input("Pessoas por turno da Tarde", min_value=2, max_value=10, value=2)
capacidade = {'Manhã': pessoas_manha, 'Tarde': pessoas_tarde}
num_pessoas = st.number_input("Quantos participantes?", min_value=2, max_value=20, value=6)

st.subheader("Participantes e seus turnos semanais")

# Armazenar os dados fora do formulário
nomes = ["" for _ in range(int(num_pessoas))]
limites = {}
restricao_dia = {}
turno_fixo_participante = {}

with st.form("form_participantes"):
    for i in range(int(num_pessoas)):
        col1, col2, col3, col4 = st.columns([2, 1, 2, 2])
        nomes[i] = col1.text_input(f"Nome do participante {i+1}", key=f"nome_{i}")
        limites[nomes[i]] = col2.number_input(f"Turnos", min_value=1, max_value=50, value=1, key=f"turno_{i}")
        restricao_dia[nomes[i]] = col3.checkbox("Máx. 1 turno por dia", value=True, key=f"restricao_{i}")
        turno_fixo = col4.selectbox("Turno fixo (opcional)", options=["", "Manhã", "Tarde"], key=f"fixo_{i}")
        if turno_fixo:
            turno_fixo_participante[nomes[i]] = turno_fixo
    submitted = st.form_submit_button("Confirmar Participantes")

# Limpar nomes inválidos
nomes = [n for n in nomes if n.strip() != ""]

# Sorteio
if submitted and nomes:
    def gerar_escala():
        escala = {(dia, turno): [] for dia in dias for turno in turnos}
        contagem = defaultdict(int)

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
                        if turno_fixo_participante.get(pessoa) and turno != turno_fixo_participante[pessoa]:
                            continue
                        candidatos.append(pessoa)

                    if not candidatos:
                        return None, None

                    # Aplicar tendência invisível
                    pesados = []
                    for pessoa in candidatos:
                        preferencia = vies_turno.get(pessoa)
                        if preferencia == turno:
                            pesados.extend([pessoa]*3)
                        else:
                            pesados.append(pessoa)

                    escolhido = random.choice(pesados)
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

        st.download_button("Baixar escala em Excel", data=output, file_name="escala_corrigida.xlsx")
    else:
        st.error("Não foi possível gerar uma escala válida com os parâmetros informados.")
