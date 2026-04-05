"""Script de renomeação e limpeza do app.py"""

content = open('app.py', 'r').read()

# 1. Renomear para Edital Copilot
replacements = [
    ('FINEP Copilot - Agnest Edition', 'Edital Copilot'),
    ('FINEP Copilot', 'Edital Copilot'),
    ('Agnest Farm Lab Edition', ''),
    ('Agnest Edition', ''),
    ('**Agnest Farm Lab Edition**', ''),
    ('Assistente Estratégico de Captura de Recursos em Editais FINEP',
     'Assistente Estratégico de Captura de Recursos em Editais'),
    ('Acesso restrito • HTTPS seguro • Agnest Farm Lab',
     'Acesso restrito • HTTPS seguro'),
    ('Bem-vindo ao FINEP Copilot', 'Bem-vindo ao Edital Copilot'),
    ('Gerencie os usuários com acesso ao FINEP Copilot.',
     'Gerencie os usuários com acesso ao Edital Copilot.'),
    ('<p>🚀 <strong>FINEP Copilot - Agnest Edition</strong></p>',
     '<p>🎯 <strong>Edital Copilot</strong></p>'),
    ('<p>Desenvolvido para a Agnest Farm Lab e seu ecossistema de parceiros</p>',
     '<p>Assistente Estratégico de Captura de Recursos em Editais</p>'),
    ('<a href="https://www.agnestfarmlab.com" target="_blank">Agnest Farm Lab</a> | ',
     '<a href="https://www.impactability.com.br" target="_blank">Impactability</a> | '),
    ('## 🚀 Edital Copilot', '## 🎯 Edital Copilot'),
    ('<h1 class="main-header">🚀 Edital Copilot - </h1>',
     '<h1 class="main-header">🎯 Edital Copilot</h1>'),
    ('<h1 class="main-header">🚀 Edital Copilot - Agnest Edition</h1>',
     '<h1 class="main-header">🎯 Edital Copilot</h1>'),
    ('<h1 class="main-header">🚀 Edital Copilot</h1>',
     '<h1 class="main-header">🎯 Edital Copilot</h1>'),
    ('page_title="Edital Copilot - ",', 'page_title="Edital Copilot",'),
    ('page_title="Edital Copilot",\n    page_icon="🚀"',
     'page_title="Edital Copilot",\n    page_icon="🎯"'),
    ('"**Edital Copilot** é um assistente estratégico para captura de recursos "\n        "em editais públicos da FINEP, desenvolvido especificamente para a "\n        "Agnest Farm Lab e seu ecossistema de parceiros."',
     '"**Edital Copilot** é um assistente estratégico para captura de recursos em editais públicos nacionais e internacionais."'),
    ('Agnest Farm Lab e seu ecossistema de parceiros.', ''),
    ('para a Agnest Farm Lab e seu ecossistema de parceiros', ''),
    ('para a  e seu ecossistema de parceiros', ''),
    ('Agnest Farm Lab', 'Impactability / Agnest Farm Lab'),
    ('Impactability / Agnest Farm Lab / Sua Iniciativa', 'Sua Empresa / Iniciativa'),
    ('value=st.session_state.company_profile.get("nome_empresa", "Impactability / Agnest Farm Lab")',
     'value=st.session_state.company_profile.get("nome_empresa", "")'),
]

for old, new in replacements:
    content = content.replace(old, new)

open('app.py', 'w').write(content)
print('OK')
