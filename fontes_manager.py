"""
Fontes Manager - Gerenciador de Fontes de Editais
Gerencia banco de dados de fontes, verifica status e descobre novas fontes automaticamente
"""

import os
import json
import requests
import hashlib
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
from openai import OpenAI
import time
from ai_client import get_ai_client

# Initialize AI client (Gemini ou OpenAI)
client, AI_MODEL = get_ai_client()

FONTES_DB_PATH = os.path.join(os.path.dirname(__file__), "fontes_db.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; AgNestCopilot/2.0; +https://agnestfarmlab.com)"
}

# ─── CRUD de Fontes ───────────────────────────────────────────────────────────

def carregar_fontes() -> Dict:
    """Carrega banco de dados de fontes do arquivo JSON."""
    if not os.path.exists(FONTES_DB_PATH):
        return {"ultima_atualizacao": datetime.now().isoformat(), "total_fontes": 0, "fontes": []}
    with open(FONTES_DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_fontes(db: Dict):
    """Salva banco de dados de fontes no arquivo JSON."""
    db["ultima_atualizacao"] = datetime.now().isoformat()
    db["total_fontes"] = len(db.get("fontes", []))
    with open(FONTES_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def gerar_id(nome: str, url: str) -> str:
    """Gera ID único para uma fonte."""
    raw = f"{nome}{url}".lower().replace(" ", "_")
    return hashlib.md5(raw.encode()).hexdigest()[:12]

def adicionar_fonte(nome: str, url: str, tipo: str, pais: str, categoria: str,
                    descricao: str = "", adicionado_por: str = "usuario") -> Dict:
    """Adiciona nova fonte ao banco de dados."""
    db = carregar_fontes()
    
    # Verificar duplicata por URL
    for f in db["fontes"]:
        if f["url"].rstrip("/") == url.rstrip("/"):
            return {"sucesso": False, "mensagem": f"Fonte já existe: {f['nome']}"}
    
    nova_fonte = {
        "id": gerar_id(nome, url),
        "nome": nome,
        "url": url,
        "tipo": tipo,
        "pais": pais,
        "categoria": categoria,
        "ativo": True,
        "adicionado_por": adicionado_por,
        "data_adicao": datetime.now().strftime("%Y-%m-%d"),
        "ultima_verificacao": None,
        "edital_ativo": None,
        "total_editais_encontrados": 0,
        "descricao": descricao
    }
    
    db["fontes"].append(nova_fonte)
    salvar_fontes(db)
    return {"sucesso": True, "mensagem": f"Fonte '{nome}' adicionada com sucesso!", "fonte": nova_fonte}

def remover_fonte(fonte_id: str) -> Dict:
    """Remove uma fonte pelo ID."""
    db = carregar_fontes()
    original = len(db["fontes"])
    db["fontes"] = [f for f in db["fontes"] if f["id"] != fonte_id]
    if len(db["fontes"]) < original:
        salvar_fontes(db)
        return {"sucesso": True, "mensagem": "Fonte removida com sucesso."}
    return {"sucesso": False, "mensagem": "Fonte não encontrada."}

def toggle_fonte(fonte_id: str) -> Dict:
    """Ativa ou desativa uma fonte."""
    db = carregar_fontes()
    for f in db["fontes"]:
        if f["id"] == fonte_id:
            f["ativo"] = not f["ativo"]
            salvar_fontes(db)
            status = "ativada" if f["ativo"] else "desativada"
            return {"sucesso": True, "mensagem": f"Fonte {status}.", "ativo": f["ativo"]}
    return {"sucesso": False, "mensagem": "Fonte não encontrada."}

def get_fontes_ativas() -> List[Dict]:
    """Retorna apenas fontes ativas."""
    db = carregar_fontes()
    return [f for f in db.get("fontes", []) if f.get("ativo", True)]

# ─── Verificação de Status ────────────────────────────────────────────────────

def verificar_status_fonte(fonte: Dict) -> Dict:
    """
    Verifica se uma fonte está acessível e se tem edital ativo.
    Retorna fonte atualizada com status.
    """
    url = fonte["url"]
    resultado = {
        **fonte,
        "ultima_verificacao": datetime.now().isoformat(),
        "edital_ativo": False,
        "status_http": None,
        "erro": None
    }
    
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12, verify=False)
        resultado["status_http"] = resp.status_code
        
        if resp.status_code != 200:
            resultado["erro"] = f"HTTP {resp.status_code}"
            return resultado
        
        # Extrair texto da página
        soup = BeautifulSoup(resp.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        texto = soup.get_text(separator=" ", strip=True)[:4000]
        
        # Verificar com IA se há edital ativo
        prompt = f"""
Analise este texto de uma página web de editais/chamadas públicas e determine:
1. Há algum edital, chamada pública ou oportunidade de financiamento ABERTA (com prazo futuro)?
2. Há menção a datas futuras, prazos abertos ou inscrições abertas?

Texto: {texto[:2000]}

Responda APENAS com JSON:
{{"edital_ativo": true/false, "quantidade_editais": 0, "resumo": "uma frase descrevendo o que foi encontrado"}}
"""
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200
        )
        text_resp = response.choices[0].message.content.strip()
        if text_resp.startswith("```"):
            text_resp = text_resp.split("```")[1]
            if text_resp.startswith("json"):
                text_resp = text_resp[4:]
        
        analise = json.loads(text_resp)
        resultado["edital_ativo"] = analise.get("edital_ativo", False)
        resultado["quantidade_editais_ativos"] = analise.get("quantidade_editais", 0)
        resultado["resumo_status"] = analise.get("resumo", "")
        
    except requests.exceptions.SSLError:
        # Tentar sem verificação SSL
        try:
            resp = requests.get(url, headers=HEADERS, timeout=12, verify=False)
            resultado["status_http"] = resp.status_code
            resultado["edital_ativo"] = resp.status_code == 200
            resultado["erro"] = "SSL ignorado"
        except Exception as e2:
            resultado["erro"] = f"SSL Error: {str(e2)[:50]}"
    except json.JSONDecodeError:
        resultado["edital_ativo"] = True  # Assume ativo se não conseguiu parsear
        resultado["erro"] = "Erro ao parsear resposta IA"
    except Exception as e:
        resultado["erro"] = str(e)[:80]
    
    return resultado

def verificar_todas_fontes(apenas_ativas: bool = True) -> List[Dict]:
    """Verifica status de todas as fontes e atualiza o banco de dados."""
    db = carregar_fontes()
    fontes = [f for f in db["fontes"] if f.get("ativo", True)] if apenas_ativas else db["fontes"]
    
    atualizadas = []
    for i, fonte in enumerate(fontes):
        print(f"  [{i+1}/{len(fontes)}] Verificando: {fonte['nome']}...")
        fonte_atualizada = verificar_status_fonte(fonte)
        atualizadas.append(fonte_atualizada)
        
        # Atualizar no banco
        for j, f in enumerate(db["fontes"]):
            if f["id"] == fonte["id"]:
                db["fontes"][j] = fonte_atualizada
                break
        
        time.sleep(0.5)
    
    salvar_fontes(db)
    return atualizadas

# ─── Descoberta Automática de Novas Fontes ────────────────────────────────────

QUERIES_DESCOBERTA = [
    "editais abertos agronegócio inovação 2026 Brasil",
    "chamadas públicas agricultura sustentável financiamento 2026",
    "grants agtech precision agriculture 2026 open call",
    "Horizon Europe agriculture sustainability open calls 2026",
    "funding opportunities smart farming food security 2026",
    "editais bioinsumos agricultura digital FINEP CNPq 2026",
    "European Green Deal agriculture funding 2026",
    "USDA grants agtech innovation 2026",
    "FAO funding opportunities agriculture 2026",
    "editais inovação agropecuária fundações estaduais 2026"
]

def descobrir_novas_fontes() -> List[Dict]:
    """
    Usa buscas web para descobrir novas fontes de editais relevantes.
    Retorna lista de novas fontes sugeridas.
    """
    print("\n🔎 Iniciando descoberta automática de novas fontes...")
    
    db = carregar_fontes()
    urls_existentes = {f["url"].rstrip("/") for f in db["fontes"]}
    
    novas_fontes_sugeridas = []
    
    # Usar IA para sugerir fontes baseado no conhecimento
    prompt = f"""
Você é um especialista em captação de recursos para agronegócio e inovação.

Liste 15 fontes de editais/chamadas públicas que NÃO estão na lista abaixo, 
relevantes para uma empresa de agricultura digital e sustentável no Brasil 
(como a Agnest Farm Lab - hub de inovação agro com EMBRAPA).

FONTES JÁ CADASTRADAS (não repetir):
{json.dumps([f['nome'] + ' - ' + f['url'] for f in db['fontes']], ensure_ascii=False)}

Inclua:
- Fundações estaduais brasileiras (FAPERJ, FAPEMIG, FAPERGS, etc.)
- Programas privados (Bunge, Cargill, Syngenta, John Deere Foundation, etc.)
- Organismos internacionais (IFAD, GEF, Green Climate Fund, etc.)
- Aceleradoras e fundos de impacto (Raízen, Embrapa Ventures, etc.)
- Programas europeus específicos (PRIMA, EIT Food, etc.)

Retorne JSON:
{{
  "fontes": [
    {{
      "nome": "Nome descritivo da fonte",
      "url": "https://url-oficial.com/pagina-de-editais",
      "tipo": "subvenção | financiamento | pesquisa | prêmio | aceleração | outro",
      "pais": "Brasil | União Europeia | Internacional | América Latina | etc",
      "categoria": "nacional | internacional | privado",
      "descricao": "Uma frase descrevendo a fonte",
      "relevancia_agro": "alta | media",
      "justificativa": "Por que é relevante para a Agnest"
    }}
  ]
}}

Responda APENAS com JSON válido. Inclua apenas URLs que você tem certeza que existem.
"""
    
    try:
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=3000
        )
        text = response.choices[0].message.content.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        
        sugestoes = json.loads(text).get("fontes", [])
        
        for s in sugestoes:
            url_norm = s.get("url", "").rstrip("/")
            if url_norm and url_norm not in urls_existentes:
                novas_fontes_sugeridas.append({
                    **s,
                    "id": gerar_id(s.get("nome", ""), s.get("url", "")),
                    "ativo": False,  # Inativo por padrão — usuário aprova
                    "adicionado_por": "agente_ia",
                    "data_adicao": datetime.now().strftime("%Y-%m-%d"),
                    "ultima_verificacao": None,
                    "edital_ativo": None,
                    "total_editais_encontrados": 0,
                    "pendente_aprovacao": True  # Flag para aprovação do usuário
                })
                urls_existentes.add(url_norm)
        
        print(f"  ✅ {len(novas_fontes_sugeridas)} novas fontes descobertas pelo agente")
        
    except Exception as e:
        print(f"  ⚠️  Erro na descoberta: {e}")
    
    return novas_fontes_sugeridas

