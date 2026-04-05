"""
Auth Manager - Sistema de Autenticação Segura
Gerencia usuários, senhas (bcrypt), sessões e permissões admin.
Banco de dados em users_db.json (nunca exposto no repositório).
"""

import os
import json
import bcrypt
from datetime import datetime
from typing import Optional, Dict, List

# Caminho do banco de usuários
USERS_DB_PATH = os.path.join(os.path.dirname(__file__), "users_db.json")

# ─── Usuário padrão inicial ───────────────────────────────────────────────────
DEFAULT_ADMIN = {
    "username": "leo",
    "name": "Leonardo",
    "email": "leo@impactability.com.br",
    "role": "admin",
    "created_at": datetime.now().isoformat(),
    "created_by": "system"
}
DEFAULT_PASSWORD = "Agnest@2026"


def _hash_password(password: str) -> str:
    """Gera hash bcrypt seguro da senha."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    """Verifica senha contra hash bcrypt."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def _load_users() -> Dict:
    """Carrega banco de usuários do arquivo JSON."""
    if not os.path.exists(USERS_DB_PATH):
        return _init_users_db()
    try:
        with open(USERS_DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return _init_users_db()


def _save_users(data: Dict) -> None:
    """Salva banco de usuários no arquivo JSON."""
    with open(USERS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _init_users_db() -> Dict:
    """Inicializa banco de usuários com o admin padrão."""
    data = {
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "users": {
            DEFAULT_ADMIN["username"]: {
                **DEFAULT_ADMIN,
                "password_hash": _hash_password(DEFAULT_PASSWORD)
            }
        }
    }
    _save_users(data)
    return data


# ─── API Pública ──────────────────────────────────────────────────────────────

def authenticate(username: str, password: str) -> Optional[Dict]:
    """
    Autentica usuário. Retorna dados do usuário se válido, None se inválido.
    """
    data = _load_users()
    username = username.strip().lower()
    user = data["users"].get(username)
    if not user:
        return None
    if not _verify_password(password, user["password_hash"]):
        return None
    return {
        "username": user["username"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"]
    }


def create_user(
    username: str,
    name: str,
    email: str,
    password: str,
    role: str = "admin",
    created_by: str = "admin"
) -> tuple:
    """
    Cria novo usuário. Retorna (True, mensagem) ou (False, erro).
    """
    data = _load_users()
    username = username.strip().lower()

    if not username or not name or not password:
        return False, "Username, nome e senha são obrigatórios."

    if len(username) < 3:
        return False, "Username deve ter pelo menos 3 caracteres."

    if len(password) < 6:
        return False, "Senha deve ter pelo menos 6 caracteres."

    if username in data["users"]:
        return False, f"Username '{username}' já existe."

    # Verificar email duplicado
    for u in data["users"].values():
        if u.get("email", "").lower() == email.lower():
            return False, f"E-mail '{email}' já está em uso."

    data["users"][username] = {
        "username": username,
        "name": name,
        "email": email,
        "role": role,
        "password_hash": _hash_password(password),
        "created_at": datetime.now().isoformat(),
        "created_by": created_by
    }
    _save_users(data)
    return True, f"Usuário '{name}' criado com sucesso!"


def update_password(username: str, new_password: str) -> tuple:
    """Atualiza senha de um usuário."""
    data = _load_users()
    username = username.strip().lower()

    if username not in data["users"]:
        return False, "Usuário não encontrado."

    if len(new_password) < 6:
        return False, "Senha deve ter pelo menos 6 caracteres."

    data["users"][username]["password_hash"] = _hash_password(new_password)
    data["users"][username]["updated_at"] = datetime.now().isoformat()
    _save_users(data)
    return True, "Senha atualizada com sucesso!"


def delete_user(username: str, requesting_user: str) -> tuple:
    """Remove um usuário (não pode remover a si mesmo)."""
    data = _load_users()
    username = username.strip().lower()

    if username == requesting_user:
        return False, "Você não pode remover sua própria conta."

    if username not in data["users"]:
        return False, "Usuário não encontrado."

    # Garantir que sempre exista pelo menos 1 admin
    admins = [u for u in data["users"].values() if u["role"] == "admin"]
    if len(admins) <= 1 and data["users"][username]["role"] == "admin":
        return False, "Não é possível remover o último administrador."

    del data["users"][username]
    _save_users(data)
    return True, f"Usuário '{username}' removido com sucesso."


def list_users() -> List[Dict]:
    """Lista todos os usuários (sem expor hashes de senha)."""
    data = _load_users()
    users = []
    for u in data["users"].values():
        users.append({
            "username": u["username"],
            "name": u["name"],
            "email": u.get("email", ""),
            "role": u["role"],
            "created_at": u.get("created_at", ""),
            "created_by": u.get("created_by", "system")
        })
    return sorted(users, key=lambda x: x["created_at"])


def get_user_count() -> int:
    """Retorna total de usuários cadastrados."""
    data = _load_users()
    return len(data["users"])


def ensure_db_exists():
    """Garante que o banco de usuários existe (cria se necessário)."""
    if not os.path.exists(USERS_DB_PATH):
        _init_users_db()
