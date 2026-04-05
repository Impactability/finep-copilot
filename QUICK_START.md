# 🚀 Guia Rápido - FINEP Copilot

## ⚡ Início em 5 Minutos

### 1. Instalação e Configuração

```bash
# Navegue até o diretório do projeto
cd /home/ubuntu/finep_copilot

# Configure a chave OpenAI
nano .env
# Adicione: OPENAI_API_KEY=sk-seu-token-aqui

# Execute a aplicação
./run.sh
```

A aplicação abrirá em `http://localhost:8501`

### 2. Fluxo de Uso Básico

#### 📊 Passo 1: Carregar Edital
1. Acesse **"Dashboard de Oportunidades"**
2. Clique em **"Faça upload de um edital FINEP"**
3. Selecione o PDF do edital
4. Clique em **"Analisar Edital"**
5. Revise as informações extraídas

#### 🎯 Passo 2: Análise de Aderência
1. Acesse **"Análise de Aderência"**
2. Preencha o perfil da Agnest:
   - Nome: "Agnest Farm Lab"
   - Natureza: "Empresa Privada"
   - Porte: Conforme sua classificação
   - Área: "Agricultura Digital e Sustentável"
   - TRL: Selecione o nível de maturidade
   - Contrapartida: Informe capacidade
3. Descreva competências técnicas
4. Clique em **"Analisar Aderência"**
5. Analise os resultados:
   - ✅ Critérios binários (passa/não passa)
   - 📊 Gráfico radar com pontuações
   - 💡 Recomendações de melhoria

#### 🤝 Passo 3: Recomendações de Arranjo
1. Acesse **"Recomendador de Arranjos"**
2. Revise a recomendação automática
3. Escolha entre:
   - **Arranjo Simples**: Agnest + 1 ICT
   - **Arranjo em Rede**: Agnest + múltiplos parceiros
4. Identifique parceiros necessários

#### 👥 Passo 4: Gerenciar Parceiros
1. Acesse **"Banco de Parceiros"**
2. Adicione parceiros conhecidos:
   - EMBRAPA (ICT)
   - Startups do ecossistema
   - Empresas coexecutoras
3. Registre histórico de relacionamentos

#### 📝 Passo 5: Gerar Proposta
1. Acesse **"Gerador de Proposta"**
2. Descreva a ideia do projeto
3. Clique em **"Gerar Rascunho de Proposta"**
4. Edite cada seção conforme necessário
5. Customize para seu projeto

#### 📥 Passo 6: Exportar Documentos
1. Acesse **"Exportar Resultados"**
2. Baixe:
   - **Diagnóstico**: Análise completa de aderência
   - **Proposta**: Rascunho em Word
3. Abra em Microsoft Word ou LibreOffice
4. Finalize e revise antes de submeter

## 📋 Checklist de Uso

- [ ] Chave OpenAI configurada em .env
- [ ] Edital FINEP em PDF disponível
- [ ] Dados da Agnest Farm Lab preparados
- [ ] Informações de parceiros atualizadas
- [ ] Ideia do projeto descrita
- [ ] Análise de aderência concluída
- [ ] Proposta gerada e revisada
- [ ] Documentos exportados em Word

## 🎯 Casos de Uso Comuns

### Cenário 1: Verificar Elegibilidade Rápida
1. Upload do edital
2. Análise de aderência com dados básicos
3. Verificar critérios binários
4. Exportar diagnóstico

**Tempo**: ~5 minutos

### Cenário 2: Preparar Proposta Completa
1. Upload do edital
2. Análise detalhada de aderência
3. Identificar parceiros necessários
4. Gerar e customizar proposta
5. Exportar documentos finais

**Tempo**: ~30-45 minutos

### Cenário 3: Avaliar Múltiplos Editais
1. Carregar primeiro edital
2. Análise rápida
3. Exportar diagnóstico
4. Repetir para próximo edital
5. Comparar oportunidades

**Tempo**: ~10 minutos por edital

## 💡 Dicas Importantes

### ✅ Boas Práticas

1. **Mantenha Dados Atualizados**
   - Atualize perfil da Agnest regularmente
   - Mantenha banco de parceiros atualizado
   - Revise capacidades técnicas

2. **Customize os Rascunhos**
   - Não use os rascunhos como finais
   - Adapte ao contexto específico
   - Revise antes de submeter

3. **Valide Informações**
   - Confirme dados extraídos do edital
   - Verifique critérios com regulamento oficial
   - Consulte FINEP em caso de dúvida

4. **Organize Documentação**
   - Mantenha cópias dos editais
   - Arquive diagnósticos gerados
   - Documente decisões de arranjo

### ⚠️ Pontos de Atenção

1. **Critérios Binários são Eliminatórios**
   - Se algum falhar, proposta será inabilitada
   - Resolva antes de submeter

2. **Contrapartida é Obrigatória**
   - Verifique percentual exigido
   - Confirme capacidade financeira

3. **Parceria com ICT é Obrigatória**
   - Sempre inclua pelo menos 1 ICT
   - EMBRAPA é parceira natural

4. **Prazos Rigorosos**
   - Respeite datas de encerramento
   - Submeta com antecedência

## 🔧 Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| "OPENAI_API_KEY not found" | Edite .env com sua chave |
| "PDF extraction failed" | Verifique se PDF não está corrompido |
| "AI analysis timeout" | Tente novamente em alguns minutos |
| "Streamlit not found" | Execute `pip install streamlit` |
| Aplicação lenta | Reinicie e verifique conexão internet |

## 📞 Suporte Rápido

- **FINEP**: https://www.finep.gov.br
- **Agnest**: https://www.agnestfarmlab.com
- **EMBRAPA**: https://www.embrapa.br

## 🎓 Próximos Passos

Após dominar a v2.0, evolua para:
- **v3.0**: Assistente de preenchimento de documentos
- **v4.0**: Integração com plataforma FINEP
- **v5.0**: Dashboard de acompanhamento de propostas

---

**Versão**: 2.0 - Agnest Edition  
**Última Atualização**: Abril 2026
