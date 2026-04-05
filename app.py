import streamlit as st
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
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

# Sidebar
with st.sidebar:
    st.markdown("## 🚀 FINEP Copilot")
    st.markdown("**Agnest Farm Lab Edition**")
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
            "📥 Exportar Resultados"
        ]
    )
    
    st.markdown("---")
    st.markdown("### Informações")
    st.info(
        "**FINEP Copilot** é um assistente estratégico para captura de recursos "
        "em editais públicos da FINEP, desenvolvido especificamente para a "
        "Agnest Farm Lab e seu ecossistema de parceiros."
    )

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
