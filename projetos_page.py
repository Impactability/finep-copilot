"""
projetos_page.py — Seção de Projetos do Edital Copilot
Gerencia projetos de captação de recursos, documentos e parceiros.
Cada projeto corresponde a um edital específico sendo trabalhado.
"""

import streamlit as st
from datetime import date, datetime
from db_manager import (
    db_create_projeto, db_list_projetos, db_get_projeto,
    db_update_projeto, db_delete_projeto,
    db_upload_documento, db_list_documentos,
    db_get_documento_conteudo, db_delete_documento,
    db_add_parceiro, db_list_parceiros, db_delete_parceiro,
    db_get_stats
)

# ─── Constantes ───────────────────────────────────────────────────────────────

STATUS_LABELS = {
    "rascunho":     "📝 Rascunho",
    "em_andamento": "🔄 Em Andamento",
    "submetido":    "📤 Submetido",
    "aprovado":     "✅ Aprovado",
    "reprovado":    "❌ Reprovado",
    "cancelado":    "🚫 Cancelado",
}

STATUS_COLORS = {
    "rascunho":     "#9E9E9E",
    "em_andamento": "#1976D2",
    "submetido":    "#F57C00",
    "aprovado":     "#2E7D32",
    "reprovado":    "#C62828",
    "cancelado":    "#757575",
}

ARRANJO_LABELS = {
    "simples":    "🏢 Arranjo Simples",
    "rede":       "🕸️ Rede",
    "consorcio":  "🤝 Consórcio",
    "indefinido": "❓ Indefinido",
}

TIPO_DOC_LABELS = {
    "edital":    "📋 Edital",
    "proposta":  "📝 Proposta",
    "orcamento": "💰 Orçamento",
    "curriculo": "👤 Currículo/CV",
    "certidao":  "📜 Certidão",
    "contrato":  "📃 Contrato",
    "relatorio": "📊 Relatório",
    "outro":     "📎 Outro",
}

MIME_TYPES_ALLOWED = {
    "application/pdf": "PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "Word",
    "application/msword": "Word",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "Excel",
    "application/vnd.ms-excel": "Excel",
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "text/plain": "TXT",
    "application/zip": "ZIP",
}


def _format_currency(value) -> str:
    if not value:
        return "—"
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(value)


def _format_date(d) -> str:
    if not d:
        return "—"
    try:
        if isinstance(d, str):
            return d[:10]
        return d.strftime("%d/%m/%Y")
    except Exception:
        return str(d)


def _format_size(size_bytes: int) -> str:
    if not size_bytes:
        return "—"
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes/1024:.1f} KB"
    else:
        return f"{size_bytes/(1024*1024):.1f} MB"


# ─── Página Principal ─────────────────────────────────────────────────────────

def render_projetos_page(current_user: dict):
    """Renderiza a seção completa de Projetos."""

    st.markdown('<h2 class="section-header">📂 Projetos de Captação</h2>', unsafe_allow_html=True)
    st.markdown(
        "Gerencie seus projetos de captação de recursos. Cada projeto corresponde a um edital "
        "específico e concentra todos os documentos, parceiros e informações necessárias para a submissão."
    )

    # ── Inicializar session state ──
    if "projeto_selecionado_id" not in st.session_state:
        st.session_state.projeto_selecionado_id = None
    if "projeto_view" not in st.session_state:
        st.session_state.projeto_view = "lista"  # lista | detalhe | novo

    # ── Métricas rápidas ──
    stats = db_get_stats()
    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("📂 Total de Projetos", stats.get("total_projetos", 0))
    with col_s2:
        st.metric("📤 Submetidos", stats.get("submetidos", 0))
    with col_s3:
        st.metric("✅ Aprovados", stats.get("aprovados", 0))
    with col_s4:
        valor = stats.get("valor_total_captacao", 0)
        st.metric("💰 Valor em Captação", _format_currency(valor))

    st.markdown("---")

    # ── Roteamento interno ──
    if st.session_state.projeto_view == "novo":
        _render_novo_projeto(current_user)
    elif st.session_state.projeto_view == "detalhe" and st.session_state.projeto_selecionado_id:
        _render_detalhe_projeto(current_user, st.session_state.projeto_selecionado_id)
    else:
        _render_lista_projetos(current_user)


