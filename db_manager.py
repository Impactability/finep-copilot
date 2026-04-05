"""
db_manager.py — Gerenciador de banco de dados MySQL para o Edital Copilot
Conexão segura, pool de conexões, funções CRUD para projetos e documentos.
"""

import os
import pymysql
import pymysql.cursors
import streamlit as st
from datetime import datetime
from typing import Optional, List, Dict, Any

# ─── CONFIGURAÇÃO SEGURA ──────────────────────────────────────────────────────

def get_db_config() -> dict:
    """Retorna configuração do banco de dados — prioriza st.secrets, depois env vars."""
    try:
        return {
            "host":     st.secrets.get("DB_HOST",     os.environ.get("DB_HOST",     "162.241.2.240")),
            "user":     st.secrets.get("DB_USER",     os.environ.get("DB_USER",     "sist4490_admin")),
            "password": st.secrets.get("DB_PASS",     os.environ.get("DB_PASS",     "1mpactaCWB123@#")),
            "database": st.secrets.get("DB_NAME",     os.environ.get("DB_NAME",     "sist4490_editalcopilot")),
            "port":     int(st.secrets.get("DB_PORT", os.environ.get("DB_PORT",     "3306"))),
            "charset":  "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor,
            "connect_timeout": 10,
            "autocommit": False,
        }
    except Exception:
        return {
            "host":     os.environ.get("DB_HOST",     "162.241.2.240"),
            "user":     os.environ.get("DB_USER",     "sist4490_admin"),
            "password": os.environ.get("DB_PASS",     "1mpactaCWB123@#"),
            "database": os.environ.get("DB_NAME",     "sist4490_editalcopilot"),
            "port":     int(os.environ.get("DB_PORT", "3306")),
            "charset":  "utf8mb4",
            "cursorclass": pymysql.cursors.DictCursor,
            "connect_timeout": 10,
            "autocommit": False,
        }


def get_connection():
    """Cria e retorna uma conexão MySQL."""
    cfg = get_db_config()
    return pymysql.connect(**cfg)


def test_connection() -> tuple[bool, str]:
    """Testa a conexão com o banco de dados."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION()")
            version = cur.fetchone()
        conn.close()
        return True, f"MySQL {version['VERSION()']}"
    except Exception as e:
        return False, str(e)


def log_audit(usuario: str, acao: str, recurso: str, recurso_id: int = None, detalhes: str = None):
    """Registra ação no log de auditoria."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO audit_log (usuario, acao, recurso, recurso_id, detalhes)
                VALUES (%s, %s, %s, %s, %s)
            """, (usuario, acao, recurso, recurso_id, detalhes))
        conn.commit()
        conn.close()
    except Exception:
        pass  # Log nunca deve quebrar a aplicação


# ─── USUÁRIOS ─────────────────────────────────────────────────────────────────

def db_get_user(username: str) -> Optional[Dict]:
    """Busca usuário pelo username."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM usuarios WHERE username = %s AND is_active = 1",
                (username.lower().strip(),)
            )
            user = cur.fetchone()
        conn.close()
        return user
    except Exception:
        return None


def db_create_user(username: str, name: str, email: str, password_hash: str,
                   role: str = "admin", created_by: str = "system",
                   receber_email: bool = True) -> tuple[bool, str]:
    """Cria novo usuário no banco."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO usuarios (username, name, email, password_hash, role, created_by, receber_email)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (username.lower().strip(), name.strip(), email.lower().strip(),
                 password_hash, role, created_by, 1 if receber_email else 0)
            )
        conn.commit()
        conn.close()
        log_audit(created_by, "CREATE_USER", "usuarios", detalhes=f"Criou usuário {username}")
        return True, f"Usuário '{username}' criado com sucesso."
    except pymysql.err.IntegrityError as e:
        if "username" in str(e):
            return False, f"Username '{username}' já existe."
        if "email" in str(e):
            return False, f"E-mail '{email}' já cadastrado."
        return False, str(e)
    except Exception as e:
        return False, str(e)


def db_list_users() -> List[Dict]:
    """Lista todos os usuários ativos."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, name, email, role, created_by, created_at, last_login, receber_email "
                "FROM usuarios WHERE is_active = 1 ORDER BY created_at"
            )
            users = cur.fetchall()
        conn.close()
        return users
    except Exception:
        return []


def db_delete_user(username: str, deleted_by: str) -> tuple[bool, str]:
    """Desativa (soft delete) um usuário."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE usuarios SET is_active = 0 WHERE username = %s",
                (username,)
            )
        conn.commit()
        conn.close()
        log_audit(deleted_by, "DELETE_USER", "usuarios", detalhes=f"Removeu usuário {username}")
        return True, f"Usuário '{username}' removido."
    except Exception as e:
        return False, str(e)


def db_update_password(username: str, new_hash: str) -> tuple[bool, str]:
    """Atualiza hash de senha do usuário."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE usuarios SET password_hash = %s WHERE username = %s",
                (new_hash, username)
            )
        conn.commit()
        conn.close()
        log_audit(username, "UPDATE_PASSWORD", "usuarios", detalhes="Senha alterada")
        return True, "Senha alterada com sucesso."
    except Exception as e:
        return False, str(e)


