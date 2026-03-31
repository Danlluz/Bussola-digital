import streamlit as st
import pandas as pd
import google.generativeai as genai
import requests
import json
import os
import plotly.express as px
from fpdf import FPDF

# ==========================================
# 0. CONFIGURAÇÃO DA PÁGINA E ESTILO
# ==========================================
st.set_page_config(page_title="Bússola Digital | Premium", page_icon="🧭", layout="wide")

ARQUIVO_CACHE = "banco_de_dados_local.csv"

# Funções de Utilidade para o PDF
def limpar_texto_pdf(texto):
    """Remove caracteres não suportados pelo FPDF padrão"""
    return texto.encode('latin-1', 'replace').decode('latin-1')

def gerar_pdf(conteudo):
    """Gera um PDF com o resultado da análise"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Dossie Bussola Digital - Analise de Carreira", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    texto_limpo = limpar_texto_pdf(conteudo)
    pdf.multi_cell(0, 10, txt=texto_limpo)
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 1. CONFIGURAÇÕES E CHAVES (SECRETS)
# ==========================================
try:
    CHAVE_GEMINI = st.secrets["gemini"]["api_key"]
    CHAVE_YOUTUBE = st.secrets["youtube"]["api_key"]
    CLIENT_ID = st.secrets["google"]["client_id"]
    REDIRECT_URI = st.secrets["google"]["redirect_uri"]
    
    genai.configure(api_key=CHAVE_GEMINI)
except Exception as e:
    st.error(f"⚠️ Erro nas Secrets: {e}")
    st.stop()

# ==========================================
# 2. MOTOR DE MINERAÇÃO (COM LIMITE E LIMPEZA)
# ==========================================
def minerar_json_youtube(arquivo_json):
    dados_brutos = json.load(arquivo_json)
    
    # Filtra e limita a 1500 vídeos para garantir performance e cota de API
    videos = [v for v in dados_brutos if "titleUrl" in v]
    videos = videos[:1500] 
    
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
                    "Título": video.get("title", "Sem Título"),
                    "Canal": snippet.get("channelTitle", "Desconhecido"),
                    "Categoria": snippet.get("categoryId", "0")
                })
        except:
            continue
        
        # Atualização visual
        progresso = (i + 1) / total
        barra_progresso.progress(progresso)
        status_texto.text(f"Processando vídeo {i+1} de {total}...")

    # LIMPEZA FINAL DA INTERFACE (Evita travamento visual)
    barra_progresso.empty()
    status_texto.empty()
    
    df = pd.DataFrame(lista_final)
    if not df.empty:
        df.to_csv(ARQUIVO_CACHE, index=False)
    return df

# ==========================================
# 3. INTERFACE PRINCIPAL
# ==========================================
st.title("🧭 Bússola Digital")
st.markdown("##### Inteligência Artificial aplicada ao seu comportamento digital.")
st.divider()

aba_simulador, aba_rapida, aba_profunda = st.tabs([
    "🚀 O Serviço", 
    "🟢 Raio-X Rápido", 
    "💎 Dossiê Premium"
])

# --- ABA 1: LANDING PAGE ---
with aba_simulador:
    st.markdown("### 🌟 Bem-vindo ao Futuro do Autoconhecimento")
    col_l1, col_l2 = st.columns([2, 1])
    with col_l1:
        st.write("""
        A **Bússola Digital** traduz seu consumo de conteúdo em um mapa de carreira.
        * **Identifique Soft Skills:** Perfil de liderança, criatividade ou analítico.
        * **Trilhas de Estudo:** Planos práticos de 90 dias.
        * **Dashboard Visual:** Veja onde você investe sua atenção.
        """)
        st.info("💡 Comece pela **Aba 3** subindo seu histórico do YouTube.")
    with col_l2:
        st.markdown("#### 🧪 Simulador")
        interesses = st.multiselect("Áreas de interesse:", ["Python", "Design", "Finanças", "Marketing"], default=["Python"])
        if st.button("Gerar Prévia"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            previa = model.generate_content(f"Diga uma profissão inovadora para quem gosta de {interesses}")
            st.write(previa.text)

# --- ABA 2: RAIO-X RÁPIDO ---
with aba_rapida:
    st.markdown("### 🟢 Conexão Instantânea")
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=https://www.googleapis.com/auth/youtube.readonly"
    st.markdown(f'<a href="{auth_url}" target="_self"><button style="background-color: #FF4B4B; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer;">🔐 Conectar com YouTube</button></a>', unsafe_allow_html=True)

# --- ABA 3: DOSSIÊ PREMIUM ---
with aba_profunda:
    st.markdown("### 💎 Análise de Histórico Profundo")

    if "dados_minerados" not in st.session_state:
        if os.path.exists(ARQUIVO_CACHE):
            st.session_state.dados_minerados = pd.read_csv(ARQUIVO_CACHE)
            st.toast("⚡ Banco de dados carregado do cache!")
        else:
            st.session_state.dados_minerados = None

    if st.session_state.dados_minerados is None:
        with st.expander("❓ Como baixar meu histórico?", expanded=True):
            st.write("Vá ao Google Takeout, selecione apenas YouTube (Histórico em JSON).")
        arquivo = st.file_uploader("Upload watch-history.json", type=["json"])
        if arquivo and st.button("⛏️ Processar Agora", type="primary"):
            df_novo = minerar_json_youtube(arquivo)
            if not df_novo.empty:
                st.session_state.dados_minerados = df_novo
                st.rerun()
    else:
        df = st.session_state.dados_minerados
        
        # Gráficos Visuais
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("##### 🏆 Canais Mais Assistidos")
            top_10 = df['Canal'].value_counts().head(10).reset_index()
            top_10.columns = ['Canal', 'Visualizações']
            fig = px.bar(top_10, x='Visualizações', y='Canal', orientation='h', 
                         color='Visualizações', color_continuous_scale='Reds', template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)
        with col_g2:
            st.markdown("##### 🍩 Distribuição de Foco")
            fatia = df['Canal'].value_counts().head(6)
            fig_pie = px.pie(values=fatia.values, names=fatia.index, hole=0.4, template="plotly_dark")
            st.plotly_chart(fig_pie, use_container_width=True)

        if st.button("♻️ Resetar Dados e Cache"):
            if os.path.exists(ARQUIVO_CACHE): os.remove(ARQUIVO_CACHE)
            del st.session_state.dados_minerados
            st.rerun()

        st.divider()
        contexto = st.text_area("🔧 Personalize sua análise (Qual seu objetivo?):")
        
        if st.button("🚀 Gerar Dossiê IA", type="primary", use_container_width=True):
            resumo = df['Canal'].value_counts().head(30).to_string()
            prompt = f"Analise este perfil do YouTube: {resumo}. Objetivo: {contexto}. Gere Arquétipo, 3 Carreiras e Trilha de 90 dias."
            with st.spinner("IA Analisando dados..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                resposta = model.generate_content(prompt)
                st.session_state.analise_pronta = resposta.text

        if "analise_pronta" in st.session_state:
            st.markdown("---")
            with st.container():
                st.markdown(st.session_state.analise_pronta)
                try:
                    pdf_bytes = gerar_pdf(st.session_state.analise_pronta)
                    st.download_button("📥 Baixar Dossiê (PDF)", data=pdf_bytes, file_name="dossie_carreira.pdf", mime="application/pdf", use_container_width=True)
                except:
                    st.warning("⚠️ Erro ao gerar PDF (caracteres especiais).")