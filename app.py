import streamlit as st
import os
import sys
from dotenv import load_dotenv
from ai_client import get_ai_client, get_model_label
from auth_manager import authenticate, create_user, update_password, delete_user, list_users, get_user_count, ensure_db_exists
import json
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
from fontes_manager import (
    carregar_fontes, salvar_fontes, adicionar_fonte, remover_fonte,
    toggle_fonte, get_fontes_ativas, verificar_todas_fontes,
    verificar_status_fonte, descobrir_novas_fontes,
    adicionar_fontes_sugeridas, aprovar_fonte_sugerida, get_estatisticas
)
from utils import (
    extract_pdf_text,
    analyze_edital_with_ai,
    evaluate_company_adherence,
    generate_proposal_draft,
    calculate_weighted_score,
    get_score_classification
)
from export_docx import (
    create_diagnosis_document,
    create_proposal_document,
    save_document
)

# Load environment variables
load_dotenv()

# Inject Streamlit secrets into os.environ (para compatibilidade)
try:
    if "OPENAI_API_KEY" in st.secrets:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
except Exception:
    pass

# Page configuration
st.set_page_config(
    page_title="FINEP Copilot - Agnest Edition",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #2E7D32;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #1976D2;
        font-weight: bold;
        border-bottom: 2px solid #1976D2;
        padding-bottom: 0.5rem;
        margin-top: 1.5rem;
    }
    .success-box {
        background-color: #E8F5E9;
        border-left: 4px solid #4CAF50;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #FFF3E0;
        border-left: 4px solid #FF9800;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #FFEBEE;
        border-left: 4px solid #F44336;
        padding: 1rem;
        border-radius: 4px;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Garantir banco de usuários inicializado
ensure_db_exists()

# Initialize session state
if "edital_data" not in st.session_state:
    st.session_state.edital_data = None
if "company_profile" not in st.session_state:
    st.session_state.company_profile = {}
if "diagnosis_results" not in st.session_state:
    st.session_state.diagnosis_results = None
if "proposal_sections" not in st.session_state:
    st.session_state.proposal_sections = None
if "partners_db" not in st.session_state:
    st.session_state.partners_db = []
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "login_error" not in st.session_state:
    st.session_state.login_error = ""

# ─── TELA DE LOGIN ────────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    st.markdown("""
        <style>
        .login-container { max-width: 420px; margin: 80px auto; padding: 2rem; 
                           background: #fff; border-radius: 12px; 
                           box-shadow: 0 4px 24px rgba(0,0,0,0.10); }
        .login-logo { text-align: center; font-size: 3rem; margin-bottom: 0.5rem; }
        .login-title { text-align: center; color: #2E7D32; font-size: 1.6rem; 
                       font-weight: bold; margin-bottom: 0.2rem; }
        .login-sub { text-align: center; color: #666; font-size: 0.95rem; 
                     margin-bottom: 1.5rem; }
        </style>
    """, unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown('<div class="login-logo">🚀</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-title">FINEP Copilot</div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Agnest Farm Lab Edition</div>', unsafe_allow_html=True)
        st.markdown("---")

        with st.form("login_form", clear_on_submit=False):
            username_input = st.text_input("👤 Usuário", placeholder="seu.usuario")
            password_input = st.text_input("🔒 Senha", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("🔐 Entrar", use_container_width=True)

            if submitted:
                user = authenticate(username_input.strip().lower(), password_input)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.current_user = user
                    st.session_state.login_error = ""
                    st.rerun()
                else:
                    st.session_state.login_error = "❌ Usuário ou senha inválidos."

        if st.session_state.login_error:
            st.error(st.session_state.login_error)

        st.markdown("<br><div style='text-align:center;color:#aaa;font-size:0.8rem;'>Acesso restrito • HTTPS seguro • Agnest Farm Lab</div>", unsafe_allow_html=True)
    st.stop()  # Para aqui se não autenticado

# Sidebar
with st.sidebar:
    st.markdown("## 🚀 FINEP Copilot")
    st.markdown("**Agnest Farm Lab Edition**")
    st.markdown("---")

    # Usuário logado
    user = st.session_state.current_user
    st.markdown(f"👤 **{user['name']}** `{user['role']}`")
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.rerun()
    st.markdown("---")
    
    st.markdown("### Navegação")
    page = st.radio(
        "Selecione uma seção:",
        [
            "🏠 Início",
            "📊 Dashboard de Oportunidades",
            "🎯 Análise de Aderência",
            "🤝 Recomendador de Arranjos",
            "👥 Banco de Parceiros",
            "📝 Gerador de Proposta",
            "📥 Exportar Resultados",
            "🌐 Gerenciador de Fontes",
            "🔐 Gerenciar Usuários"
        ]
    )
    
    st.markdown("---")
    st.markdown("### Informações")
    st.info(
        "**FINEP Copilot** é um assistente estratégico para captura de recursos "
        "em editais públicos da FINEP, desenvolvido especificamente para a "
        "Agnest Farm Lab e seu ecossistema de parceiros."
    )
    st.markdown("---")
    try:
        model_label = get_model_label()
        st.success(f"{model_label}")
    except Exception:
        pass

# Main content
st.markdown('<h1 class="main-header">🚀 FINEP Copilot - Agnest Edition</h1>', unsafe_allow_html=True)
st.markdown("Assistente Estratégico de Captura de Recursos em Editais FINEP")
st.markdown("---")

# Page routing
if page == "🏠 Início":
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<h2 class="section-header">Bem-vindo ao FINEP Copilot</h2>', unsafe_allow_html=True)
        st.markdown("""
        O FINEP Copilot é uma ferramenta inteligente desenvolvida para ajudar a **Agnest Farm Lab** 
        e sua rede de parceiros a identificar e capturar oportunidades em editais públicos da FINEP.
        
        ### 🎯 Funcionalidades Principais
        
        - **Dashboard de Oportunidades**: Analise múltiplos editais simultaneamente
        - **Análise de Aderência**: Valide a compatibilidade com seus projetos
        - **Recomendador de Arranjos**: Identifique a melhor estrutura (simples ou rede)
        - **Banco de Parceiros**: Gerencie relacionamentos com ICTs e empresas
        - **Gerador de Proposta**: Crie rascunhos automáticos de propostas
        - **Exportação**: Gere relatórios executivos em Word
        
        ### 📋 Como Começar
        
        1. Faça upload de um edital FINEP (PDF)
        2. Preencha o perfil da sua empresa/iniciativa
        3. Analise a aderência aos requisitos
        4. Receba recomendações de arranjos e parceiros
        5. Gere e exporte sua proposta
        """)
    
    with col2:
        st.markdown('<h2 class="section-header">Sobre a Agnest Farm Lab</h2>', unsafe_allow_html=True)
        st.markdown("""
        A **Agnest Farm Lab** é um hub de inovação aberta para o setor agrícola, 
        localizado em Jaguariúna/SP, com liderança da EMBRAPA.
        
        ### 🌾 Verticais Temáticas
        
        1. Inteligência Artificial
        2. IoT (Internet das Coisas)
        3. Robótica e Automação
        4. Software para suporte e decisão
        5. Sistemas de produção sustentáveis
        6. Bioinsumos
        7. Sensoriamento remoto
        8. Manejo integrado de pragas e doenças
        
        ### 🤝 Parceiros Principais
        
        - **EMBRAPA** (Parceiro Institucional)
        - **Banco do Brasil** (Parceiro Estratégico)
        - Ecossistema de startups e corporações
        
        ### 💡 Vantagens Competitivas
        
        ✅ Infraestrutura de testes validada  
        ✅ Relacionamento com EMBRAPA  
        ✅ Acesso a ecossistema de inovação  
        ✅ Selo AgNest de validação  
        ✅ Ambiente de experimentação real
        """)
    
    st.markdown("---")
    st.markdown("### 📚 Próximos Passos")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**1️⃣ Upload do Edital**\n\nComece fazendo upload de um edital FINEP em PDF")
    with col2:
        st.info("**2️⃣ Análise**\n\nA ferramenta analisará automaticamente os requisitos")
    with col3:
        st.info("**3️⃣ Recomendações**\n\nReceba sugestões de arranjos e parceiros")

elif page == "📊 Dashboard de Oportunidades":
    st.markdown('<h2 class="section-header">📊 Dashboard de Oportunidades</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    Nesta seção você pode fazer upload de editais FINEP e obter uma análise rápida de aderência.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "📤 Faça upload de um edital FINEP (PDF)",
            type=["pdf"],
            key="edital_upload"
        )
    
    with col2:
        analyze_button = st.button("🔍 Analisar Edital", use_container_width=True)
    
    if uploaded_file and analyze_button:
        with st.spinner("⏳ Analisando edital..."):
            try:
                # Save uploaded file temporarily
                temp_path = f"/tmp/{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Extract text
                pdf_text = extract_pdf_text(temp_path)
                
                # Analyze with AI
                edital_data = analyze_edital_with_ai(pdf_text)
                st.session_state.edital_data = edital_data
                
                st.success("✅ Edital analisado com sucesso!")
                
                # Display results
                st.markdown("### 📋 Informações do Edital")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Orçamento Total",
                        edital_data.get("orcamento_total", "N/A")
                    )
                with col2:
                    st.metric(
                        "Valor Mínimo",
                        edital_data.get("valor_minimo", "N/A")
                    )
                with col3:
                    st.metric(
                        "Valor Máximo",
                        edital_data.get("valor_maximo", "N/A")
                    )
                
                st.markdown("#### Detalhes")
                details_df = pd.DataFrame({
                    "Aspecto": [
                        "Título",
                        "Objetivo",
                        "TRL Mínimo",
                        "TRL Máximo",
                        "Contrapartida Mínima",
                        "Prazo de Encerramento"
                    ],
                    "Valor": [
                        edital_data.get("titulo", "N/A"),
                        edital_data.get("objetivo", "N/A"),
                        edital_data.get("trl_minimo", "N/A"),
                        edital_data.get("trl_maximo", "N/A"),
                        edital_data.get("contrapartida_minima", "N/A"),
                        edital_data.get("prazo_encerramento", "N/A")
                    ]
                })
                st.dataframe(details_df, use_container_width=True, hide_index=True)
                
                # Display thematic lines
                if "linhas_tematicas" in edital_data:
                    st.markdown("#### Linhas Temáticas")
                    for i, linha in enumerate(edital_data["linhas_tematicas"], 1):
                        st.write(f"{i}. {linha}")
                
            except Exception as e:
                st.error(f"❌ Erro ao analisar edital: {str(e)}")
    
    if st.session_state.edital_data:
        st.markdown("---")
        st.markdown("### ✅ Edital Carregado")
        st.info(f"Edital: {st.session_state.edital_data.get('titulo', 'N/A')}")
        st.markdown("Prossiga para a próxima seção para análise de aderência.")

elif page == "🎯 Análise de Aderência":
    st.markdown('<h2 class="section-header">🎯 Análise de Aderência</h2>', unsafe_allow_html=True)
    
    if not st.session_state.edital_data:
        st.warning("⚠️ Por favor, faça upload de um edital primeiro na seção 'Dashboard de Oportunidades'")
    else:
        st.markdown("### 📝 Perfil da Agnest Farm Lab / Sua Iniciativa")
        
        col1, col2 = st.columns(2)
        
        with col1:
            company_name = st.text_input(
                "Nome da Empresa/Iniciativa",
                value=st.session_state.company_profile.get("nome_empresa", "Agnest Farm Lab"),
                key="nome_empresa"
            )
            cnpj = st.text_input(
                "CNPJ",
                value=st.session_state.company_profile.get("cnpj", ""),
                key="cnpj"
            )
            nature = st.selectbox(
                "Natureza Jurídica",
                ["Empresa Privada", "ICT Pública", "ICT Privada", "Startup", "Consórcio"],
                index=0 if st.session_state.company_profile.get("natureza_juridica") is None else 
                      ["Empresa Privada", "ICT Pública", "ICT Privada", "Startup", "Consórcio"].index(
                          st.session_state.company_profile.get("natureza_juridica", "Empresa Privada")
                      ),
                key="natureza_juridica"
            )
            size = st.selectbox(
                "Porte da Empresa",
                ["MEI", "ME", "EPP", "Média I", "Média II", "Grande"],
                index=0 if st.session_state.company_profile.get("porte") is None else
                      ["MEI", "ME", "EPP", "Média I", "Média II", "Grande"].index(
                          st.session_state.company_profile.get("porte", "ME")
                      ),
                key="porte"
            )
        
        with col2:
            state = st.selectbox(
                "Estado/Região",
                ["SP", "MG", "RS", "BA", "SC", "PR", "GO", "MT", "Outro"],
                index=0 if st.session_state.company_profile.get("estado_regiao") is None else
                      ["SP", "MG", "RS", "BA", "SC", "PR", "GO", "MT", "Outro"].index(
                          st.session_state.company_profile.get("estado_regiao", "SP")
                      ),
                key="estado_regiao"
            )
            area = st.text_input(
                "Área de Atuação Principal",
                value=st.session_state.company_profile.get("area_atuacao", "Agricultura Digital e Sustentável"),
                key="area_atuacao"
            )
            trl = st.slider(
                "TRL Habitual (1-9)",
                1, 9,
                value=st.session_state.company_profile.get("trl_habitual", 5),
                key="trl_habitual"
            )
            contrapartida = st.slider(
                "Capacidade de Contrapartida (%)",
                0, 100,
                value=st.session_state.company_profile.get("contrapartida_percentual", 20),
                key="contrapartida_percentual"
            )
        
        st.markdown("### 📋 Descrição Técnica e Histórico")
        
        col1, col2 = st.columns(2)
        
        with col1:
            description = st.text_area(
                "Descrição Técnica",
                value=st.session_state.company_profile.get("descricao_tecnica", ""),
                height=100,
                key="descricao_tecnica",
                placeholder="Descreva as competências técnicas e infraestrutura disponível..."
            )
        
        with col2:
            history = st.text_area(
                "Histórico em P&D e Inovação",
                value=st.session_state.company_profile.get("historico_pd", ""),
                height=100,
                key="historico_pd",
                placeholder="Projetos anteriores, patentes, publicações, experiência com fomento..."
            )
        
        certifications = st.text_input(
            "Certificações Relevantes",
            value=st.session_state.company_profile.get("certificacoes", ""),
            key="certificacoes",
            placeholder="Ex: PIPE, Empresa Inovadora, ISO, etc."
        )
        
        # Save profile to session
        st.session_state.company_profile = {
            "nome_empresa": company_name,
            "cnpj": cnpj,
            "natureza_juridica": nature,
            "porte": size,
            "estado_regiao": state,
            "area_atuacao": area,
            "descricao_tecnica": description,
            "historico_pd": history,
            "certificacoes": certifications,
            "contrapartida_percentual": contrapartida,
            "trl_habitual": trl
        }
        
        st.markdown("---")
        
        if st.button("🔍 Analisar Aderência", use_container_width=True):
            with st.spinner("⏳ Avaliando aderência..."):
                try:
                    diagnosis = evaluate_company_adherence(
                        st.session_state.company_profile,
                        st.session_state.edital_data
                    )
                    st.session_state.diagnosis_results = diagnosis
                    
                    # Calculate weighted score
                    graduated_scores = diagnosis.get("criterios_graduais", {})
                    weighted_score = calculate_weighted_score(graduated_scores)
                    classification, recommendation = get_score_classification(weighted_score)
                    
                    st.success("✅ Análise concluída!")
                    
                    # Display results
                    st.markdown("### 📊 Resultados da Análise")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Pontuação Geral", f"{weighted_score}/10")
                    with col2:
                        st.metric("Classificação", classification)
                    with col3:
                        st.metric("Status", "✅ Recomendado" if weighted_score >= 6 else "⚠️ Revisar")
                    
                    st.markdown(f"**Recomendação:** {recommendation}")
                    
                    # Binary criteria
                    st.markdown("#### Critérios Binários (Eliminatórios)")
                    binary_criteria = diagnosis.get("criterios_binarios", {})
                    
                    binary_passed = True
                    for criterion_name, criterion_data in binary_criteria.items():
                        passed = criterion_data.get("passou", False)
                        message = criterion_data.get("mensagem", "")
                        
                        if passed:
                            st.success(f"✅ {criterion_name.replace('_', ' ').title()}")
                        else:
                            st.error(f"❌ {criterion_name.replace('_', ' ').title()}")
                            binary_passed = False
                        
                        st.caption(message)
                    
                    if not binary_passed:
                        st.markdown("""
                        <div class="error-box">
                        <strong>⚠️ ATENÇÃO:</strong> Existem critérios binários não atendidos. 
                        A proposta será inabilitada se estes não forem resolvidos.
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Graduated criteria - Radar chart
                    st.markdown("#### Critérios Graduais (Pontuação)")
                    
                    graduated_criteria = diagnosis.get("criterios_graduais", {})
                    
                    # Prepare data for radar chart
                    categories = [cat.replace('_', ' ').title() for cat in graduated_criteria.keys()]
                    values = [graduated_criteria[cat].get("nota", 0) for cat in graduated_criteria.keys()]
                    
                    fig = go.Figure(data=go.Scatterpolar(
                        r=values,
                        theta=categories,
                        fill='toself',
                        name='Pontuação'
                    ))
                    
                    fig.update_layout(
                        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
                        showlegend=False,
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Detailed scores
                    st.markdown("#### Detalhes dos Critérios")
                    
                    scores_data = []
                    for criterion_name, criterion_data in graduated_criteria.items():
                        scores_data.append({
                            "Critério": criterion_name.replace('_', ' ').title(),
                            "Nota": criterion_data.get("nota", 0),
                            "Justificativa": criterion_data.get("justificativa", "")
                        })
                    
                    scores_df = pd.DataFrame(scores_data)
                    st.dataframe(scores_df, use_container_width=True, hide_index=True)
                    
                    # Recommendations for improvement
                    st.markdown("#### 💡 Recomendações para Melhoria")
                    
                    for criterion_name, criterion_data in graduated_criteria.items():
                        score = criterion_data.get("nota", 0)
                        if score < 6:
                            st.markdown(f"""
                            <div class="warning-box">
                            <strong>{criterion_name.replace('_', ' ').title()}</strong> (Nota: {score}/10)
                            <br>{criterion_data.get("justificativa", "")}
                            </div>
                            """, unsafe_allow_html=True)
                    
                except Exception as e:
                    st.error(f"❌ Erro ao analisar aderência: {str(e)}")

elif page == "🤝 Recomendador de Arranjos":
    st.markdown('<h2 class="section-header">🤝 Recomendador de Arranjos</h2>', unsafe_allow_html=True)
    
    if not st.session_state.diagnosis_results:
        st.warning("⚠️ Por favor, complete a análise de aderência primeiro")
    else:
        st.markdown("""
        Com base na análise de aderência e no perfil da Agnest Farm Lab, 
        esta seção recomenda a melhor estrutura de arranjo para o edital.
        """)
        
        edital = st.session_state.edital_data
        company = st.session_state.company_profile
        
        st.markdown("### 📊 Análise de Arranjos")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Arranjo Simples")
            st.markdown("""
            **Estrutura:**
            - 1 Empresa Proponente (Agnest)
            - 1+ ICT Parceira (EMBRAPA, etc.)
            - Coexecutoras opcionais
            
            **Valor:**
            - Mínimo: R$ 5 milhões
            - Máximo: R$ 25 milhões
            
            **Vantagens:**
            ✅ Processo mais simples
            ✅ Menor burocracia
            ✅ Decisão rápida
            
            **Desvantagens:**
            ❌ Limite de valor menor
            ❌ Menos parceiros para compartilhar risco
            """)
            
            if st.button("📋 Detalhes Arranjo Simples"):
                st.info("""
                **Recomendado para:**
                - Projetos com orçamento até R$ 25 milhões
                - Agnest como proponente principal
                - Foco em inovação específica
                - Parceria com EMBRAPA como ICT
                """)
        
        with col2:
            st.markdown("#### Arranjo em Rede")
            st.markdown("""
            **Estrutura:**
            - 1 Empresa Proponente (Agnest)
            - 2+ Empresas Coexecutoras
            - 1+ ICT Parceira
            - Mínimo 5% do orçamento para ICT
            
            **Valor:**
            - Mínimo: R$ 5 milhões
            - Máximo: R$ 40 milhões
            
            **Vantagens:**
            ✅ Maior limite de valor
            ✅ Distribuição de risco
            ✅ Maior impacto potencial
            
            **Desvantagens:**
            ❌ Mais complexo de coordenar
            ❌ Maior burocracia
            ❌ Decisão mais lenta
            """)
            
            if st.button("📋 Detalhes Arranjo em Rede"):
                st.info("""
                **Recomendado para:**
                - Projetos com orçamento > R$ 25 milhões
                - Ecossistema completo de parceiros
                - Maior impacto e escalabilidade
                - Múltiplas empresas do AgNest
                """)
        
        st.markdown("---")
        
        st.markdown("### 🎯 Recomendação Baseada na Análise")
        
        # Simple logic for recommendation
        edital_budget = edital.get("orcamento_total", "R$ 300 milhões")
        company_size = company.get("porte", "ME")
        
        if "40" in edital.get("valor_maximo", "25"):  # Rede arrangement
            recommendation = "Arranjo em Rede"
            reason = "O edital permite arranjos em rede com limite de até R$ 40 milhões"
        else:
            recommendation = "Arranjo Simples"
            reason = "O edital é mais adequado para arranjos simples"
        
        st.markdown(f"""
        <div class="success-box">
        <strong>✅ Recomendação: {recommendation}</strong>
        <br><br>
        <strong>Motivo:</strong> {reason}
        <br><br>
        <strong>Próximos Passos:</strong>
        1. Identifique os parceiros necessários no Banco de Parceiros
        2. Valide a disponibilidade de cada parceiro
        3. Negocie os termos de participação
        4. Prepare a documentação necessária
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 👥 Parceiros Recomendados")
        
        st.markdown("#### ICTs Sugeridas")
        st.info("""
        - **EMBRAPA** (Parceiro institucional principal do AgNest)
        - Outras ICTs especializadas conforme a linha temática
        """)
        
        st.markdown("#### Empresas Coexecutoras Potenciais")
        st.info("""
        - Startups do ecossistema AgNest
        - Empresas especializadas nas verticais temáticas
        - Fornecedores de tecnologia
        - Empresas de validação e testes
        """)

elif page == "👥 Banco de Parceiros":
    st.markdown('<h2 class="section-header">👥 Banco de Parceiros</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    Gerencie seu banco de parceiros: ICTs, empresas e relacionamentos conhecidos.
    """)
    
    tab1, tab2, tab3 = st.tabs(["📋 Listar Parceiros", "➕ Adicionar Parceiro", "🔍 Buscar Parceiros"])
    
    with tab1:
        st.markdown("### Parceiros Registrados")
        
        if len(st.session_state.partners_db) == 0:
            st.info("Nenhum parceiro registrado ainda. Adicione parceiros na aba 'Adicionar Parceiro'.")
        else:
            partners_df = pd.DataFrame(st.session_state.partners_db)
            st.dataframe(partners_df, use_container_width=True, hide_index=True)
    
    with tab2:
        st.markdown("### Adicionar Novo Parceiro")
        
        col1, col2 = st.columns(2)
        
        with col1:
            partner_name = st.text_input("Nome do Parceiro")
            partner_type = st.selectbox(
                "Tipo",
                ["ICT Pública", "ICT Privada", "Empresa", "Startup", "Universidade"]
            )
            contact_name = st.text_input("Contato (Nome)")
        
        with col2:
            partner_cnpj = st.text_input("CNPJ/CPF")
            partner_area = st.text_input("Área de Especialidade")
            contact_email = st.text_input("Email de Contato")
        
        partner_description = st.text_area(
            "Descrição/Histórico de Relacionamento",
            height=100,
            placeholder="Descreva a experiência com este parceiro, projetos anteriores, etc."
        )
        
        if st.button("✅ Adicionar Parceiro", use_container_width=True):
            if partner_name and partner_type:
                new_partner = {
                    "Nome": partner_name,
                    "Tipo": partner_type,
                    "CNPJ/CPF": partner_cnpj,
                    "Área": partner_area,
                    "Contato": contact_name,
                    "Email": contact_email,
                    "Descrição": partner_description,
                    "Data Adição": datetime.now().strftime("%d/%m/%Y")
                }
                st.session_state.partners_db.append(new_partner)
                st.success("✅ Parceiro adicionado com sucesso!")
            else:
                st.error("❌ Por favor, preencha os campos obrigatórios")
    
    with tab3:
        st.markdown("### Buscar Parceiros")
        
        search_term = st.text_input("Buscar por nome ou área")
        
        if search_term:
            filtered_partners = [
                p for p in st.session_state.partners_db
                if search_term.lower() in p.get("Nome", "").lower() or
                   search_term.lower() in p.get("Área", "").lower()
            ]
            
            if filtered_partners:
                partners_df = pd.DataFrame(filtered_partners)
                st.dataframe(partners_df, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum parceiro encontrado com esse termo.")

elif page == "📝 Gerador de Proposta":
    st.markdown('<h2 class="section-header">📝 Gerador de Proposta</h2>', unsafe_allow_html=True)
    
    if not st.session_state.diagnosis_results:
        st.warning("⚠️ Por favor, complete a análise de aderência primeiro")
    else:
        st.markdown("""
        Descreva sua ideia de projeto e a ferramenta gerará um rascunho automático 
        baseado no edital e no perfil da sua empresa.
        """)
        
        project_idea = st.text_area(
            "📝 Descreva a Ideia do Projeto",
            height=150,
            placeholder="""
            Descreva brevemente:
            - O problema que será resolvido
            - A solução proposta
            - Como se alinha com as verticais do AgNest
            - Impacto esperado
            """
        )
        
        if st.button("🚀 Gerar Rascunho de Proposta", use_container_width=True):
            if not project_idea:
                st.error("❌ Por favor, descreva a ideia do projeto")
            else:
                with st.spinner("⏳ Gerando proposta..."):
                    try:
                        proposal = generate_proposal_draft(
                            st.session_state.company_profile,
                            st.session_state.edital_data,
                            project_idea
                        )
                        st.session_state.proposal_sections = proposal
                        st.success("✅ Proposta gerada com sucesso!")
                        
                        # Display sections
                        st.markdown("### 📄 Rascunho da Proposta")
                        
                        sections = [
                            ("resumo_executivo", "1. Resumo Executivo"),
                            ("problema_oportunidade", "2. Problema e Oportunidade"),
                            ("objetivo_geral", "3. Objetivo Geral"),
                            ("objetivos_especificos", "4. Objetivos Específicos"),
                            ("metodologia", "5. Metodologia"),
                            ("plano_trabalho", "6. Plano de Trabalho"),
                            ("equipe_necessaria", "7. Perfil da Equipe Necessária"),
                            ("resultados_esperados", "8. Resultados Esperados"),
                            ("indicadores_sucesso", "9. Indicadores de Sucesso"),
                            ("impacto_economico_social", "10. Impacto Econômico e Social")
                        ]
                        
                        for key, title in sections:
                            with st.expander(title):
                                content = proposal.get(key, "Conteúdo não disponível")
                                st.write(content)
                                
                                # Allow editing
                                edited_content = st.text_area(
                                    f"Editar {title}",
                                    value=content,
                                    height=150,
                                    key=f"edit_{key}",
                                    label_visibility="collapsed"
                                )
                                
                                # Update in session
                                st.session_state.proposal_sections[key] = edited_content
                        
                        st.markdown("---")
                        st.info("💡 Você pode editar cada seção acima. As alterações serão salvas para exportação.")
                        
                    except Exception as e:
                        st.error(f"❌ Erro ao gerar proposta: {str(e)}")

elif page == "📥 Exportar Resultados":
    st.markdown('<h2 class="section-header">📥 Exportar Resultados</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    Exporte seus resultados em formato Word para apresentação e arquivamento.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Exportar Diagnóstico")
        
        if st.session_state.diagnosis_results:
            if st.button("📥 Baixar Diagnóstico (Word)", use_container_width=True):
                try:
                    # Calculate weighted score
                    graduated_scores = st.session_state.diagnosis_results.get("criterios_graduais", {})
                    weighted_score = calculate_weighted_score(graduated_scores)
                    classification, recommendation = get_score_classification(weighted_score)
                    
                    # Create document
                    doc = create_diagnosis_document(
                        st.session_state.company_profile,
                        st.session_state.edital_data,
                        st.session_state.diagnosis_results,
                        weighted_score,
                        classification,
                        recommendation
                    )
                    
                    # Save and provide download
                    filename = f"Diagnostico_FINEP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                    filepath = f"/tmp/{filename}"
                    save_document(doc, filepath)
                    
                    with open(filepath, "rb") as f:
                        st.download_button(
                            label="📥 Clique para Baixar",
                            data=f.read(),
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    
                    st.success("✅ Documento pronto para download!")
                    
                except Exception as e:
                    st.error(f"❌ Erro ao gerar documento: {str(e)}")
        else:
            st.info("⚠️ Complete a análise de aderência para exportar o diagnóstico")
    
    with col2:
        st.markdown("### 📝 Exportar Proposta")
        
        if st.session_state.proposal_sections:
            if st.button("📥 Baixar Proposta (Word)", use_container_width=True):
                try:
                    # Create document
                    doc = create_proposal_document(
                        st.session_state.company_profile,
                        st.session_state.edital_data,
                        st.session_state.proposal_sections,
                        "Projeto descrito na ferramenta"
                    )
                    
                    # Save and provide download
                    filename = f"Proposta_FINEP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
                    filepath = f"/tmp/{filename}"
                    save_document(doc, filepath)
                    
                    with open(filepath, "rb") as f:
                        st.download_button(
                            label="📥 Clique para Baixar",
                            data=f.read(),
                            file_name=filename,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    
                    st.success("✅ Documento pronto para download!")
                    
                except Exception as e:
                    st.error(f"❌ Erro ao gerar documento: {str(e)}")
        else:
            st.info("⚠️ Gere uma proposta primeiro para exportar")
    
    st.markdown("---")
    st.markdown("### 📊 Exportar Relatório Executivo")
    
    if st.button("📥 Gerar Relatório Completo (Word)", use_container_width=True):
        if st.session_state.diagnosis_results and st.session_state.proposal_sections:
            try:
                st.info("✅ Relatório completo será gerado com diagnóstico + proposta")
                st.success("Funcionalidade disponível na próxima versão")
            except Exception as e:
                st.error(f"❌ Erro: {str(e)}")
        else:
            st.warning("⚠️ Complete todas as seções para gerar relatório completo")

# ─── GERENCIADOR DE FONTES ───────────────────────────────────────────────────
elif page == "🌐 Gerenciador de Fontes":
    st.markdown('<h2 class="section-header">🌐 Gerenciador de Fontes de Editais</h2>', unsafe_allow_html=True)
    st.markdown("Gerencie as fontes monitoradas semanalmente pelo agente de busca. Adicione novas URLs, verifique o status e aprove sugestões automáticas do agente.")

    # ── Estatísticas ──
    stats = get_estatisticas()
    db = carregar_fontes()
    fontes_todas = db.get("fontes", [])

    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
    with col_s1:
        st.metric("Total de Fontes", stats["total"])
    with col_s2:
        st.metric("🟢 Com Edital Ativo", stats["com_edital_ativo"])
    with col_s3:
        st.metric("⚪ Não Verificadas", stats["nao_verificadas"])
    with col_s4:
        st.metric("🤖 Sugestões Pendentes", stats["pendentes_aprovacao"])
    with col_s5:
        st.metric("✅ Ativas", stats["ativas"])

    st.markdown("---")

    # ── Abas ──
    tab_painel, tab_adicionar, tab_sugestoes, tab_verificar = st.tabs([
        "📋 Painel de Status",
        "➕ Adicionar Nova Fonte",
        "🤖 Sugestões do Agente",
        "🔄 Verificar Status"
    ])

    # ── Tab 1: Painel de Status ──
    with tab_painel:
        st.markdown("### 📋 Todas as Fontes Monitoradas")

        # Filtros
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtro_cat = st.selectbox("Filtrar por categoria", ["Todas", "nacional", "internacional", "privado"])
        with col_f2:
            filtro_status = st.selectbox("Filtrar por status", ["Todas", "Com edital ativo", "Sem edital", "Não verificada"])
        with col_f3:
            filtro_ativo = st.selectbox("Filtrar por ativação", ["Todas", "Ativas", "Inativas"])

        # Aplicar filtros
        fontes_filtradas = fontes_todas
        if filtro_cat != "Todas":
            fontes_filtradas = [f for f in fontes_filtradas if f.get("categoria") == filtro_cat]
        if filtro_status == "Com edital ativo":
            fontes_filtradas = [f for f in fontes_filtradas if f.get("edital_ativo") is True]
        elif filtro_status == "Sem edital":
            fontes_filtradas = [f for f in fontes_filtradas if f.get("edital_ativo") is False]
        elif filtro_status == "Não verificada":
            fontes_filtradas = [f for f in fontes_filtradas if f.get("ultima_verificacao") is None]
        if filtro_ativo == "Ativas":
            fontes_filtradas = [f for f in fontes_filtradas if f.get("ativo", True)]
        elif filtro_ativo == "Inativas":
            fontes_filtradas = [f for f in fontes_filtradas if not f.get("ativo", True)]

        st.markdown(f"**{len(fontes_filtradas)} fonte(s) encontrada(s)**")
        st.markdown("")

        # Cards de fontes
        for fonte in fontes_filtradas:
            # Determinar indicador de status
            edital_ativo = fonte.get("edital_ativo")
            verificada = fonte.get("ultima_verificacao") is not None
            ativo = fonte.get("ativo", True)
            pendente = fonte.get("pendente_aprovacao", False)

            if not ativo:
                bolinha = "⚫"
                status_txt = "Inativa"
                cor_borda = "#9E9E9E"
            elif pendente:
                bolinha = "🟡"
                status_txt = "Pendente aprovação"
                cor_borda = "#F57F17"
            elif not verificada:
                bolinha = "⚪"
                status_txt = "Não verificada"
                cor_borda = "#BDBDBD"
            elif edital_ativo:
                bolinha = "🟢"
                status_txt = "Edital ativo"
                cor_borda = "#2E7D32"
            else:
                bolinha = "🔴"
                status_txt = "Sem edital ativo"
                cor_borda = "#C62828"

            ultima_verif = fonte.get("ultima_verificacao")
            if ultima_verif:
                try:
                    dt = datetime.fromisoformat(ultima_verif)
                    ultima_verif_fmt = dt.strftime("%d/%m/%Y %H:%M")
                except:
                    ultima_verif_fmt = ultima_verif[:16]
            else:
                ultima_verif_fmt = "Nunca verificada"

            resumo = fonte.get("resumo_status", fonte.get("descricao", ""))
            total_enc = fonte.get("total_editais_encontrados", 0)

            with st.container():
                st.markdown(
                    f"""
                    <div style="border:1px solid {cor_borda};border-left:5px solid {cor_borda};
                                border-radius:8px;padding:14px 18px;margin-bottom:10px;
                                background:#fff;box-shadow:0 1px 3px rgba(0,0,0,0.06);">
                        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                            <div style="flex:1;">
                                <span style="font-size:20px;margin-right:8px;">{bolinha}</span>
                                <strong style="font-size:15px;color:#1a1a1a;">{fonte['nome']}</strong>
                                <span style="margin-left:10px;background:#EEE;color:#555;padding:2px 8px;
                                            border-radius:10px;font-size:11px;">{fonte.get('categoria','').upper()}</span>
                                <span style="margin-left:6px;background:#E3F2FD;color:#1565C0;padding:2px 8px;
                                            border-radius:10px;font-size:11px;">{fonte.get('tipo','')}</span>
                                <span style="margin-left:6px;background:#F3E5F5;color:#6A1B9A;padding:2px 8px;
                                            border-radius:10px;font-size:11px;">🌍 {fonte.get('pais','')}</span>
                            </div>
                            <div style="text-align:right;font-size:12px;color:#888;">
                                <div><strong>{status_txt}</strong></div>
                                <div>Última verificação: {ultima_verif_fmt}</div>
                                <div>Editais encontrados: {total_enc}</div>
                            </div>
                        </div>
                        <div style="margin-top:8px;font-size:13px;color:#555;">{resumo}</div>
                        <div style="margin-top:6px;">
                            <a href="{fonte['url']}" target="_blank" style="font-size:12px;color:#1976D2;
                               text-decoration:none;">🔗 {fonte['url'][:70]}{'...' if len(fonte['url'])>70 else ''}</a>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                col_btn1, col_btn2, col_btn3, _ = st.columns([1, 1, 1, 4])
                with col_btn1:
                    label_toggle = "⏸ Desativar" if ativo and not pendente else "▶ Ativar"
                    if st.button(label_toggle, key=f"toggle_{fonte['id']}", use_container_width=True):
                        res = toggle_fonte(fonte["id"])
                        st.success(res["mensagem"])
                        st.rerun()
                with col_btn2:
                    if st.button("🗑 Remover", key=f"remove_{fonte['id']}", use_container_width=True):
                        res = remover_fonte(fonte["id"])
                        st.success(res["mensagem"])
                        st.rerun()
                with col_btn3:
                    if pendente:
                        if st.button("✅ Aprovar", key=f"aprovar_{fonte['id']}", use_container_width=True):
                            res = aprovar_fonte_sugerida(fonte["id"])
                            st.success(res["mensagem"])
                            st.rerun()

    # ── Tab 2: Adicionar Nova Fonte ──
    with tab_adicionar:
        st.markdown("### ➕ Adicionar Nova Fonte Manualmente")
        st.markdown("Adicione qualquer URL de edital público ou privado, nacional ou internacional.")

        with st.form("form_nova_fonte"):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                nome_nova = st.text_input("Nome da Fonte *", placeholder="Ex: FAPEMIG – Editais de Pesquisa")
                url_nova = st.text_input("URL *", placeholder="https://www.fapemig.br/editais")
                tipo_novo = st.selectbox("Tipo", ["subvenção", "financiamento", "pesquisa", "prêmio", "aceleração", "inovação", "agro", "outro"])
            with col_a2:
                pais_novo = st.text_input("País / Região", placeholder="Brasil", value="Brasil")
                categoria_nova = st.selectbox("Categoria", ["nacional", "internacional", "privado"])
                descricao_nova = st.text_area("Descrição", placeholder="Breve descrição da fonte...", height=100)

            submitted = st.form_submit_button("➕ Adicionar Fonte", use_container_width=True, type="primary")
            if submitted:
                if nome_nova and url_nova:
                    res = adicionar_fonte(
                        nome=nome_nova, url=url_nova, tipo=tipo_novo,
                        pais=pais_novo, categoria=categoria_nova,
                        descricao=descricao_nova, adicionado_por="usuario"
                    )
                    if res["sucesso"]:
                        st.success(f"✅ {res['mensagem']}")
                        st.rerun()
                    else:
                        st.error(f"❌ {res['mensagem']}")
                else:
                    st.error("❌ Nome e URL são obrigatórios.")

        st.markdown("---")
        st.markdown("### 💡 Exemplos de Fontes para Adicionar")
        exemplos = [
            ("FAPERJ – Editais", "https://www.faperj.br/editais", "pesquisa", "Brasil"),
            ("FAPEMIG – Chamadas", "https://fapemig.br/pt/chamadas", "pesquisa", "Brasil"),
            ("FAPERGS – Editais", "https://fapergs.rs.gov.br/editais", "pesquisa", "Brasil"),
            ("EIT Food – Calls", "https://www.eitfood.eu/opportunities", "inovação", "União Europeia"),
            ("PRIMA Programme", "https://prima-med.org/calls-for-proposals/", "pesquisa", "União Europeia"),
            ("USDA SBIR/STTR", "https://nifa.usda.gov/grants", "pesquisa", "EUA"),
        ]
        for nome_ex, url_ex, tipo_ex, pais_ex in exemplos:
            with st.expander(f"📌 {nome_ex}"):
                st.code(url_ex)
                st.caption(f"Tipo: {tipo_ex} | País: {pais_ex}")
                if st.button(f"Adicionar {nome_ex}", key=f"add_ex_{nome_ex}"):
                    res = adicionar_fonte(nome_ex, url_ex, tipo_ex, pais_ex,
                                         "internacional" if pais_ex != "Brasil" else "nacional")
                    if res["sucesso"]:
                        st.success(f"✅ {res['mensagem']}")
                        st.rerun()
                    else:
                        st.warning(res["mensagem"])

    # ── Tab 3: Sugestões do Agente ──
    with tab_sugestoes:
        st.markdown("### 🤖 Descoberta Automática de Novas Fontes")
        st.markdown(
            "O agente de IA analisa o perfil da Agnest Farm Lab e sugere novas fontes "
            "de editais relevantes que ainda não estão cadastradas. Você aprova antes de ativar."
        )

        pendentes = [f for f in fontes_todas if f.get("pendente_aprovacao", False)]
        if pendentes:
            st.info(f"🔔 Há **{len(pendentes)} sugestão(ões)** aguardando sua aprovação na aba **Painel de Status**.")

        if st.button("🤖 Descobrir Novas Fontes com IA", type="primary", use_container_width=True):
            with st.spinner("🔎 O agente está buscando novas fontes relevantes..."):
                try:
                    novas = descobrir_novas_fontes()
                    if novas:
                        n = adicionar_fontes_sugeridas(novas)
                        st.success(f"✅ **{n} novas fontes** descobertas e adicionadas como pendentes de aprovação!")
                        st.markdown("Acesse a aba **Painel de Status** → filtre por 'Pendente aprovação' para revisar e aprovar.")
                        st.markdown("**Fontes sugeridas:**")
                        for f in novas[:n]:
                            st.markdown(f"- 🆕 **{f['nome']}** ({f.get('pais','')}) — {f.get('descricao','')}")
                            st.caption(f"  🔗 {f.get('url','')}")
                    else:
                        st.info("Nenhuma nova fonte foi encontrada. Todas as sugestões já estão cadastradas.")
                except Exception as e:
                    st.error(f"❌ Erro na descoberta: {str(e)}")

        st.markdown("---")
        st.markdown("### 📊 Fontes por Categoria")
        col_cat1, col_cat2, col_cat3 = st.columns(3)
        with col_cat1:
            st.metric("🇧🇷 Nacionais", stats["nacionais"])
        with col_cat2:
            st.metric("🌍 Internacionais", stats["internacionais"])
        with col_cat3:
            st.metric("🏢 Privadas", stats["privadas"])

    # ── Tab 4: Verificar Status ──
    with tab_verificar:
        st.markdown("### 🔄 Verificar Status das Fontes")
        st.markdown(
            "Verifica quais fontes estão acessíveis e se possuem editais ativos no momento. "
            "Cada fonte é visitada e analisada com IA. **Pode levar alguns minutos.**"
        )

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if st.button("🔄 Verificar Todas as Fontes Ativas", type="primary", use_container_width=True):
                fontes_ativas = get_fontes_ativas()
                progress = st.progress(0)
                status_text = st.empty()
                resultados = []
                for i, fonte in enumerate(fontes_ativas):
                    status_text.text(f"Verificando [{i+1}/{len(fontes_ativas)}]: {fonte['nome']}...")
                    progress.progress((i + 1) / len(fontes_ativas))
                    resultado = verificar_status_fonte(fonte)
                    resultados.append(resultado)
                    # Atualizar no banco
                    db_atual = carregar_fontes()
                    for j, f in enumerate(db_atual["fontes"]):
                        if f["id"] == fonte["id"]:
                            db_atual["fontes"][j] = resultado
                            break
                    salvar_fontes(db_atual)
                status_text.text("✅ Verificação concluída!")
                progress.progress(1.0)
                ativos = sum(1 for r in resultados if r.get("edital_ativo"))
                st.success(f"✅ Verificação concluída! **{ativos}/{len(resultados)}** fontes com edital ativo.")
                st.rerun()
        with col_v2:
            fonte_selecionada = st.selectbox(
                "Verificar fonte específica:",
                options=[f["id"] for f in fontes_todas if f.get("ativo", True)],
                format_func=lambda fid: next((f["nome"] for f in fontes_todas if f["id"] == fid), fid)
            )
            if st.button("🔍 Verificar Esta Fonte", use_container_width=True):
                fonte_obj = next((f for f in fontes_todas if f["id"] == fonte_selecionada), None)
                if fonte_obj:
                    with st.spinner(f"Verificando {fonte_obj['nome']}..."):
                        resultado = verificar_status_fonte(fonte_obj)
                        db_atual = carregar_fontes()
                        for j, f in enumerate(db_atual["fontes"]):
                            if f["id"] == fonte_selecionada:
                                db_atual["fontes"][j] = resultado
                                break
                        salvar_fontes(db_atual)
                    edital = resultado.get("edital_ativo")
                    if edital:
                        st.success(f"🟢 **Edital ativo!** {resultado.get('resumo_status','')}")
                    elif edital is False:
                        st.warning(f"🔴 **Sem edital ativo.** {resultado.get('resumo_status','')}")
                    else:
                        st.info(f"⚪ Não foi possível determinar. Erro: {resultado.get('erro','')}")

        st.markdown("---")
        st.markdown("### 📅 Histórico de Verificações")
        verificadas = [f for f in fontes_todas if f.get("ultima_verificacao")]
        if verificadas:
            df_verif = pd.DataFrame([{
                "Fonte": f["nome"],
                "Status": "🟢 Ativo" if f.get("edital_ativo") else "🔴 Inativo",
                "Última Verificação": f.get("ultima_verificacao","")[:16].replace("T"," "),
                "Editais Encontrados": f.get("total_editais_encontrados", 0),
                "Resumo": f.get("resumo_status", "")[:60]
            } for f in sorted(verificadas, key=lambda x: x.get("ultima_verificacao",""), reverse=True)])
            st.dataframe(df_verif, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma fonte verificada ainda. Clique em 'Verificar Todas' para começar.")

# ─── GERENCIAR USUÁRIOS ────────────────────────────────────────────────────────────
elif page == "🔐 Gerenciar Usuários":
    st.markdown('<h2 class="section-header">🔐 Gerenciamento de Usuários</h2>', unsafe_allow_html=True)
    st.markdown("Gerencie os usuários com acesso ao FINEP Copilot. Todos os usuários são administradores e podem contribuir com fontes e editais.")

    current_user = st.session_state.current_user
    users = list_users()

    # ── Métricas ──
    col_u1, col_u2 = st.columns(2)
    with col_u1:
        st.metric("👥 Total de Usuários", len(users))
    with col_u2:
        st.metric("🛡️ Todos Admin", len([u for u in users if u['role'] == 'admin']))

    st.markdown("---")

    tab_lista, tab_criar, tab_senha = st.tabs([
        "👥 Usuários Cadastrados",
        "➕ Criar Novo Usuário",
        "🔑 Alterar Senha"
    ])

    # ── Aba 1: Lista de usuários ──
    with tab_lista:
        st.markdown("### Usuários com Acesso")
        for u in users:
            with st.container(border=True):
                col_a, col_b, col_c = st.columns([3, 2, 1])
                with col_a:
                    st.markdown(f"👤 **{u['name']}** &nbsp; `@{u['username']}`")
                    st.caption(f"✉️ {u['email']} &nbsp;&nbsp; 📅 Criado em {u['created_at'][:10]}")
                with col_b:
                    st.markdown(f"🛡️ Papel: **{u['role'].upper()}**")
                with col_c:
                    if u['username'] != current_user['username']:
                        if st.button("🗑️ Remover", key=f"del_{u['username']}"):
                            ok, msg = delete_user(u['username'], current_user['username'])
                            if ok:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.caption("👋 Você")

    # ── Aba 2: Criar usuário ──
    with tab_criar:
        st.markdown("### Criar Novo Usuário Admin")
        st.info("🛡️ Todos os novos usuários recebem perfil **Admin** e podem contribuir com fontes, editais e análises.")

        with st.form("form_criar_usuario", clear_on_submit=True):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                new_name = st.text_input("👤 Nome Completo", placeholder="Maria Silva")
                new_username = st.text_input("🌟 Username", placeholder="maria.silva")
            with col_f2:
                new_email = st.text_input("✉️ E-mail", placeholder="maria@empresa.com")
                new_password = st.text_input("🔒 Senha Inicial", type="password", placeholder="Mínimo 6 caracteres")

            criar_btn = st.form_submit_button("➕ Criar Usuário", use_container_width=True)

            if criar_btn:
                if not all([new_name, new_username, new_email, new_password]):
                    st.error("❌ Preencha todos os campos.")
                else:
                    ok, msg = create_user(
                        username=new_username,
                        name=new_name,
                        email=new_email,
                        password=new_password,
                        role="admin",
                        created_by=current_user['username']
                    )
                    if ok:
                        st.success(f"✅ {msg}")
                        st.balloons()
                    else:
                        st.error(f"❌ {msg}")

    # ── Aba 3: Alterar senha ──
    with tab_senha:
        st.markdown("### Alterar Sua Senha")
        with st.form("form_alterar_senha", clear_on_submit=True):
            senha_atual = st.text_input("🔒 Senha Atual", type="password")
            nova_senha = st.text_input("🔑 Nova Senha", type="password", placeholder="Mínimo 6 caracteres")
            confirmar_senha = st.text_input("✅ Confirmar Nova Senha", type="password")
            alterar_btn = st.form_submit_button("🔑 Alterar Senha", use_container_width=True)

            if alterar_btn:
                if not all([senha_atual, nova_senha, confirmar_senha]):
                    st.error("❌ Preencha todos os campos.")
                elif nova_senha != confirmar_senha:
                    st.error("❌ As senhas não coincidem.")
                else:
                    # Verificar senha atual
                    check = authenticate(current_user['username'], senha_atual)
                    if not check:
                        st.error("❌ Senha atual incorreta.")
                    else:
                        ok, msg = update_password(current_user['username'], nova_senha)
                        if ok:
                            st.success(f"✅ {msg}")
                        else:
                            st.error(f"❌ {msg}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>🚀 <strong>FINEP Copilot - Agnest Edition</strong></p>
    <p>Assistente Estratégico de Captura de Recursos em Editais FINEP</p>
    <p>Desenvolvido para a Agnest Farm Lab e seu ecossistema de parceiros</p>
    <p style="margin-top: 1rem;">
        <a href="https://www.agnestfarmlab.com" target="_blank">Agnest Farm Lab</a> | 
        <a href="https://www.finep.gov.br" target="_blank">FINEP</a> | 
        <a href="https://www.embrapa.br" target="_blank">EMBRAPA</a>
    </p>
</div>
""", unsafe_allow_html=True)
