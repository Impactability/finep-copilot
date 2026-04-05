"""
Edital Hunter - Agente de Busca Proativa de Editais
Busca editais nacionais e internacionais relevantes para a Agnest Farm Lab
"""

import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Any
from openai import OpenAI
import time
from ai_client import get_ai_client

# Initialize AI client (Gemini ou OpenAI)
client, AI_MODEL = get_ai_client()

# ─── Perfil da Agnest Farm Lab ────────────────────────────────────────────────
AGNEST_PROFILE = {
    "nome": "Agnest Farm Lab",
    "tipo": "Hub de Inovação Aberta - Agricultura Digital e Sustentável",
    "localizacao": "Jaguariúna, SP, Brasil",
    "parceiros_principais": ["EMBRAPA", "Banco do Brasil"],
    "verticais": [
        "Inteligência Artificial para Agro",
        "IoT (Internet das Coisas)",
        "Robótica e Automação Agrícola",
        "Software para suporte e tomada de decisão",
        "Sistemas de produção sustentáveis",
        "Bioinsumos",
        "Sensoriamento remoto",
        "Manejo integrado de pragas e doenças"
    ],
    "palavras_chave": [
        "agtech", "agro", "agricultura digital", "agricultura sustentável",
        "bioinsumos", "precision agriculture", "smart farming", "food tech",
        "agronegócio", "inovação agrícola", "sensoriamento", "IoT agro",
        "sustainable agriculture", "agroecology", "food security",
        "digital farming", "agri-food", "crop protection", "soil health",
        "water management", "climate smart agriculture"
    ],
    "trl_habitual": "4-7",
    "porte": "Pequena/Média Empresa",
    "foco_geografico": "Brasil + Internacional"
}

# ─── Fontes de Editais ────────────────────────────────────────────────────────
FONTES = {
    "nacionais": [
        {
            "nome": "FINEP - Chamadas Públicas",
            "url": "https://www.finep.gov.br/chamadas-publicas",
            "tipo": "subvenção",
            "pais": "Brasil"
        },
        {
            "nome": "BNDES - Chamadas",
            "url": "https://www.bndes.gov.br/wps/portal/site/home/financiamento/chamadas-publicas",
            "tipo": "financiamento",
            "pais": "Brasil"
        },
        {
            "nome": "CNPq - Chamadas",
            "url": "https://www.gov.br/cnpq/pt-br/acesso-a-informacao/acoes-e-programas/chamadas",
            "tipo": "pesquisa",
            "pais": "Brasil"
        },
        {
            "nome": "EMBRAPA - Editais",
            "url": "https://www.embrapa.br/editais",
            "tipo": "pesquisa",
            "pais": "Brasil"
        },
        {
            "nome": "FAPESP - Oportunidades",
            "url": "https://fapesp.br/oportunidades",
            "tipo": "pesquisa",
            "pais": "Brasil"
        },
        {
            "nome": "MAPA - Chamadas",
            "url": "https://www.gov.br/agricultura/pt-br/assuntos/camaras-setoriais-tematicas/chamadas-publicas",
            "tipo": "agro",
            "pais": "Brasil"
        }
    ],
    "internacionais": [
        {
            "nome": "Horizon Europe - Open Calls",
            "url": "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/topic-search;callCode=null;freeTextSearchKeyword=agriculture;matchWholeText=true;typeCodes=1,0;statusCodes=31094501,31094502;programmePeriod=null;programCcm2Id=43108390;programDivisionCode=null;focusAreaCode=null;destination=null;mission=null;geographicalZonesCode=null;programmeDivisionProspect=null;startDateLte=null;startDateGte=null;crossCuttingPriorityCode=null;cpvCode=null;performanceOfDelivery=null;sortQuery=sortStatus;orderBy=asc;onlyTenders=false;topicListKey=topicSearchTablePageState",
            "tipo": "pesquisa/inovação",
            "pais": "União Europeia"
        },
        {
            "nome": "EIC Accelerator - EU",
            "url": "https://eic.ec.europa.eu/eic-funding-opportunities/eic-accelerator_en",
            "tipo": "startup/inovação",
            "pais": "União Europeia"
        },
        {
            "nome": "LIFE Programme - EU",
            "url": "https://cinea.ec.europa.eu/programmes/life_en",
            "tipo": "meio ambiente/sustentabilidade",
            "pais": "União Europeia"
        },
        {
            "nome": "FAO - Grants",
            "url": "https://www.fao.org/partnerships/resource-mobilization/en/",
            "tipo": "alimentação/agro",
            "pais": "Internacional"
        },
        {
            "nome": "CGIAR - Opportunities",
            "url": "https://www.cgiar.org/",
            "tipo": "pesquisa agrícola",
            "pais": "Internacional"
        },
        {
            "nome": "BID Lab - Calls",
            "url": "https://bidlab.org/en/calls",
            "tipo": "inovação",
            "pais": "América Latina"
        }
    ]
}