# ─── Lista de Projetos ────────────────────────────────────────────────────────

def _render_lista_projetos(current_user: dict):
    """Renderiza a lista de projetos com filtros."""

    col_btn, col_filtro = st.columns([1, 3])
    with col_btn:
        if st.button("➕ Novo Projeto", use_container_width=True, type="primary"):
            st.session_state.projeto_view = "novo"
            st.rerun()
    with col_filtro:
        filtro_status = st.selectbox(
            "Filtrar por status:",
            ["Todos"] + list(STATUS_LABELS.values()),
            label_visibility="collapsed"
        )

    projetos = db_list_projetos()

    # Aplicar filtro
    if filtro_status != "Todos":
        status_key = next((k for k, v in STATUS_LABELS.items() if v == filtro_status), None)
        if status_key:
            projetos = [p for p in projetos if p["status"] == status_key]

    if not projetos:
        st.info("📭 Nenhum projeto encontrado. Clique em **➕ Novo Projeto** para começar.")
        return

    st.markdown(f"**{len(projetos)} projeto(s) encontrado(s)**")
    st.markdown("")

    for proj in projetos:
        status = proj.get("status", "rascunho")
        status_label = STATUS_LABELS.get(status, status)
        status_color = STATUS_COLORS.get(status, "#9E9E9E")
        score = proj.get("aderencia_score")
        score_str = f"{score:.0f}%" if score else "—"
        prazo = _format_date(proj.get("prazo_submissao"))
        valor = _format_currency(proj.get("valor_solicitado"))
        arranjo = ARRANJO_LABELS.get(proj.get("arranjo_tipo", "indefinido"), "—")

        with st.container(border=True):
            col_a, col_b, col_c = st.columns([4, 2, 1])

            with col_a:
                st.markdown(
                    f"**{proj['nome']}**  "
                    f"<span style='background:{status_color};color:white;padding:2px 8px;"
                    f"border-radius:10px;font-size:0.8rem;'>{status_label}</span>",
                    unsafe_allow_html=True
                )
                if proj.get("edital_nome"):
                    st.caption(f"📋 {proj['edital_nome']}  |  {arranjo}")
                if proj.get("descricao"):
                    desc = proj["descricao"][:120] + "..." if len(proj.get("descricao","")) > 120 else proj.get("descricao","")
                    st.caption(desc)

            with col_b:
                st.markdown(f"**Prazo:** {prazo}")
                st.markdown(f"**Valor:** {valor}")
                st.markdown(f"**Aderência:** {score_str}")

            with col_c:
                if st.button("📂 Abrir", key=f"open_{proj['id']}", use_container_width=True):
                    st.session_state.projeto_selecionado_id = proj["id"]
                    st.session_state.projeto_view = "detalhe"
                    st.rerun()
                if st.button("🗑️", key=f"del_{proj['id']}", help="Remover projeto"):
                    ok, msg = db_delete_projeto(proj["id"], current_user["username"])
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


# ─── Novo Projeto ─────────────────────────────────────────────────────────────

