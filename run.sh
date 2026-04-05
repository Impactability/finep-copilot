#!/bin/bash

# FINEP Copilot - Agnest Edition
# Script de inicialização

echo "🚀 Iniciando FINEP Copilot - Agnest Edition"
echo "=========================================="
echo ""

# Verificar se .env existe
if [ ! -f .env ]; then
    echo "⚠️  Arquivo .env não encontrado!"
    echo "Criando .env a partir de .env.example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANTE: Edite o arquivo .env e adicione sua chave OpenAI:"
    echo "   OPENAI_API_KEY=sk-..."
    echo ""
fi

# Verificar se OPENAI_API_KEY está configurada
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "❌ ERRO: Chave OpenAI não configurada!"
    echo "Edite o arquivo .env e adicione sua chave:"
    echo "   OPENAI_API_KEY=sk-..."
    exit 1
fi

echo "✅ Configuração validada"
echo ""
echo "🌐 Iniciando aplicação Streamlit..."
echo "📍 Acesse: http://localhost:8501"
echo ""
echo "Pressione Ctrl+C para parar a aplicação"
echo "=========================================="
echo ""

# Executar Streamlit
streamlit run app.py