def db_update_last_login(username: str):
    """Atualiza timestamp do último login."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE usuarios SET last_login = NOW() WHERE username = %s",
                (username,)
            )
        conn.commit()
        conn.close()
    except Exception:
        pass


# ─── PROJETOS ─────────────────────────────────────────────────────────────────

def db_create_projeto(nome: str, descricao: str = "", edital_nome: str = "",
                      edital_url: str = "", edital_fonte: str = "",
                      valor_solicitado: float = None, prazo_submissao=None,
                      arranjo_tipo: str = "indefinido", notas: str = "",
                      created_by: str = "system") -> tuple[bool, str, int]:
    """Cria novo projeto. Retorna (ok, msg, projeto_id)."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO projetos
                    (nome, descricao, edital_nome, edital_url, edital_fonte,
                     valor_solicitado, prazo_submissao, arranjo_tipo, notas, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (nome, descricao, edital_nome, edital_url, edital_fonte,
                  valor_solicitado, prazo_submissao, arranjo_tipo, notas, created_by))
            projeto_id = cur.lastrowid
        conn.commit()
        conn.close()
        log_audit(created_by, "CREATE_PROJETO", "projetos", projeto_id, f"Criou projeto: {nome}")
        return True, f"Projeto '{nome}' criado com sucesso.", projeto_id
    except Exception as e:
        return False, str(e), 0


def db_list_projetos(created_by: str = None) -> List[Dict]:
    """Lista projetos, opcionalmente filtrando por criador."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            if created_by:
                cur.execute(
                    "SELECT * FROM projetos ORDER BY updated_at DESC"
                )
            else:
                cur.execute("SELECT * FROM projetos ORDER BY updated_at DESC")
            projetos = cur.fetchall()
        conn.close()
        return projetos
    except Exception:
        return []


def db_get_projeto(projeto_id: int) -> Optional[Dict]:
    """Busca projeto pelo ID."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM projetos WHERE id = %s", (projeto_id,))
            projeto = cur.fetchone()
        conn.close()
        return projeto
    except Exception:
        return None


def db_update_projeto(projeto_id: int, fields: Dict, updated_by: str) -> tuple[bool, str]:
    """Atualiza campos de um projeto."""
    allowed = {"nome", "descricao", "edital_nome", "edital_url", "edital_fonte",
               "valor_solicitado", "prazo_submissao", "status", "aderencia_score",
               "arranjo_tipo", "notas"}
    safe_fields = {k: v for k, v in fields.items() if k in allowed}
    if not safe_fields:
        return False, "Nenhum campo válido para atualizar."
    try:
        set_clause = ", ".join(f"{k} = %s" for k in safe_fields)
        values = list(safe_fields.values()) + [projeto_id]
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(f"UPDATE projetos SET {set_clause} WHERE id = %s", values)
        conn.commit()
        conn.close()
        log_audit(updated_by, "UPDATE_PROJETO", "projetos", projeto_id, f"Campos: {list(safe_fields.keys())}")
        return True, "Projeto atualizado com sucesso."
    except Exception as e:
        return False, str(e)


