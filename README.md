# Dio Never Forgets

> *"O mundo foi feito para ser governado por mim... e esse banco de dados também."* — Dio Brando

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey.svg)]()

Um sistema open-source de **compressão e busca de memória persistente** para agentes de IA locais (Hermes Agent e outros). 

Em vez de queimar contexto e tokens carregando arquivos de banco de dados inteiros para o modelo, o **Dio Never Forgets** extrai micro-resumos estruturados e constrói um índice **FTS5 Full-Text Search (BM25)** local, ultra-rápido e econômico.

---

### 📊 Números Reais em Produção

Em nossos testes reais de estresse em uma instância ativa do Hermes Agent:
- **Banco Original (`state.db`):** `354.6 MB` (20.037 sessões, 95.026 mensagens, 78.8M caracteres de texto)
- **Banco Comprimido (`dio_knowledge.db`):** `6.5 MB` (8.173 entradas consolidadas)
- **Taxa de Compressão de Disco:** **`98.17%` (54.7x menor)**
- **Redução de Tokens de Contexto:** **`96.97%` (33.1x mais enxuto)**
- **Tempo Médio de Busca:** **`< 5 milissegundos`** (zero chamadas de API, zero embedding externo)

---

## ⚡ Por que usar?

1. **Zero Custo de API:** Não usa embeddings caros da OpenAI ou Voyage. Busca por BM25/FTS5 trigram 100% local.
2. **Contexto Cirúrgico:** Seu agente busca somente os 3-5 turnos relevantes sob demanda (~100 tokens), poupando a janela de contexto.
3. **Storage Inteligente:** Detecta dinamicamente qual disco ou partição da máquina tem mais espaço livre e recomenda automaticamente onde salvar os dados.
4. **Setup Interativo com Persona:** Um instalador interativo bilíngue (PT-BR / EN) com a persona teatral do **Dio Brando** guiando a configuração e o cron semanal.

---

## 🚀 Instalação Rápida

```bash
# 1. Clone o repositório
git clone https://github.com/BeroBardo/dio-never-forgets.git
cd dio-never-forgets

# 2. Execute o Setup Interativo (emula a persona do DIO)
python3 setup.py

# 3. Extraia o conhecimento do seu agente (roda em segundos)
python3 dio_extract_knowledge.py

# 4. Busque qualquer coisa no histórico com custo zero
python3 dio_search_knowledge.py "sua busca" --limit 3
```

---

## 🧠 Arquitetura

```
┌───────────────────────────┐      ┌──────────────────────────┐      ┌───────────────────────────┐
│     state.db Original     │ ───▶ │   Extrator Inteligente   │ ───▶ │     dio_knowledge.db      │
│  (354 MB / 95k mensagens) │      │  (Filtro de ruído + FTS) │      │  (6.5 MB / 98% menor)     │
└───────────────────────────┘      └──────────────────────────┘      └───────────────────────────┘
                                                 │                                 │
                                                 ▼                                 ▼
                                   ┌──────────────────────────┐      ┌───────────────────────────┐
                                   │    Agente de IA (DIO)    │ ◀─── │     Busca FTS5 (BM25)     │
                                   │    Context-Aware Lean    │      │    (~100 tokens / 2ms)    │
                                   └──────────────────────────┘      └───────────────────────────┘
```

---

## ☕ Apoie o Projeto / Donations

Se o **Dio Never Forgets** te poupou gigabytes de RAM, salvou seu limite de contexto ou cortou seus custos de API com tokens:

- **Pix (Brasil):** `bevicter@gmail.com`
- **GitHub Sponsors / Crypto:** Em breve
- ⭐ **Deixe uma estrela no repositório!** Isso ajuda o projeto a alcançar mais pessoas.

---

## 🛡️ Privacidade e Segurança

- **Zero vazamento:** Seu `state.db` e `dio_knowledge.db` locais nunca saem da sua máquina (estão no `.gitignore`).
- **Local-first:** Nenhum dado é enviado para servidores externos.

---

## 📜 Licença

Distribuído sob a licença **MIT**. Veja `LICENSE` para mais detalhes.

---

*Criado com 🩸 por Ber The Bard & DIO.*