def aprovar_fonte_sugerida(fonte_id: str) -> Dict:
    """Aprova uma fonte sugerida pelo agente (ativa e remove flag de pendência)."""
    db = carregar_fontes()
    for f in db["fontes"]:
        if f["id"] == fonte_id:
            f["ativo"] = True
            f["pendente_aprovacao"] = False
            salvar_fontes(db)
            return {"sucesso": True, "mensagem": f"Fonte '{f['nome']}' aprovada e ativada!"}
    return {"sucesso": False, "mensagem": "Fonte não encontrada."}

def adicionar_fontes_sugeridas(fontes: List[Dict]):
    """Adiciona fontes sugeridas ao banco (como pendentes)."""
    db = carregar_fontes()
    ids_existentes = {f["id"] for f in db["fontes"]}
    adicionadas = 0
    for f in fontes:
        if f["id"] not in ids_existentes:
            db["fontes"].append(f)
            adicionadas += 1
    salvar_fontes(db)
    return adicionadas

def get_estatisticas() -> Dict:
    """Retorna estatísticas do banco de fontes."""
    db = carregar_fontes()
    fontes = db.get("fontes", [])
    return {
        "total": len(fontes),
        "ativas": len([f for f in fontes if f.get("ativo", True)]),
        "inativas": len([f for f in fontes if not f.get("ativo", True)]),
        "com_edital_ativo": len([f for f in fontes if f.get("edital_ativo") is True]),
        "sem_edital": len([f for f in fontes if f.get("edital_ativo") is False]),
        "nao_verificadas": len([f for f in fontes if f.get("ultima_verificacao") is None]),
        "pendentes_aprovacao": len([f for f in fontes if f.get("pendente_aprovacao", False)]),
        "nacionais": len([f for f in fontes if f.get("categoria") == "nacional"]),
        "internacionais": len([f for f in fontes if f.get("categoria") == "internacional"]),
        "privadas": len([f for f in fontes if f.get("categoria") == "privado"]),
        "ultima_atualizacao": db.get("ultima_atualizacao", "Nunca")
    }

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print("🔍 Verificando status de todas as fontes...")
    verificar_todas_fontes()
    print("\n🤖 Descobrindo novas fontes...")
    novas = descobrir_novas_fontes()
    if novas:
        n = adicionar_fontes_sugeridas(novas)
        print(f"✅ {n} novas fontes adicionadas como pendentes de aprovação")
    stats = get_estatisticas()
    print(f"\n📊 Estatísticas: {stats}")
