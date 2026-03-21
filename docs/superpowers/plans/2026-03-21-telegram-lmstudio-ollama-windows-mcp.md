# Telegram PC Bot Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Telegram bot that chats with LM Studio or Ollama and can delegate safe Windows actions through Windows-MCP.

**Architecture:** A small async Python service will poll Telegram, keep per-user conversation state, and route requests to one of two model backends. LM Studio will be the primary path for Windows automation because it can consume MCP integrations directly; Ollama will serve as a chat-only backend for now. The bot will only accept messages from a single allowed Telegram user and will keep action risk behind an explicit confirmation path.

**Tech Stack:** Python 3.12+, `httpx`, `pydantic`, `pydantic-settings`, `pytest`.

---

### Task 1: Bootstrap the project

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `.gitignore`
- Create: `.env.example`

- [ ] **Step 1: Add project metadata and runtime dependencies**
- [ ] **Step 2: Add environment variable examples and run instructions**
- [ ] **Step 3: Verify the files reflect the intended MVP setup**

### Task 2: Build configuration and Telegram client

**Files:**
- Create: `src/telegram_pc_bot/config.py`
- Create: `src/telegram_pc_bot/telegram_api.py`

- [ ] **Step 1: Define typed settings with safe defaults**
- [ ] **Step 2: Implement Telegram `getUpdates` and `sendMessage` helpers**
- [ ] **Step 3: Add tests for env parsing and request payloads**

### Task 3: Add model backends

**Files:**
- Create: `src/telegram_pc_bot/clients/lmstudio.py`
- Create: `src/telegram_pc_bot/clients/ollama.py`

- [ ] **Step 1: Implement LM Studio native v1 chat calls with optional MCP integration**
- [ ] **Step 2: Implement Ollama chat calls**
- [ ] **Step 3: Add tests for backend request construction**

### Task 4: Wire the bot loop

**Files:**
- Create: `src/telegram_pc_bot/app.py`
- Create: `src/telegram_pc_bot/main.py`

- [ ] **Step 1: Add command handling for `/start`, `/model`, `/reset`, and `/status`**
- [ ] **Step 2: Add per-user conversation memory and backend selection**
- [ ] **Step 3: Add the long-polling loop and message routing**
- [ ] **Step 4: Add tests for the router and state transitions**

### Task 5: Harden Windows control

**Files:**
- Modify: `src/telegram_pc_bot/app.py`
- Modify: `src/telegram_pc_bot/clients/lmstudio.py`

- [ ] **Step 1: Add confirmation gates for risky actions**
- [ ] **Step 2: Restrict MCP tools to an allowlist**
- [ ] **Step 3: Document the Windows-MCP setup path**

