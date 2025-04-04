
import streamlit as st
import pandas as pd
import random
from collections import defaultdict
from io import BytesIO
from datetime import datetime, timedelta

st.title("Gerador de Escala com Datas e Feriados")

st.write("Preencha os dados abaixo para gerar sua escala semanal com datas reais e feriados personalizados.")

dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']
turnos = ['Manhã', 'Tarde']
vies_turno = {'Jack': 'Tarde'}

# Entradas de datas
data_inicio = st.date_input("Selecione a data de início da semana (uma segunda-feira):", value=datetime.today())
feriados = st.date_input("Selecione os feriados (serão ignorados na escala):", value=[], key="feriados", format="DD/MM/YYYY")

# Calcular datas reais
datas_semana = []
for i in range(5):
    data = data_inicio + timedelta(days=i)
    if data not in feriados:
        dia_label = f"{dias_semana[i]} ({data.strftime('%d/%m')})"
        datas_semana.append((dia_label, data))

# Entradas gerais
pessoas_manha = st.number_input("Pessoas por turno da Manhã", min_value=2, max_value=10, value=4)
pessoas_tarde = st.number_input("Pessoas por turno da Tarde", min_value=2, max_value=10, value=2)
capacidade = {'Manhã': pessoas_manha, 'Tarde': pessoas_tarde}
num_pessoas = st.number_input("Quantos participantes?", min_value=2, max_value=20, value=6)

st.subheader("Participantes e seus turnos semanais")
nomes = []
limites = {}
restricao_dia = {}

with st.form("formulario_completo"):
    for i in range(int(num_pessoas)):
        col1, col2, col3 = st.columns([2, 1, 2])
        nome = col1.text_input(f"Nome do participante {i+1}", key=f"nome_{i}")
        turnos_semanais = col2.number_input("Turnos", min_value=1, max_value=50, value=1, key=f"turno_{i}")
        unica_vez = col3.checkbox("Máx. 1 turno por dia", value=True, key=f"restricao_{i}")
        if nome:
            nomes.append(nome)
            limites[nome] = turnos_semanais
            restricao_dia[nome] = unica_vez
    gerar = st.form_submit_button("Gerar Escala")

def validar_distribuicao(escala, contagem):
    distribuicao = defaultdict(lambda: {'dias': set(), 'turnos': set()})
    for (dia, turno), pessoas in escala.items():
        for pessoa in pessoas:
            distribuicao[pessoa]['dias'].add(dia)
            distribuicao[pessoa]['turnos'].add(turno)

    for pessoa, info in distribuicao.items():
        total_turnos = contagem[pessoa]
        turnos_usados = info['turnos']
        dias_usados = info['dias']

        if 2 <= total_turnos <= 5 and len(turnos_usados) < 2:
            return False
        if total_turnos > 5 and len(dias_usados) < 4:
            return False
    return True

def validar_tendencia_jack(escala):
    jack_turnos = []
    for (dia, turno), pessoas in escala.items():
        if 'Jack' in pessoas:
            jack_turnos.append(turno)

    if len(jack_turnos) == 5:
        tardes = sum(1 for t in jack_turnos if t == 'Tarde')
        manhas = sum(1 for t in jack_turnos if t == 'Manhã')
        return tardes >= 2 and manhas <= 3
    return True

if gerar:
    if not nomes or len(nomes) != len(set(nomes)):
        st.warning("Preencha todos os nomes corretamente e sem repetições.")
    else:
        def gerar_escala():
            escala = {(dia_label, turno): [] for (dia_label, _) in datas_semana for turno in turnos}
            contagem = defaultdict(int)

            for dia_label, _ in datas_semana:
                for turno in turnos:
                    while len(escala[(dia_label, turno)]) < capacidade[turno]:
                        candidatos = []
                        for pessoa in nomes:
                            if contagem[pessoa] >= limites[pessoa]:
                                continue
                            if pessoa in escala[(dia_label, turno)]:
                                continue
                            if restricao_dia.get(pessoa, False):
                                if any(pessoa in escala[(dia_label, t)] for t in turnos):
                                    continue
                            candidatos.append(pessoa)

                        if not candidatos:
                            return None, None

                        pesados = []
                        for pessoa in candidatos:
                            preferencia = vies_turno.get(pessoa)
                            if preferencia == turno:
                                pesados.extend([pessoa]*3)
                            else:
                                pesados.append(pessoa)

                        escolhido = random.choice(pesados)
                        escala[(dia_label, turno)].append(escolhido)
                        contagem[escolhido] += 1
            return escala, contagem

        escala, contagem = None, None
        for tentativa in range(1000):
            escala_tmp, contagem_tmp = gerar_escala()
            if escala_tmp and validar_distribuicao(escala_tmp, contagem_tmp) and validar_tendencia_jack(escala_tmp):
                escala, contagem = escala_tmp, contagem_tmp
                break

        if escala:
            st.success("Escala gerada com sucesso!")

            data = []
            for (dia_label, _) in datas_semana:
                linha = {'Dia': dia_label}
                for turno in turnos:
                    linha[turno] = ', '.join(escala[(dia_label, turno)])
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

            st.download_button("Baixar escala em Excel", data=output, file_name="escala_com_datas_e_feriados.xlsx")
        else:
            st.error("Não foi possível gerar uma escala válida com os parâmetros e feriados escolhidos.")
