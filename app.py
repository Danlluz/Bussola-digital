import streamlit as st
import pandas as pd
import google.generativeai as genai
import requests
import json
import os
import plotly.express as px
from fpdf import FPDF

# ==========================================
# 0. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Bússola Digital | Premium", page_icon="🧭", layout="wide")

ARQUIVO_CACHE = "banco_de_dados_local.csv"

def limpar_texto_pdf(texto):
    return texto.encode('latin-1', 'replace').decode('latin-1')

def gerar_pdf(conteudo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Dossie Bussola Digital - Analise de Carreira", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=limpar_texto_pdf(conteudo))
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 1. CONFIGURAÇÕES E CHAVES (SECRETS)
# ==========================================
try:
    CHAVE_GEMINI = st.secrets["gemini"]["api_key"]
    CHAVE_YOUTUBE = st.secrets["youtube"]["api_key"]
    CLIENT_ID = st.secrets["google"]["client_id"]
    REDIRECT_URI = st.secrets["google"]["redirect_uri"]
    
    # Configuração da IA
    genai.configure(api_key=CHAVE_GEMINI)
except Exception as e:
    st.error(f"⚠️ Erro nas Secrets: {e}")
    st.stop()

# ==========================================
# 2. MOTOR DE MINERAÇÃO (HÍBRIDO)
# ==========================================
def minerar_json_youtube(arquivo_json):
    dados_brutos = json.load(arquivo_json)
    videos = [v for v in dados_brutos if "titleUrl" in v][:1000] 
    
    lista_final = []
    total = len(videos)
    barra_progresso = st.progress(0)
    status_texto = st.empty()
    
    for i, video in enumerate(videos):
        video_id = video["titleUrl"].split("v=")[-1]
        url_api = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={CHAVE_YOUTUBE}"
        
        try:
            res = requests.get(url_api).json()
            if "items" in res and len(res["items"]) > 0:
                snippet = res["items"][0]["snippet"]
                lista_final.append({
                    "Canal": snippet.get("channelTitle", "Desconhecido"),
                    "Título": video.get("title", "Sem Título")
                })
            else:
                raise Exception("API Limit/Error")
        except:
            # Fallback: Extração offline do nome do canal
            titulo_bruto = video.get("title", "")
            canal = titulo_bruto.split("from ")[-1] if "from " in titulo_bruto else "Outros"
            lista_final.append({"Canal": canal, "Título": titulo_bruto})

        barra_progresso.progress((i + 1) / total)
        status_texto.text(f"Minerando: {i+1}/{total}")

    barra_progresso.empty()
    status_texto.empty()
    
    df = pd.DataFrame(lista_final)
    if not df.empty:
        df.to_csv(ARQUIVO_CACHE, index=False)
        return df
    return None

# ==========================================
# 3. INTERFACE PRINCIPAL
# ==========================================
st.title("🧭 Bússola Digital")
st.markdown("##### Inteligência Artificial aplicada ao seu comportamento digital.")
st.divider()

aba_simulador, aba_rapida, aba_profunda = st.tabs(["🚀 O Serviço", "🟢 Raio-X", "💎 Dossiê Premium"])

# --- ABA 1: O SERVIÇO ---
with aba_simulador:
    st.markdown("### 🌟 Sua Carreira Guiada por Dados")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("""
        A **Bússola Digital** analisa seus padrões de consumo no YouTube para mapear habilidades e oportunidades.
        
        * **Mapeamento de Habilidades:** Traduzimos entretenimento em competências profissionais.
        * **Dossiê Personalizado:** Relatórios gerados por IA de última geração.
        * **Plano de Ação:** Trilhas de 90 dias para transição ou aceleração de carreira.
        """)
        st.info("💡 **Como começar?** Baixe seu histórico no Google Takeout e suba na Aba 3.")
    with col2:
        st.markdown("#### 🧪 Simulador Rápido")
        area = st.selectbox("Escolha uma área:", ["Tecnologia", "Artes", "Gestão", "Saúde"])
        if st.button("Ver Tendência"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            resp = model.generate_content(f"Diga uma tendência de carreira em 2026 para {area}")
            st.success(resp.text)

# --- ABA 2: RAIO-X (OAUTH) ---
with aba_rapida:
    st.markdown("### 🟢 Conexão em Tempo Real")
    st.write("Analise seus vídeos curtidos e inscrições atuais instantaneamente.")
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=https://www.googleapis.com/auth/youtube.readonly"
    st.markdown(f'<a href="{auth_url}" target="_self"><button style="background-color:#FF4B4B;color:white;padding:12px 24px;border:none;border-radius:8px;cursor:pointer;font-weight:bold;">🔐 Conectar com Google YouTube</button></a>', unsafe_allow_html=True)
    st.caption("Nota: Requer configuração de tela de consentimento no Google Cloud.")

# --- ABA 3: DOSSIÊ PREMIUM ---
with aba_profunda:
    st.markdown("### 💎 Análise de Histórico Profundo")

    if "dados_minerados" not in st.session_state:
        if os.path.exists(ARQUIVO_CACHE):
            st.session_state.dados_minerados = pd.read_csv(ARQUIVO_CACHE)
        else:
            st.session_state.dados_minerados = None

    if st.session_state.dados_minerados is None:
        arquivo = st.file_uploader("Upload watch-history.json", type=["json"])
        if arquivo and st.button("⛏️ Iniciar Análise", type="primary"):
            res = minerar_json_youtube(arquivo)
            if res is not None:
                st.session_state.dados_minerados = res
                st.rerun()
    else:
        df = st.session_state.dados_minerados
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### 🏆 Top Canais")
            top = df['Canal'].value_counts().head(10).reset_index()
            fig = px.bar(top, x='count', y='Canal', orientation='h', template="plotly_dark", color_discrete_sequence=['#FF4B4B'])
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("##### 🍩 Distribuição")
            fatia = df['Canal'].value_counts().head(6)
            fig_pie = px.pie(values=fatia.values, names=fatia.index, hole=0.4, template="plotly_dark")
            st.plotly_chart(fig_pie, use_container_width=True)

        if st.button("♻️ Resetar Dados"):
            if os.path.exists(ARQUIVO_CACHE): os.remove(ARQUIVO_CACHE)
            st.session_state.dados_minerados = None
            st.rerun()

        st.divider()
        contexto = st.text_area("🔧 Qual seu objetivo profissional hoje?")
        if st.button("🚀 Gerar Dossiê IA", type="primary", use_container_width=True):
            resumo = df['Canal'].value_counts().head(30).to_string()
            with st.spinner("IA Analisando..."):
                try:
                    # Correção do modelo para evitar erro 404
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    resposta = model.generate_content(f"Perfil: {resumo}. Objetivo: {contexto}. Gere Arquétipo, 3 Carreiras e Plano 90 dias.")
                    st.session_state.analise_pronta = resposta.text
                except Exception as e:
                    st.error(f"Erro na IA: {e}")

        if "analise_pronta" in st.session_state:
            st.markdown("---")
            st.markdown(st.session_state.analise_pronta)
            pdf = gerar_pdf(st.session_state.analise_pronta)
            st.download_button("📥 Baixar PDF", data=pdf, file_name="dossie.pdf", mime="application/pdf")