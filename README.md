# CaimBot — Guia Completo de Instalação e Uso

CaimBot é um bot modular para Discord focado em **moderação**, **tickets de suporte**, **logs separados por servidor** e **comandos utilitários**.

---

## Sumário
1. [Visão Geral](#visão-geral)  
2. [Pré-requisitos](#pré-requisitos)  
3. [Estrutura do Repositório](#estrutura-do-repositório)  
4. [Arquivos de Configuração](#arquivos-de-configuração)  
5. [Instalação Local](#instalação-local)  
6. [Rodando o Bot](#rodando-o-bot)  
7. [Implantação em Produção](#implantação-em-produção)  
8. [Criar e Autorizar o Bot no Discord](#criar-e-autorizar-o-bot-no-discord)  
9. [Comandos Disponíveis](#comandos-disponíveis)  
10. [Sistema de Tickets](#sistema-de-tickets)  
11. [Logs por Servidor](#logs-por-servidor)  
12. [Segurança e Boas Práticas](#segurança-e-boas-práticas)  
13. [Troubleshooting](#troubleshooting)  
14. [Entrega ao Cliente](#entrega-ao-cliente)  
15. [FAQ Rápida](#faq-rápida)  

---

## Visão Geral
CaimBot oferece funcionalidades de:
- **Moderação:** kick, ban, mute, tempban, warns, logs.  
- **Suporte/Tickets:** criação de tickets com modais e botões.  
- **Logs separados por servidor**: cada guilda possui seu próprio canal de logs.  
- **Utilidades:** comandos simples como `/say`.

---

## Pré-requisitos
- Python 3.11+  
- pip  
- Git (opcional)  
- Token do bot Discord (`token_dc`)  

---

## Estrutura do Repositório


projeto.bot/
├─ cogs/
│ ├─ moderacao.py
│ ├─ suporte.py
│ ├─ logs_suporte.py
│ └─ utilidades.py
├─ .gitignore
├─ .env.example
├─ main.py
├─ requirements.txt
├─ config.json
└─ warns.json


- `config.json` e `warns.json` são gerados em runtime e **não devem ser versionados**.

---

## Arquivos de Configuração

### `.env`
```env
token_dc=SEU_TOKEN_DO_DISCORD_AQUI

.env.example
# Modelo para entrega, não contém token real
token_dc=COLE_AQUI_SEU_TOKEN

config.json

Exemplo de configuração por guild:

{
  "GUILD_ID": {
    "log_channel_id": 111111111111111111,
    "suporte_logs_channel_id": 222222222222222222,
    "mod_channel_id": 333333333333333333,
    "suporte_channel_id": 444444444444444444,
    "suporte_category_id": 555555555555555555
  }
}

Instalação Local

Clone o repositório:

git clone <URL_DO_REPO>
cd projeto.bot


Crie virtualenv:

python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate    # Windows


Instale dependências:

pip install -r requirements.txt


Crie .env com seu token do Discord.

Rodando o Bot
python main.py


O bot carregará os cogs e sincronizará comandos com o Discord.

Mensagens de erro aparecerão no terminal.

Implantação em Produção
VPS + systemd

Criar unit file com path do projeto e virtualenv.

Comando de start: ExecStart=/caminho/.venv/bin/python main.py.

Docker
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python","main.py"]

Railway / Replit / Render

Adicione variável de ambiente token_dc.

Comando: python main.py.

Criar e Autorizar o Bot no Discord

Developer Portal → Applications → New Application → Bot → Add Bot.

Copie token → coloque em .env.

OAuth2 URL Generator → Scopes: bot, applications.commands.

Permissões recomendadas:

Send Messages

Embed Links

Manage Channels

Manage Messages

Kick Members

Ban Members

Moderate Members

Comandos Disponíveis
Moderação

/setup_logs — cria canal de logs.

/set_mod_channel <canal> — define canal de moderação.

/limpar <quantidade> — apaga mensagens.

/kick <membro> [motivo]

/ban <membro> [motivo]

/tempban <membro> <minutos> [motivo]

/mute <membro> <minutos> [motivo]

/unmute <membro>

/warn <membro> [motivo]

/warns <membro>

/clear_warns <membro>

/help — lista de comandos.

Tickets / Suporte

/suporte_create — cria categoria e canal de tickets.

Botões dentro do ticket: Fechar Ticket, Notificar Moderação.

Utilidades

/say <canal> <mensagem> — envia mensagem como bot.

Sistema de Tickets

/suporte_create cria categoria Suporte e canal suporte.

Usuário abre ticket via botão/modal.

Ticket gera canal privado para usuário + bot.

Notificação enviada para mod_channel_id e logs para suporte_logs_channel_id.

Botões permitem fechar ticket ou notificar moderação.

Logs por Servidor

/setup_logs → logs de moderação

/setup_logs_suporte → logs de suporte

Configuração armazenada em config.json[guild_id].

Segurança e Boas Práticas

Nunca versionar .env.

Regenerar token se houver vazamento.

Use variáveis de ambiente seguras em produção.

Revise permissões do bot para evitar excessos.

Troubleshooting

Erro de interação falhou → use await interaction.response.defer().

Comandos globais não aparecem → pode levar até 1 hora; use bot.tree.sync(guild=...) para testes.

Bot não cria canais → verifique Manage Channels e permissões de role.

Token vaza no Git → remover histórico e .env do repo.

Entrega ao Cliente

Enviar repositório/ZIP sem .env.

Incluir .env.example.

requirements.txt para instalação.

Pequeno guia de setup: clone, venv, pip install, criar .env, rodar python main.py.

FAQ Rápida

Múltiplos servidores? → Suportado, cada guild_id tem config própria.

Precisa de admin? → Apenas para comandos de setup ou /say.

Logs e suporte em canais diferentes? → /setup_logs + /setup_logs_suporte.

Contato

Autor: cainxz

Discord: @caimxzzzz