def _render_novo_projeto(current_user: dict):
    """Formulário para criar novo projeto."""

    col_back, _ = st.columns([1, 5])
    with col_back:
        if st.button("← Voltar"):
            st.session_state.projeto_view = "lista"
            st.rerun()

    st.markdown("### ➕ Novo Projeto de Captação")
    st.markdown("Preencha as informações do edital que deseja trabalhar. Você poderá adicionar documentos e parceiros após criar o projeto.")

    with st.form("form_novo_projeto", clear_on_submit=False):
        st.markdown("#### 📋 Informações do Projeto")
        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("🏷️ Nome do Projeto *", placeholder="Ex: FINEP Cadeias Agro 2026")
            edital_nome = st.text_input("📋 Nome do Edital", placeholder="Ex: Mais Inovação Brasil – Cadeias Agroindustriais")
            edital_fonte = st.text_input("🏛️ Fonte / Órgão", placeholder="Ex: FINEP, BNDES, Horizon Europe")
            edital_url = st.text_input("🔗 URL do Edital", placeholder="https://...")

        with col2:
            valor_str = st.text_input("💰 Valor Solicitado (R$)", placeholder="Ex: 1500000")
            prazo_input = st.date_input("📅 Prazo de Submissão", value=None, min_value=date.today())
            arranjo_tipo = st.selectbox(
                "🤝 Tipo de Arranjo",
                options=list(ARRANJO_LABELS.keys()),
                format_func=lambda x: ARRANJO_LABELS[x]
            )
            status_inicial = st.selectbox(
                "📌 Status Inicial",
                options=["rascunho", "em_andamento"],
                format_func=lambda x: STATUS_LABELS[x]
            )

        descricao = st.text_area("📝 Descrição / Objetivo do Projeto", placeholder="Descreva brevemente o projeto e sua proposta de valor...", height=100)
        notas = st.text_area("🗒️ Notas Internas", placeholder="Observações, lembretes, contatos importantes...", height=80)

        submitted = st.form_submit_button("✅ Criar Projeto", use_container_width=True, type="primary")

        if submitted:
            if not nome.strip():
                st.error("❌ O nome do projeto é obrigatório.")
            else:
                # Converter valor
                valor = None
                if valor_str.strip():
                    try:
                        valor = float(valor_str.replace("R$", "").replace(".", "").replace(",", ".").strip())
                    except ValueError:
                        st.error("❌ Valor inválido. Use apenas números.")
                        st.stop()

                ok, msg, proj_id = db_create_projeto(
                    nome=nome.strip(),
                    descricao=descricao.strip(),
                    edital_nome=edital_nome.strip(),
                    edital_url=edital_url.strip(),
                    edital_fonte=edital_fonte.strip(),
                    valor_solicitado=valor,
                    prazo_submissao=prazo_input if prazo_input else None,
                    arranjo_tipo=arranjo_tipo,
                    notas=notas.strip(),
                    created_by=current_user["username"]
                )
                if ok:
                    st.success(f"✅ {msg}")
                    st.session_state.projeto_selecionado_id = proj_id
                    st.session_state.projeto_view = "detalhe"
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")


# ─── Detalhe do Projeto ───────────────────────────────────────────────────────