# ─── Funções de Busca ─────────────────────────────────────────────────────────

def fetch_page(url: str, timeout: int = 15) -> str:
    """Busca conteúdo de uma página web."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; AgNestBot/1.0; +https://agnestfarmlab.com)"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"ERRO: {str(e)}"

def extract_text_from_html(html: str, max_chars: int = 5000) -> str:
    """Extrai texto limpo de HTML."""
    try:
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 20]
        return "\n".join(lines)[:max_chars]
    except Exception:
        return html[:max_chars]

def search_editais_with_ai(fonte: Dict, page_text: str) -> List[Dict]:
    """
    Usa IA para identificar editais relevantes para a Agnest Farm Lab
    a partir do texto de uma página.
    """
    prompt = f"""
Você é um especialista em captação de recursos para inovação em agronegócio.

Analise o conteúdo abaixo da fonte "{fonte['nome']}" ({fonte['pais']}) e identifique 
editais, chamadas públicas ou oportunidades de financiamento relevantes para:

PERFIL DA ORGANIZAÇÃO:
- Nome: Agnest Farm Lab
- Foco: Agricultura Digital e Sustentável
- Verticais: IA, IoT, Robótica, Bioinsumos, Sensoriamento, Sustentabilidade
- Parceiros: EMBRAPA, Banco do Brasil
- Localização: Brasil (mas aceita internacionais)

CONTEÚDO DA PÁGINA:
{page_text}

Retorne um JSON com lista de editais encontrados (pode ser vazia se não houver nada relevante):
{{
  "editais": [
    {{
      "titulo": "Nome do edital",
      "descricao": "Descrição em 2-3 frases",
      "prazo": "Data de encerramento ou 'Não informado'",
      "valor_estimado": "Valor disponível ou 'Não informado'",
      "url": "Link direto se disponível",
      "tipo": "subvenção | financiamento | pesquisa | prêmio | outro",
      "pais": "{fonte['pais']}",
      "fonte": "{fonte['nome']}",
      "relevancia_agro": "alta | media | baixa",
      "palavras_chave_identificadas": ["palavra1", "palavra2"]
    }}
  ]
}}

Inclua APENAS editais com relevância alta ou média para agro/sustentabilidade/inovação.
Responda APENAS com JSON válido.
"""
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2000
        )
        text = response.choices[0].message.content.strip()
        # Remove markdown code blocks if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text).get("editais", [])
    except Exception as e:
        print(f"  ⚠️  Erro ao analisar com IA: {e}")
        return []

def score_edital_for_agnest(edital: Dict) -> Dict:
    """
    Calcula score de aderência do edital ao perfil da Agnest Farm Lab.
    """
    prompt = f"""
Avalie a aderência deste edital ao perfil da Agnest Farm Lab e retorne um JSON de scoring.

EDITAL:
{json.dumps(edital, ensure_ascii=False, indent=2)}

PERFIL AGNEST FARM LAB:
- Hub de inovação aberta para agricultura digital e sustentável
- Verticais: IA, IoT, Robótica, Bioinsumos, Sensoriamento remoto, Sustentabilidade
- Parceiros ICT: EMBRAPA
- Localização: Jaguariúna/SP - Brasil
- Pode participar como proponente, coexecutora ou gestora operacional
- Infraestrutura de testes em ambiente real (Farm Lab)

Retorne JSON:
{{
  "score_aderencia": 0-10,
  "classificacao": "Alta Aderência | Aderência Moderada | Baixa Aderência",
  "cor": "verde | amarelo | vermelho",
  "pode_entrar_sozinha": true/false,
  "precisa_parceiro": true/false,
  "tipo_parceiro_necessario": "ICT | empresa | consórcio | não precisa",
  "pontos_fortes": ["ponto 1", "ponto 2"],
  "gaps": ["gap 1", "gap 2"],
  "acao_recomendada": "Submeter imediatamente | Buscar parceiro e submeter | Monitorar | Não recomendado",
  "justificativa": "Explicação em 2-3 frases"
}}

