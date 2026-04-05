import pdfplumber
import json
from openai import OpenAI
import os
from typing import Dict, List, Any

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from PDF file using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        raise Exception(f"Erro ao extrair PDF: {str(e)}")
    return text

def analyze_edital_with_ai(pdf_text: str) -> Dict[str, Any]:
    """
    Use OpenAI to analyze edital and extract structured information.
    """
    prompt = f"""
    Analise o seguinte edital da FINEP e extraia as informações estruturadas em JSON:
    
    {pdf_text[:4000]}  # Limit to first 4000 chars to avoid token limits
    
    Retorne um JSON com a seguinte estrutura:
    {{
        "titulo": "Título do edital",
        "objetivo": "Objetivo geral",
        "orcamento_total": "Valor total em reais",
        "linhas_tematicas": ["linha 1", "linha 2", ...],
        "requisitos_elegibilidade": ["requisito 1", "requisito 2", ...],
        "valor_minimo": "Valor mínimo por projeto",
        "valor_maximo": "Valor máximo por projeto",
        "contrapartida_minima": "Percentual mínimo de contrapartida",
        "trl_minimo": "TRL mínimo exigido",
        "trl_maximo": "TRL máximo exigido",
        "prazo_encerramento": "Data de encerramento",
        "criterios_avaliacao": ["critério 1", "critério 2", ...]
    }}
    
    Responda APENAS com o JSON válido, sem explicações adicionais.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500
        )
        
        response_text = response.choices[0].message.content
        # Try to parse JSON
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, return structured error
            return {
                "erro": "Não foi possível extrair dados estruturados",
                "texto_bruto": response_text
            }
    except Exception as e:
        raise Exception(f"Erro ao analisar edital com IA: {str(e)}")

def evaluate_company_adherence(company_profile: Dict, edital_data: Dict) -> Dict[str, Any]:
    """
    Evaluate company adherence to edital requirements using AI.
    Returns binary criteria results and graduated scores.
    """
    
    prompt = f"""
    Você é um especialista em editais FINEP. Avalie a aderência de uma empresa a um edital.
    
    PERFIL DA EMPRESA:
    {json.dumps(company_profile, ensure_ascii=False, indent=2)}
    
    DADOS DO EDITAL:
    {json.dumps(edital_data, ensure_ascii=False, indent=2)}
    
    Retorne uma avaliação em JSON com a seguinte estrutura:
    {{
        "criterios_binarios": {{
            "natureza_juridica_elegivel": {{"passou": true/false, "mensagem": "..."}},
            "porte_elegivel": {{"passou": true/false, "mensagem": "..."}},
            "cnpj_ativo": {{"passou": true/false, "mensagem": "..."}},
            "nao_impedido": {{"passou": true/false, "mensagem": "..."}},
            "alinhamento_geografico": {{"passou": true/false, "mensagem": "..."}}
        }},
        "criterios_graduais": {{
            "aderencia_tematica": {{"nota": 1-10, "justificativa": "..."}},
            "maturidade_trl": {{"nota": 1-10, "justificativa": "..."}},
            "capacidade_tecnica": {{"nota": 1-10, "justificativa": "..."}},
            "historico_pd": {{"nota": 1-10, "justificativa": "..."}},
            "contrapartida": {{"nota": 1-10, "justificativa": "..."}},
            "impacto_escalabilidade": {{"nota": 1-10, "justificativa": "..."}},
            "alinhamento_geografico_preferencial": {{"nota": 1-10, "justificativa": "..."}}
        }},
        "recomendacao_geral": "Recomendação final"
    }}
    
    Responda APENAS com o JSON válido.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content
        return json.loads(response_text)
    except Exception as e:
        raise Exception(f"Erro ao avaliar aderência: {str(e)}")

def generate_proposal_draft(company_profile: Dict, edital_data: Dict, project_idea: str) -> Dict[str, str]:
    """
    Generate proposal draft sections using AI.
    """
    
    prompt = f"""
    Você é um especialista em redação de propostas para editais FINEP. 
    Gere rascunhos das seções de uma proposta baseado nos dados fornecidos.
    
    PERFIL DA EMPRESA:
    {json.dumps(company_profile, ensure_ascii=False, indent=2)}
    
    DADOS DO EDITAL:
    {json.dumps(edital_data, ensure_ascii=False, indent=2)}
    
    IDEIA DO PROJETO:
    {project_idea}
    
    Retorne um JSON com as seguintes seções (cada uma com 150-300 palavras):
    {{
        "resumo_executivo": "...",
        "problema_oportunidade": "...",
        "objetivo_geral": "...",
        "objetivos_especificos": "...",
        "metodologia": "...",
        "plano_trabalho": "...",
        "equipe_necessaria": "...",
        "resultados_esperados": "...",
        "indicadores_sucesso": "...",
        "impacto_economico_social": "..."
    }}
    
    Responda APENAS com o JSON válido.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3000
        )
        
        response_text = response.choices[0].message.content
        return json.loads(response_text)
    except Exception as e:
        raise Exception(f"Erro ao gerar proposta: {str(e)}")

def calculate_weighted_score(graduated_scores: Dict[str, Dict]) -> float:
    """
    Calculate weighted average of graduated criteria.
    
    Weights:
    - Aderência temática: 25%
    - Maturidade TRL: 20%
    - Capacidade técnica: 15%
    - Histórico P&D: 15%
    - Contrapartida: 10%
    - Impacto: 10%
    - Alinhamento geográfico: 5%
    """
    weights = {
        "aderencia_tematica": 0.25,
        "maturidade_trl": 0.20,
        "capacidade_tecnica": 0.15,
        "historico_pd": 0.15,
        "contrapartida": 0.10,
        "impacto_escalabilidade": 0.10,
        "alinhamento_geografico_preferencial": 0.05
    }
    
    total_score = 0
    for criterion, weight in weights.items():
        if criterion in graduated_scores:
            score = graduated_scores[criterion].get("nota", 5)
            total_score += score * weight
    
    return round(total_score, 2)

def get_score_classification(score: float) -> tuple[str, str]:
    """
    Classify score and return recommendation.
    """
    if score <= 3:
        return "Baixa Aderência", "Não recomendado submeter sem ajustes significativos"
    elif score <= 6:
        return "Aderência Moderada", "Submissão possível com atenção aos pontos fracos"
    elif score <= 9:
        return "Boa Aderência", "Recomendado prosseguir com a proposta"
    else:
        return "Aderência Excelente", "Excelente alinhamento com o edital"