def _render_detalhe_projeto(current_user: dict, projeto_id: int):
    """Renderiza a página de detalhe de um projeto com abas."""

    projeto = db_get_projeto(projeto_id)
    if not projeto:
        st.error("Projeto não encontrado.")
        st.session_state.projeto_view = "lista"
        st.rerun()
        return

    # Botão voltar
    col_back, col_status, _ = st.columns([1, 2, 3])
    with col_back:
        if st.button("← Voltar à Lista"):
            st.session_state.projeto_view = "lista"
            st.rerun()

    status = projeto.get("status", "rascunho")
    status_color = STATUS_COLORS.get(status, "#9E9E9E")
    status_label = STATUS_LABELS.get(status, status)

    st.markdown(
        f"### 📂 {projeto['nome']}  "
        f"<span style='background:{status_color};color:white;padding:3px 12px;"
        f"border-radius:12px;font-size:0.85rem;'>{status_label}</span>",
        unsafe_allow_html=True
    )

    # Informações rápidas
    col_i1, col_i2, col_i3, col_i4 = st.columns(4)
    with col_i1:
        st.metric("📋 Edital", projeto.get("edital_fonte") or "—")
    with col_i2:
        st.metric("📅 Prazo", _format_date(projeto.get("prazo_submissao")))
    with col_i3:
        st.metric("💰 Valor", _format_currency(projeto.get("valor_solicitado")))
    with col_i4:
        score = projeto.get("aderencia_score")
        st.metric("🎯 Aderência", f"{score:.0f}%" if score else "—")

    st.markdown("---")

    # Abas
    tab_info, tab_docs, tab_parceiros, tab_editar = st.tabs([
        "📋 Informações",
        "📁 Documentos",
        "🤝 Parceiros",
        "✏️ Editar Projeto"
    ])

    # ── Aba Informações ──
    with tab_info:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Nome do Edital:**")
            st.write(projeto.get("edital_nome") or "—")
            st.markdown("**URL do Edital:**")
            url = projeto.get("edital_url")
            if url:
                st.markdown(f"[🔗 Acessar edital]({url})")
            else:
                st.write("—")
            st.markdown("**Tipo de Arranjo:**")
            st.write(ARRANJO_LABELS.get(projeto.get("arranjo_tipo", "indefinido"), "—"))
        with col_b:
            st.markdown("**Descrição:**")
            st.write(projeto.get("descricao") or "—")
            st.markdown("**Notas Internas:**")
            st.write(projeto.get("notas") or "—")

        st.markdown("---")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.caption(f"📅 Criado em: {_format_date(projeto.get('created_at'))}")
            st.caption(f"👤 Criado por: {projeto.get('created_by') or '—'}")
        with col_c2:
            st.caption(f"🔄 Atualizado em: {_format_date(projeto.get('updated_at'))}")

        # Alterar status
        st.markdown("---")
        st.markdown("**Alterar Status do Projeto:**")
        col_st1, col_st2 = st.columns([2, 1])
        with col_st1:
            novo_status = st.selectbox(
                "Status",
                options=list(STATUS_LABELS.keys()),
                index=list(STATUS_LABELS.keys()).index(status),
                format_func=lambda x: STATUS_LABELS[x],
                label_visibility="collapsed"
            )
        with col_st2:
            if st.button("💾 Salvar Status", use_container_width=True):
                ok, msg = db_update_projeto(projeto_id, {"status": novo_status}, current_user["username"])
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    # ── Aba Documentos ──
    with tab_docs:
        _render_documentos(current_user, projeto_id)

    # ── Aba Parceiros ──
    with tab_parceiros:
        _render_parceiros(current_user, projeto_id)

    # ── Aba Editar ──
    with tab_editar:
        _render_editar_projeto(current_user, projeto)


# ─── Documentos ───────────────────────────────────────────────────────────────

def _render_documentos(current_user: dict, projeto_id: int):
    """Aba de upload e listagem de documentos do projeto."""

    st.markdown("### 📁 Documentos do Projeto")
    st.markdown("Faça upload de todos os documentos necessários para a submissão do edital.")

    # Upload
    with st.expander("📤 Enviar Novo Documento", expanded=True):
        col_u1, col_u2 = st.columns(2)
        with col_u1:
            uploaded_file = st.file_uploader(
                "Selecione o arquivo",
                type=["pdf", "docx", "doc", "xlsx", "xls", "jpg", "jpeg", "png", "txt", "zip"],
                help="Máximo 20MB por arquivo"
            )
        with col_u2:
            tipo_doc = st.selectbox(
                "Tipo de Documento",
                options=list(TIPO_DOC_LABELS.keys()),
                format_func=lambda x: TIPO_DOC_LABELS[x]
            )

        if uploaded_file and st.button("📤 Enviar Documento", type="primary"):
            conteudo = uploaded_file.read()
            mime = uploaded_file.type or "application/octet-stream"
            ok, msg, doc_id = db_upload_documento(
                projeto_id=projeto_id,
                nome_original=uploaded_file.name,
                conteudo=conteudo,
                tipo_documento=tipo_doc,
                mime_type=mime,
                uploaded_by=current_user["username"]
            )
            if ok:
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(f"❌ {msg}")

    # Listagem
    docs = db_list_documentos(projeto_id)

    if not docs:
        st.info("📭 Nenhum documento enviado ainda.")
        return

    st.markdown(f"**{len(docs)} documento(s) enviado(s)**")

    for doc in docs:
        tipo_label = TIPO_DOC_LABELS.get(doc.get("tipo_documento", "outro"), "📎 Outro")
        with st.container(border=True):
            col_d1, col_d2, col_d3 = st.columns([4, 2, 1])
            with col_d1:
                st.markdown(f"**{doc['nome_original']}**")
                st.caption(f"{tipo_label}  |  {_format_size(doc.get('tamanho_bytes'))}  |  Enviado por {doc.get('uploaded_by','—')} em {_format_date(doc.get('uploaded_at'))}")
            with col_d2:
                # Botão de download
                conteudo, nome = db_get_documento_conteudo(doc["id"])
                if conteudo:
                    st.download_button(
                        label="⬇️ Baixar",
                        data=conteudo,
                        file_name=nome or doc["nome_original"],
                        mime=doc.get("mime_type", "application/octet-stream"),
                        key=f"dl_{doc['id']}",
                        use_container_width=True
                    )
            with col_d3:
                if st.button("🗑️", key=f"deldoc_{doc['id']}", help="Remover documento"):
                    ok, msg = db_delete_documento(doc["id"], current_user["username"])
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


