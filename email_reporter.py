"""
Email Reporter - Gerador e Enviador de Relatório Semanal de Editais
Envia relatório HTML formatado para leo@impactability.com.br
"""

import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import List, Dict

# ─── Configurações de E-mail ──────────────────────────────────────────────────
EMAIL_REMETENTE = "contato@impactability.com.br"
EMAIL_SENHA_APP = "eqpg abwd xvja hwui"
EMAIL_DESTINATARIO = "leo@impactability.com.br"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

# ─── Gerador de HTML do E-mail ────────────────────────────────────────────────

def gerar_html_email(editais: List[Dict], data_busca: str) -> str:
    """Gera HTML rico e formatado para o e-mail semanal."""

    alta = [e for e in editais if e.get("score_aderencia", 0) >= 7]
    media = [e for e in editais if 4 <= e.get("score_aderencia", 0) < 7]
    baixa = [e for e in editais if e.get("score_aderencia", 0) < 4]

    data_fmt = datetime.now().strftime("%d/%m/%Y")
    semana = datetime.now().strftime("%V")

    def badge_cor(cor):
        cores = {
            "verde": "#2E7D32",
            "amarelo": "#F57F17",
            "vermelho": "#C62828"
        }
        return cores.get(cor, "#555")

    def card_edital(e, index):
        cor = badge_cor(e.get("cor", "amarelo"))
        score = e.get("score_aderencia", 0)
        pontos = "".join(f"<li style='margin:3px 0;color:#333;'>✅ {p}</li>" for p in e.get("pontos_fortes", [])[:3])
        gaps = "".join(f"<li style='margin:3px 0;color:#555;'>⚠️ {g}</li>" for g in e.get("gaps", [])[:2])
        url = e.get("url", "#")
        url_display = url[:60] + "..." if len(url) > 60 else url
        parceiro_tag = ""
        if e.get("precisa_parceiro"):
            parceiro_tag = f"""
            <span style="background:#FFF3E0;color:#E65100;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:bold;">
                🤝 Precisa de parceiro: {e.get('tipo_parceiro_necessario','ICT')}
            </span>"""
        else:
            parceiro_tag = """
            <span style="background:#E8F5E9;color:#1B5E20;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:bold;">
                ✅ Pode entrar sozinha
            </span>"""

        return f"""
        <div style="background:#fff;border:1px solid #e0e0e0;border-left:5px solid {cor};border-radius:8px;padding:20px;margin-bottom:16px;box-shadow:0 2px 4px rgba(0,0,0,0.05);">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;">
                <div style="flex:1;">
                    <span style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:1px;">{e.get('fonte','')}</span>
                    <h3 style="margin:4px 0 8px 0;color:#1a1a1a;font-size:16px;line-height:1.4;">{index}. {e.get('titulo','Sem título')}</h3>
                </div>
                <div style="text-align:right;">
                    <div style="background:{cor};color:#fff;padding:6px 14px;border-radius:20px;font-weight:bold;font-size:18px;display:inline-block;">{score}/10</div>
                    <div style="font-size:11px;color:{cor};font-weight:bold;margin-top:4px;">{e.get('classificacao','')}</div>
                </div>
            </div>

            <p style="color:#444;font-size:14px;line-height:1.6;margin:8px 0;">{e.get('descricao','')}</p>

            <div style="display:flex;gap:8px;flex-wrap:wrap;margin:10px 0;">
                <span style="background:#F3E5F5;color:#6A1B9A;padding:2px 8px;border-radius:12px;font-size:11px;">🌍 {e.get('pais','')}</span>
                <span style="background:#E3F2FD;color:#0D47A1;padding:2px 8px;border-radius:12px;font-size:11px;">📋 {e.get('tipo','')}</span>
                <span style="background:#FFF8E1;color:#F57F17;padding:2px 8px;border-radius:12px;font-size:11px;">📅 Prazo: {e.get('prazo','Não informado')}</span>
                <span style="background:#E8EAF6;color:#283593;padding:2px 8px;border-radius:12px;font-size:11px;">💰 {e.get('valor_estimado','Não informado')}</span>
                {parceiro_tag}
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0;">
                <div>
                    <p style="font-size:12px;font-weight:bold;color:#2E7D32;margin:0 0 4px 0;">PONTOS FORTES</p>
                    <ul style="margin:0;padding-left:16px;font-size:13px;">{pontos}</ul>
                </div>
                <div>
                    <p style="font-size:12px;font-weight:bold;color:#C62828;margin:0 0 4px 0;">GAPS / ATENÇÃO</p>
                    <ul style="margin:0;padding-left:16px;font-size:13px;">{gaps}</ul>
                </div>
            </div>

            <div style="background:#F5F5F5;border-radius:6px;padding:10px;margin:10px 0;">
                <p style="margin:0;font-size:13px;"><strong>🎯 Ação Recomendada:</strong> <span style="color:{cor};font-weight:bold;">{e.get('acao_recomendada','')}</span></p>
                <p style="margin:6px 0 0 0;font-size:13px;color:#555;">{e.get('justificativa','')}</p>
            </div>

            <a href="{url}" style="display:inline-block;background:{cor};color:#fff;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:bold;margin-top:8px;">
                🔗 Ver Edital Completo
            </a>
        </div>
        """

    # Gerar cards por categoria
    cards_alta = "".join(card_edital(e, i+1) for i, e in enumerate(alta))
    cards_media = "".join(card_edital(e, i+1) for i, e in enumerate(media))
    cards_baixa = "".join(card_edital(e, i+1) for i, e in enumerate(baixa[:3]))  # Máximo 3 de baixa

    secao_alta = f"""
    <div style="margin-bottom:32px;">
        <div style="background:#2E7D32;color:#fff;padding:12px 20px;border-radius:8px 8px 0 0;display:flex;align-items:center;gap:10px;">
            <span style="font-size:24px;">🟢</span>
            <div>
                <h2 style="margin:0;font-size:18px;">Alta Aderência — {len(alta)} edital(is)</h2>
                <p style="margin:2px 0 0 0;font-size:13px;opacity:0.9;">Score ≥ 7/10 · Ação imediata recomendada</p>
            </div>
        </div>
        <div style="border:1px solid #e0e0e0;border-top:none;border-radius:0 0 8px 8px;padding:16px;">
            {cards_alta if alta else '<p style="color:#888;text-align:center;padding:20px;">Nenhum edital com alta aderência encontrado esta semana.</p>'}
        </div>
    </div>
    """ if alta else ""

    secao_media = f"""
    <div style="margin-bottom:32px;">
        <div style="background:#F57F17;color:#fff;padding:12px 20px;border-radius:8px 8px 0 0;display:flex;align-items:center;gap:10px;">
            <span style="font-size:24px;">🟡</span>
            <div>
                <h2 style="margin:0;font-size:18px;">Aderência Moderada — {len(media)} edital(is)</h2>
                <p style="margin:2px 0 0 0;font-size:13px;opacity:0.9;">Score 4-6/10 · Avaliar com parceiros</p>
            </div>
        </div>
        <div style="border:1px solid #e0e0e0;border-top:none;border-radius:0 0 8px 8px;padding:16px;">
            {cards_media if media else '<p style="color:#888;text-align:center;padding:20px;">Nenhum edital com aderência moderada encontrado esta semana.</p>'}
        </div>
    </div>
    """ if media else ""

    secao_baixa = f"""
    <div style="margin-bottom:32px;">
        <div style="background:#757575;color:#fff;padding:12px 20px;border-radius:8px 8px 0 0;display:flex;align-items:center;gap:10px;">
            <span style="font-size:24px;">🔴</span>
            <div>
                <h2 style="margin:0;font-size:18px;">Baixa Aderência — {len(baixa)} edital(is)</h2>
                <p style="margin:2px 0 0 0;font-size:13px;opacity:0.9;">Score &lt; 4/10 · Para referência</p>
            </div>
        </div>
        <div style="border:1px solid #e0e0e0;border-top:none;border-radius:0 0 8px 8px;padding:16px;">
            {cards_baixa if baixa else '<p style="color:#888;text-align:center;padding:20px;">Nenhum edital com baixa aderência encontrado.</p>'}
        </div>
    </div>
    """ if baixa else ""

    html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FINEP Copilot - Relatório Semanal de Editais</title>