Responda APENAS com JSON válido.
"""
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        scoring = json.loads(text)
        return {**edital, **scoring}
    except Exception as e:
        print(f"  ⚠️  Erro ao calcular score: {e}")
        return {**edital, "score_aderencia": 5, "classificacao": "Aderência Moderada", "cor": "amarelo"}

def run_edital_hunt() -> List[Dict]:
    """
    Executa busca completa de editais em todas as fontes.
    Retorna lista de editais com scores de aderência.
    """
    print("\n🔍 Iniciando busca proativa de editais...")
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 60)

    all_editais = []
    todas_fontes = FONTES["nacionais"] + FONTES["internacionais"]

    for fonte in todas_fontes:
        print(f"\n📡 Buscando: {fonte['nome']} ({fonte['pais']})...")

        html = fetch_page(fonte["url"])
        if html.startswith("ERRO"):
            print(f"  ❌ {html}")
            continue

        page_text = extract_text_from_html(html)
        if len(page_text) < 100:
            print(f"  ⚠️  Conteúdo insuficiente extraído")
            continue

        editais = search_editais_with_ai(fonte, page_text)
        print(f"  ✅ {len(editais)} edital(is) identificado(s)")

        for edital in editais:
            scored = score_edital_for_agnest(edital)
            all_editais.append(scored)
            time.sleep(0.5)  # Rate limiting

    # Sort by score
    all_editais.sort(key=lambda x: x.get("score_aderencia", 0), reverse=True)

    print(f"\n✅ Busca concluída! {len(all_editais)} editais encontrados e analisados.")
    return all_editais

def save_results(editais: List[Dict], filepath: str = "/home/ubuntu/finep_copilot/editais_encontrados.json"):
    """Salva resultados em arquivo JSON."""
    data = {
        "data_busca": datetime.now().isoformat(),
        "total_editais": len(editais),
        "perfil_agnest": AGNEST_PROFILE,
        "editais": editais
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Resultados salvos em: {filepath}")
    return filepath

def run_edital_hunt_from_db() -> List[Dict]:
    """
    Variánte que usa as fontes do banco de dados persistente (fontes_db.json)
    em vez das fontes hardcoded. Permite que o usuário adicione/remova fontes.
    """
    try:
        from fontes_manager import get_fontes_ativas
        fontes_ativas = get_fontes_ativas()
    except ImportError:
        print("⚠️  fontes_manager não disponível, usando fontes padrão")
        return run_edital_hunt()

    if not fontes_ativas:
        print("⚠️  Nenhuma fonte ativa no banco. Usando fontes padrão.")
        return run_edital_hunt()

    print(f"🔍 Iniciando busca proativa de editais (banco de dados)...")
    print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"📊 Fontes ativas: {len(fontes_ativas)}")
    print("=" * 60)

    all_editais = []

    for fonte_db in fontes_ativas:
        fonte = {
            "nome": fonte_db["nome"],
            "url": fonte_db["url"],
            "tipo": fonte_db.get("tipo", "outro"),
            "pais": fonte_db.get("pais", "Brasil")
        }
        print(f"\n📡 Buscando: {fonte['nome']} ({fonte['pais']})...")

        html = fetch_page(fonte["url"])
        if html.startswith("ERRO"):
            print(f"  ❌ {html}")
            continue

        page_text = extract_text_from_html(html)
        if len(page_text) < 100:
            print(f"  ⚠️  Conteúdo insuficiente extraído")
            continue

        editais = search_editais_with_ai(fonte, page_text)
        print(f"  ✅ {len(editais)} edital(is) identificado(s)")

        for edital in editais:
            scored = score_edital_for_agnest(edital)
            all_editais.append(scored)
            time.sleep(0.3)

    all_editais.sort(key=lambda x: x.get("score_aderencia", 0), reverse=True)
    print(f"\n✅ Busca concluída! {len(all_editais)} editais encontrados e analisados.")
    return all_editais


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    editais = run_edital_hunt()
    save_results(editais)
    print(f"\n📊 Resumo:")
    alta = [e for e in editais if e.get("score_aderencia", 0) >= 7]
    media = [e for e in editais if 4 <= e.get("score_aderencia", 0) < 7]
    baixa = [e for e in editais if e.get("score_aderencia", 0) < 4]
    print(f"  🟢 Alta Aderência: {len(alta)}")
    print(f"  🟡 Aderência Moderada: {len(media)}")
    print(f"  🔴 Baixa Aderência: {len(baixa)}")
