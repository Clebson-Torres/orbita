# Orbita

Controle seu PC Windows via Telegram usando um LLM local (Ollama ou LM Studio).

Envie mensagens pelo celular e o Orbita executa ações no seu computador — abre apps, tira screenshots, busca notícias, verifica RAM, roda scripts PowerShell e muito mais.

## Instalação (Windows)

Abra o PowerShell e cole:

```powershell
irm https://raw.githubusercontent.com/Clebson-Torres/orbita/main/install.ps1 | iex
```

O instalador:
- verifica o Python (3.12+ necessário)
- instala o Orbita via pip
- cria um lançador silencioso (sem janela CMD)
- cria atalho na área de trabalho
- pergunta se quer iniciar com o Windows

Após instalar, configure:

```powershell
orbita setup
```

E inicie:

```powershell
orbita run          # com janela de terminal (desenvolvimento)
# ou
# clique duas vezes em Orbita.lnk na área de trabalho (sem janela)
```

## Requisitos

- Windows 10/11
- Python 3.12+ — [python.org](https://python.org)
- [Ollama](https://ollama.com) **ou** [LM Studio](https://lmstudio.ai) rodando localmente
- Bot do Telegram criado via [@BotFather](https://t.me/botfather)

## Modelos recomendados (Ollama)

```powershell
ollama pull qwen3:4b   # melhor equilíbrio (6 GB VRAM)
ollama pull qwen3:8b   # mais qualidade
```

## Comandos no Telegram

| Comando | Descrição |
|---|---|
| `/help` | Lista todos os comandos |
| `/status` | Backend ativo, dry-run, histórico |
| `/model ollama\|lmstudio` | Troca o backend |
| `/dryrun on\|off` | Simula ações sem executar |
| `/skills` | Lista skills carregadas com nível de risco |
| `/news g1 economia` | Notícias via RSS (sem browser) |
| `/audit` | Últimas 20 ações registradas |
| `/reset` | Limpa memória da conversa |

## CLI

```powershell
orbita setup              # wizard de configuração (grava %APPDATA%\Orbita\.env)
orbita run                # inicia o bot
orbita doctor             # verifica integrações
orbita env                # exibe o .env atual
orbita skills             # lista skills disponíveis
orbita check telegram     # testa só o Telegram
orbita check lmstudio     # testa só o LM Studio
orbita check ollama       # testa só o Ollama
orbita check mcp          # testa só o Windows-MCP
```

## Skills

O Orbita usa um sistema de skills — pastas com `SKILL.md` que ensinam o LLM quando e como usar cada capacidade. São carregadas automaticamente na inicialização.

Skills incluídas: screenshot, clipboard, volume, brilho, rede, bateria, processos, serviços, arquivos, sistema, janelas, notificações, scripts, notícias RSS, modo foco, browser e mais.

Para criar uma skill nova:

```
%APPDATA%\Orbita\skills\
  minha_skill\
    SKILL.md
```

## Dados em runtime

Tudo fica em `%APPDATA%\Orbita\`:

```
%APPDATA%\Orbita\
  .env          ← configuração (gerado pelo orbita setup)
  memory.json   ← histórico de conversas
  audit.log     ← registro de ações
  orbita.log    ← log do sistema
  orbita.vbs    ← lançador silencioso
  skills\       ← skills do usuário
```

## Licença

MIT
