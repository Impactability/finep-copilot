"""
Run Weekly Report - Orquestrador do Relatório Semanal
Executa: busca de editais → análise de aderência → envio de e-mail
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Injetar chave do ambiente
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("❌ OPENAI_API_KEY não configurada!")
    sys.exit(1)

from edital_hunter import run_edital_hunt, save_results
from email_reporter import gerar_e_enviar_relatorio

def main():
    print("\n" + "="*60)
    print("🚀 FINEP COPILOT - RELATÓRIO SEMANAL DE EDITAIS")
    print("   Agnest Farm Lab Edition")
    print(f"   {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("="*60)

    # 1. Buscar editais
    print("\n📡 FASE 1: Buscando editais em fontes nacionais e internacionais...")
    editais = run_edital_hunt()

    if not editais:
        print("\n⚠️  Nenhum edital encontrado. Enviando e-mail de aviso...")
        from email_reporter import enviar_email
        html_vazio = """
        <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:40px 20px;text-align:center;">
            <h2 style="color:#2E7D32;">🌾 FINEP Copilot - Relatório Semanal</h2>
            <p>Nenhum edital novo foi encontrado esta semana nas fontes monitoradas.</p>
            <p style="color:#888;font-size:13px;">Próxima busca: próxima segunda-feira às 8h</p>
        </div>
        """
        enviar_email(html_vazio, "FINEP Copilot · Sem novos editais esta semana")
        return

    # 2. Salvar resultados
    print("\n💾 FASE 2: Salvando resultados...")
    json_path = save_results(editais)

    # 3. Enviar e-mail
    print("\n📧 FASE 3: Gerando e enviando relatório por e-mail...")
    sucesso = gerar_e_enviar_relatorio(editais=editais)

    # 4. Resumo final
    alta = [e for e in editais if e.get("score_aderencia", 0) >= 7]
    media = [e for e in editais if 4 <= e.get("score_aderencia", 0) < 7]
    baixa = [e for e in editais if e.get("score_aderencia", 0) < 4]

    print("\n" + "="*60)
    print("📊 RESUMO FINAL")
    print("="*60)
    print(f"  Total de editais analisados: {len(editais)}")
    print(f"  🟢 Alta Aderência (≥7):      {len(alta)}")
    print(f"  🟡 Aderência Moderada (4-6): {len(media)}")
    print(f"  🔴 Baixa Aderência (<4):     {len(baixa)}")
    print(f"  📧 E-mail enviado:           {'✅ Sim' if sucesso else '❌ Falhou'}")
    print(f"  💾 Resultados salvos em:     {json_path}")
    print("="*60)

    if alta:
        print("\n🏆 TOP EDITAIS (Alta Aderência):")
        for i, e in enumerate(alta[:5], 1):
            print(f"  {i}. [{e.get('score_aderencia',0)}/10] {e.get('titulo','')[:60]}...")
            print(f"     📍 {e.get('fonte','')} · {e.get('pais','')}")
            print(f"     🎯 {e.get('acao_recomendada','')}")

if __name__ == "__main__":
    main()