</head>
<body style="margin:0;padding:0;background:#F5F5F5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">

<!-- Header -->
<div style="background:linear-gradient(135deg,#1B5E20 0%,#2E7D32 50%,#388E3C 100%);padding:40px 20px;text-align:center;">
    <img src="https://www.agnestfarmlab.com/wp-content/uploads/2024/01/logo-agnest-white.png" alt="Agnest Farm Lab" style="height:50px;margin-bottom:16px;" onerror="this.style.display='none'">
    <h1 style="color:#fff;margin:0;font-size:28px;font-weight:800;letter-spacing:-0.5px;">🚀 FINEP Copilot</h1>
    <p style="color:#A5D6A7;margin:8px 0 0 0;font-size:16px;">Relatório Semanal de Editais · Semana {semana} · {data_fmt}</p>
</div>

<!-- Summary Bar -->
<div style="background:#fff;border-bottom:1px solid #e0e0e0;padding:0 20px;">
    <div style="max-width:700px;margin:0 auto;display:flex;justify-content:space-around;padding:20px 0;text-align:center;flex-wrap:wrap;gap:16px;">
        <div>
            <div style="font-size:36px;font-weight:800;color:#2E7D32;">{len(alta)}</div>
            <div style="font-size:13px;color:#555;">Alta Aderência</div>
        </div>
        <div style="width:1px;background:#e0e0e0;"></div>
        <div>
            <div style="font-size:36px;font-weight:800;color:#F57F17;">{len(media)}</div>
            <div style="font-size:13px;color:#555;">Aderência Moderada</div>
        </div>
        <div style="width:1px;background:#e0e0e0;"></div>
        <div>
            <div style="font-size:36px;font-weight:800;color:#757575;">{len(baixa)}</div>
            <div style="font-size:13px;color:#555;">Baixa Aderência</div>
        </div>
        <div style="width:1px;background:#e0e0e0;"></div>
        <div>
            <div style="font-size:36px;font-weight:800;color:#1565C0;">{len(editais)}</div>
            <div style="font-size:13px;color:#555;">Total Analisados</div>
        </div>
    </div>