# ─── Parceiros ────────────────────────────────────────────────────────────────

def _render_parceiros(current_user: dict, projeto_id: int):
    """Aba de parceiros do projeto."""

    st.markdown("### 🤝 Parceiros do Projeto")
    st.markdown("Registre os parceiros envolvidos ou prospectados para este projeto.")

    # Adicionar parceiro
    with st.expander("➕ Adicionar Parceiro", expanded=False):
        with st.form(f"form_parceiro_{projeto_id}", clear_on_submit=True):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p_nome = st.text_input("🏛️ Nome da Organização *", placeholder="Ex: EMBRAPA Soja")
                p_tipo = st.selectbox("Tipo", ["ICT", "empresa", "startup", "governo", "outro"])
                p_papel = st.text_input("Papel no Projeto", placeholder="Ex: Coexecutora, Parceira Técnica")
            with col_p2:
                p_contato = st.text_input("👤 Nome do Contato", placeholder="Ex: Dr. João Silva")
                p_email = st.text_input("✉️ E-mail do Contato", placeholder="joao@embrapa.br")
                p_status = st.selectbox("Status", ["prospecto", "negociando", "confirmado"])

            if st.form_submit_button("➕ Adicionar Parceiro", use_container_width=True):
                if not p_nome.strip():
                    st.error("❌ Nome da organização é obrigatório.")
                else:
                    ok, msg = db_add_parceiro(
                        projeto_id=projeto_id,
                        parceiro_nome=p_nome.strip(),
                        parceiro_tipo=p_tipo,
                        parceiro_papel=p_papel.strip(),
                        contato_nome=p_contato.strip(),
                        contato_email=p_email.strip(),
                        status=p_status
                    )
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

    # Listagem
    parceiros = db_list_parceiros(projeto_id)

    if not parceiros:
        st.info("📭 Nenhum parceiro cadastrado ainda.")
        return

    STATUS_P_LABELS = {
        "confirmado":  "✅ Confirmado",
        "negociando":  "🔄 Negociando",
        "prospecto":   "🔍 Prospecto",
    }
    STATUS_P_COLORS = {
        "confirmado": "#2E7D32",
        "negociando": "#F57C00",
        "prospecto":  "#1976D2",
    }

    for p in parceiros:
        p_status = p.get("status", "prospecto")
        p_color = STATUS_P_COLORS.get(p_status, "#9E9E9E")
        p_status_label = STATUS_P_LABELS.get(p_status, p_status)

        with st.container(border=True):
            col_pa, col_pb, col_pc = st.columns([4, 2, 1])
            with col_pa:
                st.markdown(
                    f"**{p['parceiro_nome']}** — {p.get('parceiro_tipo','').upper()}  "
                    f"<span style='background:{p_color};color:white;padding:2px 8px;"
                    f"border-radius:8px;font-size:0.75rem;'>{p_status_label}</span>",
                    unsafe_allow_html=True
                )
                if p.get("parceiro_papel"):
                    st.caption(f"Papel: {p['parceiro_papel']}")
                if p.get("contato_nome") or p.get("contato_email"):
                    st.caption(f"Contato: {p.get('contato_nome','')} — {p.get('contato_email','')}")
            with col_pc:
                if st.button("🗑️", key=f"delparc_{p['id']}", help="Remover parceiro"):
                    ok, msg = db_delete_parceiro(p["id"])
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)


