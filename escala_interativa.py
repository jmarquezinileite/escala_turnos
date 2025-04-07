
import streamlit as st
import pandas as pd
import random
from collections import defaultdict
from io import BytesIO
from datetime import datetime, timedelta

st.title("Gerador de Escala com Feriados Opcionais")

st.write("Gere uma escala semanal com datas reais. Se desejar, exclua manualmente os dias de feriado.")

dias_semana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta']
turnos = ['Manhã', 'Tarde']
vies_turno = {'Jack': 'Tarde'}

data_inicio = st.date_input("Data de início da semana (segunda-feira):", value=datetime.today(), format="DD/MM/YYYY")

usar_feriados = st.checkbox("Deseja excluir feriados nesta semana?", value=False)
feriados = []

if usar_feriados:
    feriados = st.date_input("Selecione os feriados:", value=[], format="DD/MM/YYYY", key="feriados", help="Datas selecionadas serão marcadas como feriado.", disabled=not usar_feriados)

datas_semana = []
for i in range(5):
    data = data_inicio + timedelta(days=i)
    dia_label = f"{dias_semana[i]} ({data.strftime('%d/%m')})"
    is_feriado = data in feriados
    datas_semana.append((dia_label, data, is_feriado))

pessoas_manha = st.number_input("Pessoas por turno da Manhã", min_value=2, max_value=10, value=4)
pessoas_tarde = st.number_input("Pessoas por turno da Tarde", min_value=2, max_value=10, value=2)
capacidade = {'Manhã': pessoas_manha, 'Tarde': pessoas_tarde}
num_pessoas = st.number_input("Quantos agentes?", min_value=2, max_value=20, value=6)

st.subheader("Agentes e seus turnos semanais")
nomes = []
limites = {}
restricao_dia = {}

with st.form("formulario_completo"):
    for i in range(int(num_pessoas)):
        col1, col2, col3 = st.columns([2, 1, 2])
        nome = col1.text_input("Agente", key=f"nome_{i}")
        turnos_semanais = col2.number_input("Turnos", min_value=1, max_value=50, value=1, key=f"turno_{i}")
        unica_vez = col3.checkbox("Máx. 1 turno por dia", value=False, key=f"restricao_{i}")
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
        if 2 <= total_turnos <= 5 and len(info['turnos']) < 2:
            return False
        if total_turnos > 5 and len(info['dias']) < 4:
            return False
    return True

def validar_tendencia_jack(escala):
    jack_turnos = []
    for (dia, turno), pessoas in escala.items():
        if 'Jack' in pessoas:
            jack_turnos.append(turno)
    if len(jack_turnos) == 5:
        tardes = sum(1 for t in jack_turnos if t == 'Tarde')
        return tardes >= 2
    return True

if gerar:
    if not nomes or len(nomes) != len(set(nomes)):
        st.warning("Preencha todos os nomes corretamente e sem repetições.")
    else:
        def gerar_escala():
            escala = {}
            contagem = defaultdict(int)
            dias_embaralhados = datas_semana.copy()
            random.shuffle(dias_embaralhados)
            for dia_label, data, is_feriado in dias_embaralhados:
                for turno in turnos:
                    if is_feriado:
                        escala[(dia_label, turno)] = ["Feriado"]
                        continue
                    escala[(dia_label, turno)] = []
                    while len(escala[(dia_label, turno)]) < capacidade[turno]:
                        candidatos = []
                        for pessoa in nomes:
                            if contagem[pessoa] >= limites[pessoa]:
                                continue
                            if pessoa in escala[(dia_label, turno)]:
                                continue
                            if restricao_dia.get(pessoa, False):
                                if any(pessoa in escala.get((dia_label, t), []) for t in turnos):
                                    continue
                            candidatos.append(pessoa)
                        random.shuffle(candidatos)
                        if not candidatos:
                            return None, None
                        pesados = []
                        for pessoa in candidatos:
                            preferencia = vies_turno.get(pessoa)
                            if preferencia == turno:
                                pesados.extend([pessoa]*5)
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
            for (dia_label, _, _) in datas_semana:
                for turno in turnos:
                    agentes = escala.get((dia_label, turno), [])
                    if agentes == ["Feriado"]:
                        data.append({
                            'Dia': dia_label,
                            'Turno': turno,
                            'Agentes': 'Feriado',
                            'Anhanguera': '—',
                            'Dom Pedro': '—'
                        })
                    elif isinstance(agentes, list):
                        linha = {
                            'Dia': dia_label,
                            'Turno': turno,
                            'Agentes': ', '.join(agentes)
                        }
                        if len(agentes) == 4:
                            temp = agentes[:]
                            random.shuffle(temp)
                            linha['Anhanguera'] = ', '.join(temp[:2])
                            linha['Dom Pedro'] = ', '.join(temp[2:])
                        else:
                            linha['Anhanguera'] = '—'
                            linha['Dom Pedro'] = '—'
                        data.append(linha)
            df = pd.DataFrame(data)
            st.dataframe(df)

            contagem_df = pd.DataFrame.from_dict(contagem, orient='index', columns=['Turnos']).sort_index()
            st.subheader("Turnos por agente")
            st.dataframe(contagem_df)

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Escala_com_Eixos')
                contagem_df.to_excel(writer, sheet_name='Turnos_por_Agente')
            output.seek(0)

            st.download_button("Baixar escala em Excel", data=output, file_name="escala_tabela_completa.xlsx")
        else:
            st.error("Não foi possível gerar uma escala válida com os parâmetros definidos.")