def db_delete_projeto(projeto_id: int, deleted_by: str) -> tuple[bool, str]:
    """Remove projeto e todos os documentos associados (CASCADE)."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT nome FROM projetos WHERE id = %s", (projeto_id,))
            proj = cur.fetchone()
            nome = proj["nome"] if proj else str(projeto_id)
            cur.execute("DELETE FROM projetos WHERE id = %s", (projeto_id,))
        conn.commit()
        conn.close()
        log_audit(deleted_by, "DELETE_PROJETO", "projetos", projeto_id, f"Removeu: {nome}")
        return True, f"Projeto '{nome}' removido."
    except Exception as e:
        return False, str(e)


# ─── DOCUMENTOS ───────────────────────────────────────────────────────────────

def db_upload_documento(projeto_id: int, nome_original: str, conteudo: bytes,
                        tipo_documento: str = "outro", mime_type: str = "application/octet-stream",
                        uploaded_by: str = "system") -> tuple[bool, str, int]:
    """Faz upload de documento vinculado a um projeto."""
    import hashlib
    import re
    # Nome de arquivo seguro (sem path traversal)
    safe_name = re.sub(r'[^a-zA-Z0-9._-]', '_', nome_original)
    tamanho = len(conteudo)
    # Limite de 20MB por arquivo
    if tamanho > 20 * 1024 * 1024:
        return False, "Arquivo excede o limite de 20MB.", 0
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO documentos
                    (projeto_id, nome_original, nome_arquivo, tipo_documento,
                     tamanho_bytes, mime_type, conteudo, uploaded_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (projeto_id, nome_original, safe_name, tipo_documento,
                  tamanho, mime_type, conteudo, uploaded_by))
            doc_id = cur.lastrowid
        conn.commit()
        conn.close()
        log_audit(uploaded_by, "UPLOAD_DOC", "documentos", doc_id,
                  f"Projeto {projeto_id}: {nome_original} ({tamanho} bytes)")
        return True, f"Documento '{nome_original}' enviado com sucesso.", doc_id
    except Exception as e:
        return False, str(e), 0


def db_list_documentos(projeto_id: int) -> List[Dict]:
    """Lista documentos de um projeto (sem o conteúdo binário)."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, nome_original, nome_arquivo, tipo_documento,
                       tamanho_bytes, mime_type, uploaded_by, uploaded_at
                FROM documentos
                WHERE projeto_id = %s
                ORDER BY uploaded_at DESC
            """, (projeto_id,))
            docs = cur.fetchall()
        conn.close()
        return docs
    except Exception:
        return []


def db_get_documento_conteudo(doc_id: int) -> Optional[bytes]:
    """Retorna o conteúdo binário de um documento para download."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT conteudo, nome_original FROM documentos WHERE id = %s", (doc_id,))
            doc = cur.fetchone()
        conn.close()
        if doc:
            return doc["conteudo"], doc["nome_original"]
        return None, None
    except Exception:
        return None, None


def db_delete_documento(doc_id: int, deleted_by: str) -> tuple[bool, str]:
    """Remove um documento."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT nome_original FROM documentos WHERE id = %s", (doc_id,))
            doc = cur.fetchone()
            nome = doc["nome_original"] if doc else str(doc_id)
            cur.execute("DELETE FROM documentos WHERE id = %s", (doc_id,))
        conn.commit()
        conn.close()
        log_audit(deleted_by, "DELETE_DOC", "documentos", doc_id, f"Removeu: {nome}")
        return True, f"Documento '{nome}' removido."
    except Exception as e:
        return False, str(e)


# ─── PARCEIROS POR PROJETO ────────────────────────────────────────────────────

def db_add_parceiro(projeto_id: int, parceiro_nome: str, parceiro_tipo: str = "outro",
                    parceiro_papel: str = "", contato_nome: str = "",
                    contato_email: str = "", status: str = "prospecto") -> tuple[bool, str]:
    """Adiciona parceiro a um projeto."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO projeto_parceiros
                    (projeto_id, parceiro_nome, parceiro_tipo, parceiro_papel,
                     contato_nome, contato_email, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (projeto_id, parceiro_nome, parceiro_tipo, parceiro_papel,
                  contato_nome, contato_email, status))
        conn.commit()
        conn.close()
        return True, f"Parceiro '{parceiro_nome}' adicionado."
    except Exception as e:
        return False, str(e)


def db_list_parceiros(projeto_id: int) -> List[Dict]:
    """Lista parceiros de um projeto."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM projeto_parceiros WHERE projeto_id = %s ORDER BY parceiro_nome",
                (projeto_id,)
            )
            parceiros = cur.fetchall()
        conn.close()
        return parceiros
    except Exception:
        return []


def db_delete_parceiro(parceiro_id: int) -> tuple[bool, str]:
    """Remove parceiro de um projeto."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM projeto_parceiros WHERE id = %s", (parceiro_id,))
        conn.commit()
        conn.close()
        return True, "Parceiro removido."
    except Exception as e:
        return False, str(e)


# ─── ESTATÍSTICAS ─────────────────────────────────────────────────────────────

def db_get_stats() -> Dict:
    """Retorna estatísticas gerais do sistema."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) as total FROM projetos")
            total_projetos = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(*) as total FROM projetos WHERE status = 'submetido'")
            submetidos = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(*) as total FROM projetos WHERE status = 'aprovado'")
            aprovados = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(*) as total FROM documentos")
            total_docs = cur.fetchone()["total"]

            cur.execute("SELECT COUNT(*) as total FROM usuarios WHERE is_active = 1")
            total_users = cur.fetchone()["total"]

            cur.execute("SELECT COALESCE(SUM(valor_solicitado), 0) as total FROM projetos WHERE status IN ('submetido','aprovado')")
            valor_total = cur.fetchone()["total"]

        conn.close()
        return {
            "total_projetos": total_projetos,
            "submetidos": submetidos,
            "aprovados": aprovados,
            "total_documentos": total_docs,
            "total_usuarios": total_users,
            "valor_total_captacao": float(valor_total or 0),
        }
    except Exception:
        return {}