</div>

<!-- Main Content -->
<div style="max-width:700px;margin:0 auto;padding:24px 16px;">

    <!-- Intro -->
    <div style="background:#E8F5E9;border:1px solid #A5D6A7;border-radius:8px;padding:16px;margin-bottom:24px;">
        <p style="margin:0;font-size:14px;color:#1B5E20;line-height:1.6;">
            <strong>🤖 Agnest Copilot</strong> realizou uma varredura completa em <strong>{FONTES_NOMES} fontes</strong> 
            (nacionais e internacionais) e identificou <strong>{len(editais)} editais</strong> com potencial relevância 
            para a Agnest Farm Lab. Os editais foram analisados e pontuados automaticamente com base no perfil 
            da Agnest, verticais temáticas e capacidade de participação.
        </p>
    </div>

    {secao_alta}
    {secao_media}
    {secao_baixa}

    <!-- CTA -->
    <div style="background:linear-gradient(135deg,#1B5E20,#2E7D32);border-radius:12px;padding:24px;text-align:center;margin-bottom:24px;">
        <h3 style="color:#fff;margin:0 0 8px 0;font-size:18px;">🎯 Quer analisar em detalhes?</h3>
        <p style="color:#A5D6A7;margin:0 0 16px 0;font-size:14px;">Acesse o FINEP Copilot para análise completa, geração de proposta e exportação de documentos.</p>
        <a href="https://agnestfarmlab.com" style="background:#fff;color:#2E7D32;padding:10px 24px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:14px;">
            🚀 Abrir FINEP Copilot
        </a>
    </div>

    <!-- Footer -->
    <div style="text-align:center;padding:16px 0;border-top:1px solid #e0e0e0;">
        <p style="color:#888;font-size:12px;margin:0;">
            Este relatório foi gerado automaticamente pelo <strong>FINEP Copilot - Agnest Edition</strong><br>
            Busca realizada em: {data_busca} · Próximo relatório: próxima segunda-feira às 8h<br><br>
            <a href="https://www.agnestfarmlab.com" style="color:#2E7D32;">Agnest Farm Lab</a> · 
            <a href="https://www.finep.gov.br" style="color:#2E7D32;">FINEP</a> · 
            <a href="https://www.embrapa.br" style="color:#2E7D32;">EMBRAPA</a>
        </p>
    </div>

</div>
</body>
</html>
"""
    return html

# Variável auxiliar para o template
FONTES_NOMES = 12  # Total de fontes rastreadas (int, não list)

def enviar_email(html_content: str, assunto: str = None) -> bool:
    """Envia o relatório por e-mail via SMTP."""
    if assunto is None:
        semana = datetime.now().strftime("%V")
        data = datetime.now().strftime("%d/%m/%Y")
        assunto = f"🌾 FINEP Copilot · Relatório Semanal de Editais · Semana {semana} ({data})"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = f"FINEP Copilot <{EMAIL_REMETENTE}>"
    msg["To"] = EMAIL_DESTINATARIO

    # Texto simples (fallback)
    texto_simples = f"""
FINEP Copilot - Relatório Semanal de Editais
Agnest Farm Lab Edition

Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Acesse o FINEP Copilot para visualizar o relatório completo com análise detalhada de aderência.

---
Agnest Farm Lab · https://www.agnestfarmlab.com
"""
    msg.attach(MIMEText(texto_simples, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(EMAIL_REMETENTE, EMAIL_SENHA_APP)
            server.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_string())
        print(f"✅ E-mail enviado com sucesso para {EMAIL_DESTINATARIO}")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")
        return False

def gerar_e_enviar_relatorio(editais: List[Dict] = None, json_path: str = None) -> bool:
    """
    Fluxo completo: carrega editais, gera HTML e envia e-mail.
    """
    # Carregar editais
    if editais is None and json_path:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        editais = data.get("editais", [])
        data_busca = data.get("data_busca", datetime.now().isoformat())
    elif editais is not None:
        data_busca = datetime.now().isoformat()
    else:
        print("❌ Nenhum dado de editais fornecido")
        return False

    data_busca_fmt = datetime.fromisoformat(data_busca).strftime("%d/%m/%Y %H:%M")

    print(f"\n📧 Gerando relatório com {len(editais)} editais...")
    html = gerar_html_email(editais, data_busca_fmt)

    print("📤 Enviando e-mail...")
    return enviar_email(html)

if __name__ == "__main__":
    import sys
    json_path = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/finep_copilot/editais_encontrados.json"
    if os.path.exists(json_path):
        gerar_e_enviar_relatorio(json_path=json_path)
    else:
        print(f"❌ Arquivo não encontrado: {json_path}")
        print("Execute primeiro: python3 edital_hunter.py")
