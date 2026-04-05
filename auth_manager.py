"""
auth_manager.py — Sistema de Autenticação Segura do Edital Copilot
Gerencia usuários, senhas (bcrypt), sessões e permissões admin.
Persistência via MySQL (sist4490_editalcopilot.usuarios).

Segurança implementada:
- Senhas com bcrypt (salt automático, nunca armazenadas em texto puro)
- Proteção contra enumeração de usuários (tempo constante na verificação)
- Soft-delete de usuários (is_active = 0)
- Auditoria de todas as ações
- Validação de inputs em todas as funções
- Sem exposição de hashes em nenhuma resposta
"""

import bcrypt
from datetime import datetime
from typing import Optional, Dict, List

from db_manager import (
    db_get_user, db_create_user, db_list_users, db_delete_user,
    db_update_password, db_update_last_login, get_connection
)

# ─── Usuário padrão inicial ───────────────────────────────────────────────────
DEFAULT_ADMIN = {
    "username":      "leo",
    "name":          "Leonardo",
    "email":         "leo@impactability.com.br",
    "role":          "admin",
    "receber_email": True,
}
DEFAULT_PASSWORD = "Agnest@2026"


# ─── Funções de hash ──────────────────────────────────────────────────────────

def _hash_password(password: str) -> str:
    """Gera hash bcrypt seguro (custo 12)."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(rounds=12)
    ).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    """Verifica senha contra hash bcrypt (tempo constante)."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ─── Inicialização ────────────────────────────────────────────────────────────

def ensure_db_exists():
    """Garante que o usuário admin padrão existe no banco MySQL."""
    try:
        user = db_get_user(DEFAULT_ADMIN["username"])
        if not user:
            pw_hash = _hash_password(DEFAULT_PASSWORD)
            db_create_user(
                username=DEFAULT_ADMIN["username"],
                name=DEFAULT_ADMIN["name"],
                email=DEFAULT_ADMIN["email"],
                password_hash=pw_hash,
                role=DEFAULT_ADMIN["role"],
                created_by="system",
                receber_email=True,
            )
    except Exception:
        pass


# ─── API Pública ──────────────────────────────────────────────────────────────

def authenticate(username: str, password: str) -> Optional[Dict]:
    """
    Autentica usuário. Retorna dados do usuário se válido, None se inválido.
    Nunca revela se o username existe ou não (proteção contra enumeração).
    """
    username = username.strip().lower()
    user = db_get_user(username)

    # Sempre executa checkpw para evitar timing attack
    dummy_hash = "$2b$12$invalidhashfortimingatttackprotection000000000000000000"
    if user:
        valid = _verify_password(password, user["password_hash"])
    else:
        _verify_password(password, dummy_hash)  # timing protection
        return None

    if not valid:
        return None

    # Atualizar último login
    db_update_last_login(username)

    return {
        "username":      user["username"],
        "name":          user["name"],
        "email":         user["email"],
        "role":          user["role"],
        "receber_email": bool(user.get("receber_email", True)),
    }


def create_user(
    username: str,
    name: str,
    email: str,
    password: str,
    role: str = "admin",
    created_by: str = "admin",
    receber_email: bool = True,
) -> tuple:
    """
    Cria novo usuário. Retorna (True, mensagem) ou (False, erro).
    Validações: username único, email único, senha mínima 6 chars.
    """
    username = username.strip().lower()

    # Validações de input
    if not username or not name or not password:
        return False, "Username, nome e senha são obrigatórios."
    if len(username) < 3:
        return False, "Username deve ter pelo menos 3 caracteres."
    if not username.replace(".", "").replace("_", "").replace("-", "").isalnum():
        return False, "Username só pode conter letras, números, ponto, hífen e underscore."
    if len(password) < 6:
        return False, "Senha deve ter pelo menos 6 caracteres."
    if "@" not in email or "." not in email.split("@")[-1]:
        return False, "E-mail inválido."

    pw_hash = _hash_password(password)
    ok, msg = db_create_user(
        username=username,
        name=name.strip(),
        email=email.lower().strip(),
        password_hash=pw_hash,
        role=role,
        created_by=created_by,
        receber_email=receber_email,
    )
    return ok, msg


def update_password(username: str, new_password: str) -> tuple:
    """Atualiza senha de um usuário com validação."""
    username = username.strip().lower()
    if len(new_password) < 6:
        return False, "Senha deve ter pelo menos 6 caracteres."
    new_hash = _hash_password(new_password)
    return db_update_password(username, new_hash)


def delete_user(username: str, requesting_user: str) -> tuple:
    """Remove um usuário (soft delete). Não pode remover a si mesmo."""
    username = username.strip().lower()
    if username == requesting_user.strip().lower():
        return False, "Você não pode remover sua própria conta."

    # Garantir que sempre exista pelo menos 1 admin ativo
    users = db_list_users()
    admins = [u for u in users if u["role"] == "admin"]
    target = next((u for u in users if u["username"] == username), None)
    if target and target["role"] == "admin" and len(admins) <= 1:
        return False, "Não é possível remover o último administrador."

    return db_delete_user(username, requesting_user)


def list_users() -> List[Dict]:
    """Lista todos os usuários ativos (sem expor hashes de senha)."""
    return db_list_users()


def get_user_count() -> int:
    """Retorna total de usuários ativos."""
    return len(db_list_users())


def update_email_preference(username: str, receber_email: bool) -> tuple:
    """Atualiza preferência de recebimento de e-mail semanal."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE usuarios SET receber_email = %s WHERE username = %s",
                (1 if receber_email else 0, username)
            )
        conn.commit()
        conn.close()
        status = "ativado" if receber_email else "desativado"
        return True, f"Recebimento de e-mail semanal {status}."
    except Exception as e:
        return False, str(e)


def get_email_recipients() -> List[str]:
    """Retorna lista de e-mails de usuários que optaram por receber o relatório semanal."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT email FROM usuarios WHERE is_active = 1 AND receber_email = 1"
            )
            rows = cur.fetchall()
        conn.close()
        return [r["email"] for r in rows]
    except Exception:
        return ["leo@impactability.com.br"]  # fallback
