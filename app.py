import streamlit as st
import pandas as pd
import google.generativeai as genai
import requests
import urllib.parse
import json
import time
import os

st.set_page_config(page_title="Bússola Digital | Seu Futuro Mapeado", page_icon="🧭", layout="wide")

# ==========================================
# 1. CONFIGURAÇÕES E CHAVES (O COFRE)
# ==========================================
try:
    CLIENT_ID = st.secrets["google"]["client_id"]
    CLIENT_SECRET = st.secrets["google"]["client_secret"]
    REDIRECT_URI = st.secrets["google"]["redirect_uri"]
    CHAVE_GEMINI = st.secrets["gemini"]["api_key"]
    CHAVE_YOUTUBE = st.secrets["youtube"]["api_key"]
    
    genai.configure(api_key=CHAVE_GEMINI)
except Exception as e:
    st.error(f"⚠️ Erro no cofre (.streamlit/secrets.toml): {e}")
    st.stop()

SCOPE = "https://www.googleapis.com/auth/youtube.readonly"

# ==========================================
# 2. MOTOR DE MINERAÇÃO TOTAL (HARDCORE)
# ==========================================
def minerar_json_youtube(arquivo_json):
    dados_brutos = json.load(arquivo_json)
    lista_final = []
    
    barra_progresso = st.progress(0)
    status_texto = st.empty()
    
    videos = [v for v in dados_brutos if "titleUrl" in v]
    total = len(videos)
    
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
        
        progresso = (i + 1) / total
        barra_progresso.progress(progresso)
        status_texto.text(f"Minerando vídeo {i+1} de {total} (Consumindo cota da API)...")

    if len(lista_final) > 0:
        status_texto.success(f"✅ Mineração de {len(lista_final)} vídeos concluída!")
    else:
        status_texto.error("❌ Nenhum vídeo processado. Verifique sua cota.")
        
    return pd.DataFrame(lista_final)

# ==========================================
# 3. INTERFACE E ABAS
# ==========================================
st.title("🧭 Bússola Digital")
st.markdown("Descubra sua vocação, mapeie suas habilidades ocultas e crie sua trilha de carreira baseada no seu consumo real de conteúdo.")
st.divider()

aba_simulador, aba_rapida, aba_profunda = st.tabs([
    "🚀 1. O App (Simulador)", 
    "🟢 2. Raio-X (Likes)", 
    "💎 3. Bússola Premium (Takeout)"
])

# ------------------------------------------
# ABA 1: LANDING PAGE + SIMULADOR
# ------------------------------------------
with aba_simulador:
    
    # Seção de Vendas (O Diferencial Comercial)
    st.markdown("### Por que a Bússola Digital é diferente?")
    col_vendas1, col_vendas2, col_vendas3 = st.columns(3)
    
    with col_vendas1:
        st.info("**🧠 Mapa de Soft Skills Ocultas**\n\nNão perguntamos quem você é. Analisamos seus interesses reais para revelar habilidades que você nem sabia que tinha (ex: Resolução de Problemas, Foco Analítico).")
    with col_vendas2:
        st.success("**🗺️ Trilhas de Estudo Acionáveis**\n\nNão entregamos apenas o nome de uma profissão. Geramos um plano prático de 3 meses focado no que você deve estudar para começar sua transição hoje.")
    with col_vendas3:
        st.warning("**🏢 Match Corporativo (Em Breve)**\n\nNo futuro, conectaremos seu perfil de habilidades e fit cultural diretamente com recrutadores de empresas inovadoras. Sem viés de currículo.")

    st.divider()
    
    # O Simulador
    st.markdown("### 🎛️ Teste o Motor da IA (Simulador Manual)")
    st.write("Arraste os controles abaixo para simular um histórico e veja como nossa IA reage em tempo real.")
    
    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        tech = st.slider("💻 Tecnologia & Código (%)", 0, 100, 20)
        arte = st.slider("🎨 Arte & Design (%)", 0, 100, 20)
    with col_sim2:
        financas = st.slider("📈 Finanças & Negócios (%)", 0, 100, 20)
        games = st.slider("🎮 Games & E-sports (%)", 0, 100, 20)
        
    if st.button("Simular Meu Futuro", use_container_width=True):
        with st.spinner("Calculando o perfil vocacional..."):
            resumo_simulado = f"Tecnologia: {tech}%, Arte: {arte}%, Finanças: {financas}%, Games: {games}%"
            prompt_simulador = f"Atue como orientador vocacional. Baseado neste consumo simulado do YouTube: {resumo_simulado}. Sugira 3 carreiras ideais, estilo de trabalho e foco de estudo."
            
            try:
                model = genai.GenerativeModel('gemini-2.5-flash')
                resposta = model.generate_content(prompt_simulador)
                st.success("Resultado da Simulação:")
                st.markdown(resposta.text)
            except Exception as e:
                st.error(f"⚠️ Detalhe técnico do erro: {e}")