# ─── Editar Projeto ───────────────────────────────────────────────────────────

def _render_editar_projeto(current_user: dict, projeto: dict):
    """Aba para editar informações do projeto."""

    st.markdown("### ✏️ Editar Projeto")

    with st.form(f"form_editar_{projeto['id']}", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            nome = st.text_input("🏷️ Nome do Projeto *", value=projeto.get("nome", ""))
            edital_nome = st.text_input("📋 Nome do Edital", value=projeto.get("edital_nome") or "")
            edital_fonte = st.text_input("🏛️ Fonte / Órgão", value=projeto.get("edital_fonte") or "")
            edital_url = st.text_input("🔗 URL do Edital", value=projeto.get("edital_url") or "")

        with col2:
            valor_atual = projeto.get("valor_solicitado")
            valor_str = st.text_input(
                "💰 Valor Solicitado (R$)",
                value=str(int(float(valor_atual))) if valor_atual else ""
            )
            prazo_atual = projeto.get("prazo_submissao")
            if prazo_atual and isinstance(prazo_atual, str):
                try:
                    prazo_atual = datetime.strptime(prazo_atual[:10], "%Y-%m-%d").date()
                except Exception:
                    prazo_atual = None
            prazo_input = st.date_input("📅 Prazo de Submissão", value=prazo_atual)

            arranjo_keys = list(ARRANJO_LABELS.keys())
            arranjo_atual = projeto.get("arranjo_tipo", "indefinido")
            arranjo_idx = arranjo_keys.index(arranjo_atual) if arranjo_atual in arranjo_keys else 0
            arranjo_tipo = st.selectbox(
                "🤝 Tipo de Arranjo",
                options=arranjo_keys,
                index=arranjo_idx,
                format_func=lambda x: ARRANJO_LABELS[x]
            )

            score_atual = projeto.get("aderencia_score")
            aderencia = st.number_input(
                "🎯 Score de Aderência (%)",
                min_value=0.0, max_value=100.0,
                value=float(score_atual) if score_atual else 0.0,
                step=1.0
            )

        descricao = st.text_area("📝 Descrição", value=projeto.get("descricao") or "", height=100)
        notas = st.text_area("🗒️ Notas Internas", value=projeto.get("notas") or "", height=80)

        if st.form_submit_button("💾 Salvar Alterações", use_container_width=True, type="primary"):
            if not nome.strip():
                st.error("❌ O nome do projeto é obrigatório.")
            else:
                valor = None
                if valor_str.strip():
                    try:
                        valor = float(valor_str.replace("R$", "").replace(".", "").replace(",", ".").strip())
                    except ValueError:
                        st.error("❌ Valor inválido.")
                        st.stop()

                fields = {
                    "nome": nome.strip(),
                    "descricao": descricao.strip(),
                    "edital_nome": edital_nome.strip(),
                    "edital_url": edital_url.strip(),
                    "edital_fonte": edital_fonte.strip(),
                    "valor_solicitado": valor,
                    "prazo_submissao": prazo_input,
                    "arranjo_tipo": arranjo_tipo,
                    "aderencia_score": aderencia if aderencia > 0 else None,
                    "notas": notas.strip(),
                }
                ok, msg = db_update_projeto(projeto["id"], fields, current_user["username"])
                if ok:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
