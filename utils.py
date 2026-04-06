import pdfplumber
import json
from openai import OpenAI
import os
import re
from typing import Dict, List, Any
from ai_client import get_ai_client

# Initialize AI client (Gemini ou OpenAI)
client, AI_MODEL = get_ai_client()

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

def clean_json_response(text: str) -> str:
    """
    Limpa a resposta da IA para garantir que seja um JSON válido.
    Remove blocos de código markdown e textos extras.
    """
    if not text:
        return ""
    
    # Remover blocos de código markdown (```json ... ``` ou ``` ...)
    text = re.sub(r'```(?:json)?\s*(.*?)\s*```', r'\1', text, flags=re.DOTALL)
    
    # Tentar encontrar o primeiro '{' e o último '}'
    start = text.find('{')
    end = text.rfind('}')
    
    if start != -1 and end != -1:
        return text[start:end+1]
    
    return text.strip()

def analyze_edital_with_ai(pdf_text: str) -> Dict[str, Any]:
    """
    Use AI to analyze edital and extract structured information.
    """
    prompt = f"""
    Analise o seguinte edital e extraia as informações estruturadas em JSON:
    
    {pdf_text[:6000]}  # Limit to first 6000 chars to avoid token limits
    
    Retorne um JSON com a seguinte estrutura EXATA:
    {{
        "titulo": "Título do edital",
        "objetivo": "Objetivo geral",
        "orcamento_total": "Valor total em reais",
        "linhas_tematicas": ["linha 1", "linha 2"],
        "requisitos_elegibilidade": ["requisito 1", "requisito 2"],
        "valor_minimo": "Valor mínimo por projeto",
        "valor_maximo": "Valor máximo por projeto",
        "contrapartida_minima": "Percentual mínimo de contrapartida",
        "trl_minimo": "TRL mínimo exigido",
        "trl_maximo": "TRL máximo exigido",
        "prazo_encerramento": "Data de encerramento",
        "criterios_avaliacao": ["critério 1", "critério 2"]
    }}
    
    Responda APENAS com o JSON válido, sem explicações adicionais.
    """
    
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1500
        )
        
        response_text = response.choices[0].message.content
        cleaned_text = clean_json_response(response_text)
        
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
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
    Você é um especialista em editais de inovação e fomento. Avalie a aderência de uma empresa a um edital.
    
    PERFIL DA EMPRESA:
    {json.dumps(company_profile, ensure_ascii=False, indent=2)}
    
    DADOS DO EDITAL:
    {json.dumps(edital_data, ensure_ascii=False, indent=2)}
    
    Retorne uma avaliação em JSON com a seguinte estrutura EXATA:
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
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content
        cleaned_text = clean_json_response(response_text)
        
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            # Tentar uma segunda vez com temperatura 0 se falhar
            response = client.chat.completions.create(
                model=AI_MODEL,
                messages=[{"role": "user", "content": prompt + "\nPOR FAVOR, RESPONDA APENAS O JSON PURO."}],
                temperature=0,
                max_tokens=2000
            )
            response_text = response.choices[0].message.content
            cleaned_text = clean_json_response(response_text)
            return json.loads(cleaned_text)
            
    except Exception as e:
        raise Exception(f"Erro ao avaliar aderência: {str(e)}")

def generate_proposal_draft(company_profile: Dict, edital_data: Dict, project_idea: str) -> Dict[str, str]:
    """
    Generate proposal draft sections using AI.
    """
    
    prompt = f"""
    Você é um especialista em redação de propostas para editais de inovação. 
    Gere rascunhos das seções de uma proposta baseado nos dados fornecidos.
    
    PERFIL DA EMPRESA:
    {json.dumps(company_profile, ensure_ascii=False, indent=2)}
    
    DADOS DO EDITAL:
    {json.dumps(edital_data, ensure_ascii=False, indent=2)}
    
    IDEIA DO PROJETO:
    {project_idea}
    
    Retorne um JSON com as seguintes seções EXATAS:
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
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3000
        )
        
        response_text = response.choices[0].message.content
        cleaned_text = clean_json_response(response_text)
        return json.loads(cleaned_text)
    except Exception as e:
        raise Exception(f"Erro ao gerar proposta: {str(e)}")

def calculate_weighted_score(graduated_scores: Dict[str, Dict]) -> float:
    """
    Calculate weighted average of graduated criteria.
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
    weight_sum = 0
    
    for criterion, weight in weights.items():
        if criterion in graduated_scores:
            score = graduated_scores[criterion].get("nota", 5)
            total_score += score * weight
            weight_sum += weight
    
    if weight_sum == 0:
        return 0.0
        
    return round(total_score / weight_sum, 2)

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
