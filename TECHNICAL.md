# 📚 Documentação Técnica - FINEP Copilot

## 🏗️ Arquitetura do Sistema

### Componentes Principais

```
┌─────────────────────────────────────────────────────────┐
│                  STREAMLIT FRONTEND                      │
│  (Interface Web Interativa - app.py)                    │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ PDF Upload   │ │ Form Input   │ │ Session      │
│ Processing   │ │ Validation   │ │ Management   │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
        ┌───────────────▼───────────────┐
        │   UTILS MODULE (utils.py)     │
        │  ┌─────────────────────────┐  │
        │  │ PDF Text Extraction     │  │
        │  │ (pdfplumber)            │  │
        │  └─────────────────────────┘  │
        │  ┌─────────────────────────┐  │
        │  │ AI Analysis             │  │
        │  │ (OpenAI GPT-4.1-mini)   │  │
        │  └─────────────────────────┘  │
        │  ┌─────────────────────────┐  │
        │  │ Scoring & Evaluation    │  │
        │  └─────────────────────────┘  │
        └───────────────┬───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │  EXPORT MODULE (export_docx)  │
        │  ┌─────────────────────────┐  │
        │  │ Document Generation     │  │
        │  │ (python-docx)           │  │
        │  └─────────────────────────┘  │
        └───────────────┬───────────────┘
                        │
                        ▼
            ┌──────────────────────┐
            │  Word Documents      │
            │  (.docx files)       │
            └──────────────────────┘
```

## 📁 Estrutura de Arquivos

```
finep_copilot/
│
├── app.py                    # Aplicação principal Streamlit
│   ├── Seção 1: Início
│   ├── Seção 2: Dashboard
│   ├── Seção 3: Análise de Aderência
│   ├── Seção 4: Recomendador de Arranjos
│   ├── Seção 5: Banco de Parceiros
│   ├── Seção 6: Gerador de Proposta
│   └── Seção 7: Exportação
│
├── utils.py                  # Funções utilitárias
│   ├── extract_pdf_text()
│   ├── analyze_edital_with_ai()
│   ├── evaluate_company_adherence()
│   ├── generate_proposal_draft()
│   ├── calculate_weighted_score()
│   └── get_score_classification()
│
├── export_docx.py            # Geração de documentos
│   ├── create_diagnosis_document()
│   ├── create_proposal_document()
│   └── save_document()
│
├── requirements.txt          # Dependências Python
├── .env.example              # Template de variáveis
├── .gitignore                # Arquivos ignorados
├── run.sh                    # Script de inicialização
├── README.md                 # Documentação geral
├── QUICK_START.md            # Guia rápido
└── TECHNICAL.md              # Este arquivo
```

## 🔄 Fluxo de Dados

### 1. Upload e Análise de Edital

```
PDF Upload
    ↓
extract_pdf_text(pdf_path)
    ├─ Abre PDF com pdfplumber
    ├─ Extrai texto de todas as páginas
    └─ Retorna texto concatenado
    ↓
analyze_edital_with_ai(pdf_text)
    ├─ Cria prompt estruturado
    ├─ Envia para GPT-4.1-mini
    ├─ Recebe JSON estruturado
    └─ Retorna dados do edital
    ↓
Armazenado em st.session_state.edital_data
```

### 2. Análise de Aderência

```
Company Profile + Edital Data
    ↓
evaluate_company_adherence()
    ├─ Cria prompt de avaliação
    ├─ Inclui perfil da empresa
    ├─ Inclui dados do edital
    ├─ Envia para GPT-4.1-mini
    └─ Recebe avaliação estruturada
    ↓
Processa Critérios Binários
    ├─ Natureza jurídica
    ├─ Porte
    ├─ CNPJ
    ├─ Impedimentos
    └─ Alinhamento geográfico
    ↓
Processa Critérios Graduais (1-10)
    ├─ Aderência temática (25%)
    ├─ Maturidade TRL (20%)
    ├─ Capacidade técnica (15%)
    ├─ Histórico P&D (15%)
    ├─ Contrapartida (10%)
    ├─ Impacto (10%)
    └─ Alinhamento geográfico (5%)
    ↓
calculate_weighted_score()
    ├─ Aplica pesos
    ├─ Calcula média ponderada
    └─ Retorna score 0-10
    ↓
get_score_classification()
    ├─ Classifica (Baixa/Moderada/Boa/Excelente)
    └─ Retorna recomendação
    ↓
Armazenado em st.session_state.diagnosis_results
```