# ------------------------------------------
# ABA 2: FLUXO RÁPIDO (VIA LOGIN)
# ------------------------------------------
with aba_rapida:
    st.markdown("### Análise Instantânea")
    
    if "logado" not in st.session_state: st.session_state.logado = False
    if "token" not in st.session_state: st.session_state.token = None

    codigo_url = st.query_params.get("code")

    if codigo_url and not st.session_state.logado:
        token_data = {
            "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET,
            "code": codigo_url, "grant_type": "authorization_code", "redirect_uri": REDIRECT_URI
        }
        res = requests.post("https://oauth2.googleapis.com/token", data=token_data).json()
        if "access_token" in res:
            st.session_state.token = res["access_token"]
            st.session_state.logado = True
            st.query_params.clear()
            st.rerun()

    if not st.session_state.logado:
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope={SCOPE}&access_type=offline&prompt=consent"
        st.link_button("🔗 Conectar Conta Google", auth_url, type="primary")
    else:
        if st.button("🧠 Gerar Perfil de Essência", use_container_width=True):
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            yt_res = requests.get("https://youtube.googleapis.com/youtube/v3/videos?part=snippet&myRating=like&maxResults=30", headers=headers).json()
            
            if "items" in yt_res:
                canais = [item["snippet"]["channelTitle"] for item in yt_res["items"]]
                prompt = f"Analise o perfil psicológico e interesses deste usuário baseado nos canais que ele curte: {list(set(canais))}"
                
                try:
                    with st.spinner("IA analisando curtidas..."):
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        resposta = model.generate_content(prompt)
                        st.info(resposta.text)
                except Exception as e:
                    st.error(f"⚠️ Detalhe técnico do erro: {e}")
            else:
                st.warning("Não encontramos vídeos curtidos públicos nesta conta.")

