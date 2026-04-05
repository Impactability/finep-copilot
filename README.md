# 🚀 FINEP Copilot - Agnest Edition

Assistente estratégico inteligente para captura de recursos em editais públicos da FINEP, desenvolvido especificamente para a **Agnest Farm Lab** e seu ecossistema de parceiros.

## 📋 Visão Geral

O FINEP Copilot é uma ferramenta web baseada em Streamlit que utiliza IA (GPT-4o) para analisar editais FINEP e fornecer recomendações estratégicas sobre:

- ✅ Aderência de projetos aos requisitos do edital
- 🤝 Recomendações de arranjos (simples vs. rede)
- 👥 Identificação de parceiros necessários
- 📝 Geração automática de rascunhos de propostas
- 📥 Exportação de documentos em Word

## 🎯 Funcionalidades Principais

### 1. Dashboard de Oportunidades
- Upload de múltiplos editais FINEP em PDF
- Análise automática de características principais
- Visualização estruturada de requisitos

### 2. Análise de Aderência
- Validação contra critérios binários (eliminatórios)
- Pontuação graduada em 7 critérios com pesos
- Gráfico radar interativo mostrando forças e fraquezas
- Recomendações específicas para melhoria

### 3. Recomendador de Arranjos
- Sugestão automática: Arranjo Simples vs. Rede
- Análise de limites de valor
- Identificação de parceiros necessários

### 4. Banco de Parceiros
- Registro de ICTs conhecidas (EMBRAPA, etc.)
- Cadastro de empresas e startups
- Histórico de relacionamentos

### 5. Gerador de Proposta
- Rascunho automático baseado no edital
- 10 seções estruturadas
- Editor integrado para customização

### 6. Exportação
- Diagnóstico completo em Word
- Proposta em Word
- Relatórios executivos

## 🛠️ Instalação

### Pré-requisitos
- Python 3.8+
- pip ou conda

### Passos

1. **Clone ou baixe o projeto:**
```bash
cd /home/ubuntu/finep_copilot
```

2. **Crie um ambiente virtual (opcional mas recomendado):**
```bash
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente:**
```bash
cp .env.example .env
# Edite .env e adicione sua chave OpenAI
# OPENAI_API_KEY=sk-...
```

5. **Execute a aplicação:**
```bash
streamlit run app.py
```

A aplicação abrirá em `http://localhost:8501`

## 📖 Como Usar

### Fluxo Básico

1. **Início**: Familiarize-se com a ferramenta e a Agnest Farm Lab
2. **Dashboard**: Faça upload de um edital FINEP em PDF
3. **Análise**: Preencha o perfil da sua empresa/iniciativa
4. **Aderência**: Execute a análise automática
5. **Arranjos**: Receba recomendações de estrutura
6. **Parceiros**: Consulte ou adicione parceiros
7. **Proposta**: Gere rascunho automático
8. **Exportação**: Baixe documentos em Word

### Exemplo de Uso

#### Passo 1: Upload do Edital
- Acesse "Dashboard de Oportunidades"
- Clique em "Faça upload de um edital FINEP"
- Selecione um PDF do edital
- Clique em "Analisar Edital"

#### Passo 2: Análise de Aderência
- Acesse "Análise de Aderência"
- Preencha o perfil da Agnest Farm Lab
- Descreva a capacidade técnica
- Clique em "Analisar Aderência"

#### Passo 3: Geração de Proposta
- Acesse "Gerador de Proposta"
- Descreva a ideia do projeto
- Clique em "Gerar Rascunho de Proposta"
- Edite as seções conforme necessário

#### Passo 4: Exportação
- Acesse "Exportar Resultados"
- Clique em "Baixar Diagnóstico" ou "Baixar Proposta"
- Abra o arquivo Word gerado

## 🏗️ Arquitetura

### Estrutura de Arquivos
```
finep_copilot/
├── app.py                 # Aplicação principal Streamlit
├── utils.py              # Funções utilitárias e IA
├── export_docx.py        # Geração de documentos Word
├── requirements.txt      # Dependências Python
├── .env.example          # Template de variáveis de ambiente
└── README.md             # Este arquivo
```

### Fluxo de Dados
```
PDF Upload → Extract Text → Analyze with GPT-4o → Store in Session
                                    ↓
                            Company Profile
                                    ↓
                        Evaluate Adherence with AI
                                    ↓
                        Generate Scores & Recommendations
                                    ↓
                        Export to Word Document
```

## 🤖 Integração com IA

### Modelos Utilizados
- **GPT-4.1-mini**: Análise de editais e avaliação de aderência
- **Temperatura**: 0.3-0.7 conforme a tarefa

### Prompts Principais

1. **Análise de Edital**: Extração estruturada de informações
2. **Avaliação de Aderência**: Critérios binários e graduais
3. **Geração de Proposta**: Rascunhos de 10 seções

## 📊 Critérios de Avaliação

### Critérios Binários (Eliminatórios)
- Natureza jurídica elegível
- Porte elegível
- CNPJ ativo e sem restrições
- Não estar em lista de impedidos
- Alinhamento geográfico obrigatório

### Critérios Graduais (Pontuação 1-10)
| Critério | Peso |
|----------|------|
| Aderência Temática | 25% |
| Maturidade TRL | 20% |
| Capacidade Técnica | 15% |
| Histórico P&D | 15% |
| Contrapartida | 10% |
| Impacto e Escalabilidade | 10% |
| Alinhamento Geográfico | 5% |

## 🔐 Segurança

- Chave OpenAI armazenada em variável de ambiente
- Arquivos temporários salvos em `/tmp`
- Sem armazenamento persistente de dados sensíveis
- Sessão do Streamlit isolada por usuário

## 📝 Configuração

### Variáveis de Ambiente

```bash
# Obrigatória
OPENAI_API_KEY=sk-...

# Opcional
OPENAI_API_BASE=https://api.openai.com/v1  # Padrão
```

## 🚀 Deployment

### Streamlit Cloud
```bash
# 1. Faça push para GitHub
git push origin main

# 2. Acesse https://streamlit.io/cloud
# 3. Conecte seu repositório
# 4. Configure as variáveis de ambiente
# 5. Deploy automático
```

### Docker
```bash
# Crie Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]

# Build e run
docker build -t finep-copilot .
docker run -p 8501:8501 -e OPENAI_API_KEY=sk-... finep-copilot
```

## 🐛 Troubleshooting

### Erro: "OPENAI_API_KEY not found"
- Verifique se o arquivo `.env` existe
- Confirme que a chave está correta
- Reinicie a aplicação

### Erro: "PDF extraction failed"
- Verifique se o PDF não está corrompido
- Tente um PDF diferente
- Confirme que é um PDF válido

### Erro: "AI analysis timeout"
- Verifique conexão com internet
- Tente novamente em alguns minutos
- Verifique se a chave OpenAI tem créditos

## 📞 Suporte

Para dúvidas sobre:
- **FINEP**: https://www.finep.gov.br
- **Agnest Farm Lab**: https://www.agnestfarmlab.com
- **EMBRAPA**: https://www.embrapa.br

## 📄 Licença

Desenvolvido para Agnest Farm Lab. Uso interno.

## 🙏 Agradecimentos

- EMBRAPA (parceiro institucional)
- FINEP (editais e regulamentações)
- Banco do Brasil (parceiro estratégico)
- Ecossistema AgNest

---

**Versão**: 2.0 - Agnest Edition  
**Última Atualização**: Abril 2026  
**Status**: Produção