### 3. Geração de Proposta

```
Company Profile + Edital + Ideia do Projeto
    ↓
generate_proposal_draft()
    ├─ Cria prompt de geração
    ├─ Inclui contexto completo
    ├─ Envia para GPT-4.1-mini
    └─ Recebe 10 seções em JSON
    ↓
Seções Geradas:
    ├─ Resumo Executivo
    ├─ Problema e Oportunidade
    ├─ Objetivo Geral
    ├─ Objetivos Específicos
    ├─ Metodologia
    ├─ Plano de Trabalho
    ├─ Equipe Necessária
    ├─ Resultados Esperados
    ├─ Indicadores de Sucesso
    └─ Impacto Econômico e Social
    ↓
Usuário edita seções
    ↓
Armazenado em st.session_state.proposal_sections
```

### 4. Exportação de Documentos

```
Diagnosis Results
    ↓
create_diagnosis_document()
    ├─ Cria documento Word
    ├─ Adiciona metadata
    ├─ Insere critérios binários
    ├─ Insere gráfico radar
    ├─ Insere critérios graduais
    ├─ Insere recomendações
    └─ Retorna Document object
    ↓
save_document(doc, filename)
    ├─ Salva em /tmp/
    └─ Retorna caminho
    ↓
Streamlit download_button
    ├─ Lê arquivo
    ├─ Oferece download
    └─ Usuário baixa .docx
```

## 🤖 Integração com OpenAI

### Configuração

```python
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

### Chamadas à API

#### 1. Análise de Edital
```python
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3,  # Mais determinístico
    max_tokens=1500
)
```

#### 2. Avaliação de Aderência
```python
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.5,  # Balanceado
    max_tokens=2000
)
```

#### 3. Geração de Proposta
```python
response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7,  # Mais criativo
    max_tokens=3000
)
```

### Tratamento de Erros

```python
try:
    response = client.chat.completions.create(...)
    return json.loads(response.choices[0].message.content)
except json.JSONDecodeError:
    return {"erro": "JSON parsing failed"}
except Exception as e:
    raise Exception(f"API error: {str(e)}")
```

## 💾 Gerenciamento de Estado (Session State)

```python
st.session_state = {
    "edital_data": {
        "titulo": str,
        "objetivo": str,
        "orcamento_total": str,
        "linhas_tematicas": [str],
        "requisitos_elegibilidade": [str],
        ...
    },
    "company_profile": {
        "nome_empresa": str,
        "cnpj": str,
        "natureza_juridica": str,
        "porte": str,
        "estado_regiao": str,
        "area_atuacao": str,
        "descricao_tecnica": str,
        "historico_pd": str,
        "certificacoes": str,
        "contrapartida_percentual": int,
        "trl_habitual": int
    },
    "diagnosis_results": {
        "criterios_binarios": {...},
        "criterios_graduais": {...},
        "recomendacao_geral": str
    },
    "proposal_sections": {
        "resumo_executivo": str,
        "problema_oportunidade": str,
        ...
    },
    "partners_db": [
        {
            "Nome": str,
            "Tipo": str,
            "CNPJ/CPF": str,
            "Área": str,
            "Contato": str,
            "Email": str,
            "Descrição": str,
            "Data Adição": str
        }
    ]
}
```

## 📊 Critérios de Avaliação

### Pesos dos Critérios Graduais

```python
weights = {
    "aderencia_tematica": 0.25,           # 25%
    "maturidade_trl": 0.20,               # 20%
    "capacidade_tecnica": 0.15,           # 15%
    "historico_pd": 0.15,                 # 15%
    "contrapartida": 0.10,                # 10%
    "impacto_escalabilidade": 0.10,       # 10%
    "alinhamento_geografico_preferencial": 0.05  # 5%
}
```

### Cálculo de Score

```python
def calculate_weighted_score(graduated_scores):
    total_score = 0
    for criterion, weight in weights.items():
        if criterion in graduated_scores:
            score = graduated_scores[criterion].get("nota", 5)
            total_score += score * weight
    return round(total_score, 2)
