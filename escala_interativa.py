
import streamlit as st
from datetime import datetime

st.set_page_config(layout="centered")
st.title("🔧 Teste de Carregamento do App")

st.write("Se você está vendo esta mensagem, o Streamlit está funcionando corretamente.")

if st.button("Clique aqui para testar"):
    st.success(f"O app está respondendo! Data atual: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
