"""
AI Client - Módulo centralizado de configuração do cliente de IA
Suporta: Gemini 2.5 Flash (padrão) e GPT-4.1-mini (fallback)

Configuração via Streamlit secrets ou variáveis de ambiente:
  - GEMINI_API_KEY  → usa Google Gemini via API compatível com OpenAI
  - OPENAI_API_KEY  → usa OpenAI diretamente (fallback)
"""

import os
from openai import OpenAI

# ─── Modelos disponíveis ──────────────────────────────────────────────────────
MODEL_GEMINI = "gemini-2.5-flash"
MODEL_OPENAI = "gpt-4.1-mini"

# Base URL para Gemini via API compatível com OpenAI (Google AI Studio)
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# Chave Gemini padrão (pode ser sobrescrita por secrets do Streamlit ou env)
DEFAULT_GEMINI_KEY = "AIzaSyCxHvak48hdforY28CTkkpt9kyR3cTlWik"

def get_ai_client() -> tuple:
    """
    Retorna (client, model_name) configurado com base nas chaves disponíveis.
    Prioridade: GEMINI_API_KEY (secrets/env) > chave padrão Gemini > OPENAI_API_KEY
    """
    # Tentar ler secrets do Streamlit primeiro
    gemini_key = None
    openai_key = None

    try:
        import streamlit as st
        gemini_key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("gemini_api_key")
        openai_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("openai_api_key")
    except Exception:
        pass

    # Fallback para variáveis de ambiente
    if not gemini_key:
        gemini_key = os.getenv("GEMINI_API_KEY")
    if not openai_key:
        openai_key = os.getenv("OPENAI_API_KEY")

    # Fallback para chave padrão Gemini
    if not gemini_key:
        gemini_key = DEFAULT_GEMINI_KEY

    # Prioridade 1: Gemini
    if gemini_key:
        client = OpenAI(
            api_key=gemini_key,
            base_url=GEMINI_BASE_URL
        )
        return client, MODEL_GEMINI

    # Prioridade 2: OpenAI (com base_url do ambiente se disponível)
    if openai_key:
        # Verificar se há base_url customizada (ambiente Manus)
        base_url = os.getenv("OPENAI_BASE_URL")
        if base_url:
            client = OpenAI(api_key=openai_key, base_url=base_url)
        else:
            client = OpenAI(api_key=openai_key)
        return client, MODEL_OPENAI

    raise ValueError(
        "Nenhuma chave de IA configurada. "
        "Adicione GEMINI_API_KEY ou OPENAI_API_KEY nos secrets do Streamlit."
    )

def get_model_name() -> str:
    """Retorna apenas o nome do modelo ativo."""
    _, model = get_ai_client()
    return model

def get_model_label() -> str:
    """Retorna label amigável do modelo ativo."""
    _, model = get_ai_client()
    if "gemini" in model:
        return f"🤖 Google Gemini ({model})"
    return f"🤖 OpenAI ({model})"