```

### Classificação

```
Score 1-3:   Baixa Aderência
Score 4-6:   Aderência Moderada
Score 7-9:   Boa Aderência
Score 10:    Aderência Excelente
```

## 🔐 Segurança

### Variáveis de Ambiente

```bash
# .env (nunca commitar)
OPENAI_API_KEY=sk-...

# .env.example (commitar)
OPENAI_API_KEY=your_openai_api_key_here
```

### Tratamento de Dados Sensíveis

- Chaves armazenadas em variáveis de ambiente
- PDFs salvos temporariamente em `/tmp/`
- Sessão isolada por usuário
- Sem persistência de dados sensíveis

## 🧪 Testes

### Teste Manual

```bash
# 1. Instale dependências
pip install -r requirements.txt

# 2. Configure .env
cp .env.example .env
# Edite com sua chave

# 3. Execute
streamlit run app.py

# 4. Teste cada seção
```

### Casos de Teste

1. **Upload de Edital**
   - PDF válido → Sucesso
   - PDF corrompido → Erro tratado
   - Arquivo vazio → Erro tratado

2. **Análise de Aderência**
   - Todos critérios binários passam → Score calculado
   - Algum critério falha → Alerta exibido
   - Dados incompletos → Validação

3. **Geração de Proposta**
   - Ideia completa → Proposta gerada
   - Ideia vazia → Erro tratado
   - Edição de seções → Salva em session

4. **Exportação**
   - Diagnóstico → .docx gerado
   - Proposta → .docx gerado
   - Download → Funciona

## 📈 Performance

### Otimizações

- Uso de `@st.cache_data` para dados estáticos
- Lazy loading de seções
- Compressão de PDFs grandes
- Limite de tokens em chamadas API

### Limites

- Máximo 10MB para upload de PDF
- Máximo 4000 caracteres para análise inicial
- Timeout de 60s para API calls
- Máximo 3000 tokens para geração de proposta

## 🚀 Deployment

### Streamlit Cloud

1. Push para GitHub
2. Conectar repositório em streamlit.io/cloud
3. Configurar variáveis de ambiente
4. Deploy automático

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

### Variáveis de Ambiente (Production)

```bash
OPENAI_API_KEY=sk-...
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_PORT=8501
```

## 📝 Logs e Debugging

### Ativar Modo Debug

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Logs Importantes

- Extração de PDF
- Chamadas à API OpenAI
- Erros de validação
- Exportação de documentos

## 🔄 Roadmap de Evolução

### v2.0 (Atual)
- ✅ Análise de editais
- ✅ Avaliação de aderência
- ✅ Recomendador de arranjos
- ✅ Banco de parceiros
- ✅ Geração de proposta
- ✅ Exportação em Word

### v3.0 (Próxima)
- 📋 Assistente de preenchimento de documentos
- 🔍 Extração de campos obrigatórios
- 🤖 Preenchimento inteligente
- ✅ Validação de completude
- 📤 Integração com plataforma FINEP

### v4.0 (Futura)
- 📊 Dashboard de acompanhamento
- 📧 Notificações de prazos
- 🔄 Sincronização com FINEP
- 📈 Análise de histórico

---

**Versão**: 2.0 - Agnest Edition  
**Última Atualização**: Abril 2026