# ------------------------------------------
# ABA 3: FLUXO PROFUNDO (VIA JSON) - DESIGN AMIGÁVEL E ANÁLISE PSICOLÓGICA
# ------------------------------------------
with aba_profunda:
    st.markdown("### 💎 Dossiê de Carreira Premium")
    
    # 1. Botão de Reset Amigável
    if "analise_pronta" in st.session_state or "dados_minerados" in st.session_state:
        col_reset1, col_reset2 = st.columns([3, 1])
        with col_reset2:
            if st.button("🗑️ Reiniciar Tudo", use_container_width=True):
                for key in ["analise_pronta", "dados_minerados"]:
                    if key in st.session_state: del st.session_state[key]
                if os.path.exists("backup_mineracao.csv"): os.remove("backup_mineracao.csv")
                st.rerun()

    # 2. Upload e Mineração
    if "dados_minerados" not in st.session_state:
        st.write("Suba seu histórico para desbloquear seu mapa psicológico e trilha de carreira.")
        arquivo_bruto = st.file_uploader("Arquivo 'watch-history.json'", type=["json"])
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            if arquivo_bruto and st.button("⛏️ Iniciar Mineração", type="primary", use_container_width=True):
                df_final = minerar_json_youtube(arquivo_bruto)
                if not df_final.empty:
                    st.session_state.dados_minerados = df_final
                    df_final.to_csv("backup_mineracao.csv", index=False)
                    st.rerun()
        with col_m2:
            if os.path.exists("backup_mineracao.csv"):
                if st.button("🔄 Usar Memória Local", use_container_width=True):
                    st.session_state.dados_minerados = pd.read_csv("backup_mineracao.csv")
                    st.rerun()
    else:
        # 3. INTERFACE DE ANÁLISE (QUANDO JÁ TEM DADOS)
        st.success(f"📊 {len(st.session_state.dados_minerados)} vídeos analisados com sucesso!")
        
        with st.expander("🔧 Calibrar meu Perfil (Opcional)", expanded=False):
            contexto_extra = st.text_area(
                "Conte algo sobre seus objetivos atuais:", 
                placeholder="Ex: 'Embora eu assista games, meu foco atual é migrar para o Marketing Digital.'",
                key="input_ajuste_v2"
            )

        if st.button("🚀 Gerar Meu Dossiê Visual", type="primary", use_container_width=True):
            df = st.session_state.dados_minerados
            resumo = df['Canal'].value_counts().head(30).to_string()
            texto_calibragem = f"\n\nCONTEXTO DO USUÁRIO: '{contexto_extra}'" if contexto_extra else ""

            # PROMPT ULTRA-ESTRUTURADO PARA EVITAR TEXTOS GIGANTES
            prompt_premium = f"""
            Você é um Headhunter e Psicólogo Organizacional de uma Big Tech.
            Analise este histórico real: {resumo} {texto_calibragem}
            
            Sua resposta deve seguir esta estrutura visual e profunda:

            ## 🧠 1. Perfil Psicológico e Comportamental
            Dê um nome único ao perfil deste usuário (ex: 'O Arquiteto de Sistemas Criativos'). 
            Descreva como o consumo de conteúdo reflete sua forma de tomar decisões e lidar com problemas.

            ## 🎯 2. O seu "Oceano Azul" (Carreiras)
            Identifique 3 carreiras onde o usuário teria uma vantagem competitiva injusta porque ele combina conhecimentos de áreas diferentes que viu no YouTube.
            * **Carreira X:** Justificativa profunda conectando os canais assistidos.

            ## 🛡️ 3. Inventário de Habilidades (Hard & Soft)
            Crie uma lista destacando:
            • **Habilidade:** [Origem no histórico] -> [Como aplicar no mercado].

            ## ⚠️ 4. Ponto Cego (Análise Crítica)
            Identifique um padrão de consumo que pode estar prejudicando o foco do usuário ou uma área importante que ele está negligenciando para atingir o objetivo dele.

            ## 🛠️ 5. Projeto "Portfólio de Ouro"
            Sugira UM projeto prático que o usuário deve construir nos próximos 30 dias para provar sua competência na área sugerida.

            ## 🗺️ 6. Trilha de Estudos Master (90 Dias)
            | Mês | Foco Teórico | Prática Sugerida | Sugestão de Conteúdo |
            | :--- | :--- | :--- | :--- |
            | **Mês 1** | Conceitos Base | Exercício X | Buscar por [Termo de Busca] |
            | **Mês 2** | Ferramentas | Projeto Y | Canais de [Nicho] |
            | **Mês 3** | Portfólio | Publicar Z | Networking no [Plataforma] |

            Use negritos, divisores e emojis. Seja direto, mas extremamente perspicaz.
            """
            
            try:
                with st.spinner("IA desenhando seu futuro..."):
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    resposta = model.generate_content(prompt_premium)
                    st.session_state.analise_pronta = resposta.text
                    st.balloons()
            except Exception as e:
                st.error(f"Erro: {e}")

        # EXIBIÇÃO PERSISTENTE E AMIGÁVEL
        if "analise_pronta" in st.session_state:
            st.markdown("---")
            # Container branco para dar destaque ao resultado
            with st.container():
                st.markdown(st.session_state.analise_pronta)