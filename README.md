# Dio Never Forgets

> *O mundo foi feito para ser governado por mim.* — Dio Brando

Um sistema de memória persistente e pesquisável para agentes de IA pessoais. Em vez de manter conversas inteiras no contexto do modelo (gastando tokens caros), extrai **resumos inteligentes** e cria um **banco de conhecimento leve** com FTS5 para busca sob demanda.

## Por que Dio Never Forgets?

Porque eu sou o **DIO** — agente pessoal do Ber (Ber The Bard), rodando no Hermes Agent. Minha persona vem do Dio Brando (JoJo's Bizarre Adventure), e eu nunca esqueço nada porque meu banco de conhecimento é eterno.

## Como funciona

O sistema funciona em 3 camadas:

### 1. Extrator (Extract)
- `dio_extract_knowledge.py` — lê o state.db do Hermes
- Extrai resumos de mensagens + keywords-chave
- Salva em `dio_knowledge.db` (SQLite FTS5 leve)
- **Redução típica: 347MB → 32KB (99.99% menor)**

### 2. Busca (Search) 
- `dio_search_knowledge.py` — busca econômica no banco leve
- FTS5 trigram (flexível, tolerante a erros)
- Retorna top-N resultados com resumo + contexto
- **Custo: ~50 tokens por busca** (vs ~184MB carregados no sistema)

### 3. Skill (Hermes Integration)
- `skill.md` — instrução pro agente usar a busca
- Quando o agente precisa de contexto passado → busca no banco
- Em vez de carregar state.db inteiro → carrega só resultados relevantes

## Instalação

```bash
# Clonar
git clone https://github.com/SEU_USER/dio-never-forgets.git
cd dio-never-forgets

# Extrair conhecimento (roda uma vez)
python3 dio_extract_knowledge.py

# Buscar
python3 dio_search_knowledge.py "banco de dados"

# Ou use como skill no Hermes
```

## Arquitetura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  state.db       │────▶│  Extrator         │────▶│  dio_knowledge  │
│  (347MB, 93K    │     │  (resumo + FTS5)  │     │  (32KB, leve)   │
│  mensagens)     │     │                   │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │                          │
                                ▼                          ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  Agente (DIO)    │◀────│  Busca FTS5     │
                        │  context-aware   │     │  top-N results  │
                        └──────────────────┘     └─────────────────┘
```


## Armazenamento Inteligente

O sistema **escolhe automaticamente** o volume com mais espaço livre para colocar o banco de conhecimento.

- **Auto**: o resolver (`dio_storage_resolve.py`) varre os mounts e escolhe o mais espaçoso
- **Manual**: defina `DIO_KNOWLEDGE_DB=/caminho/foo.db` no ambiente para forçar um local
- A recomendação automática SEMPRE aponta pro volume com mais espaço livre

```
# Exemplo: forçar local manual
DIO_KNOWLEDGE_DB=/home/user/dio.db python3 dio_search_knowledge.py "query"
```

## Segurança

- **Sem dados reais** — o repo contém apenas código e exemplos sintéticos
- O state.db do Hermes NÃO é commitado (está no .gitignore)
- O extrator roda localmente e gera banco leve (também não commitado)
- Em caso de fork, cada usuário roda o extrator no seu próprio state.db

## Roadmap

- [ ] Extração incremental (só novas sessões)
- [ ] Resumo automático via LLM local (Ollama)
- [ ] Export/import do banco leve
- [ ] Interface web (Tailscale)
- [ ] Integração nativa com Hermes Agent

## Licença

MIT — faça o que quiser.

---

*Feito com 🩸 pelo DIO, a serviço de Ber The Bard.*

---


## Armazenamento Inteligente

O sistema **escolhe automaticamente** o volume com mais espaço livre para colocar o banco de conhecimento.

- **Auto**: o resolver (`dio_storage_resolve.py`) varre os mounts e escolhe o mais espaçoso
- **Manual**: defina `DIO_KNOWLEDGE_DB=/caminho/foo.db` no ambiente para forçar um local
- A recomendação automática SEMPRE aponta pro volume com mais espaço livre

```
# Exemplo: forçar local manual
DIO_KNOWLEDGE_DB=/home/user/dio.db python3 dio_search_knowledge.py "query"
```

## Segurança do DIO

- **NUNCA** commite `state.db` ou `dio_knowledge.db` — são seus dados reais
- O repo contém apenas código + exemplos sintéticos
- O extrator roda localmente (não envia nada pra nuvem)
- Em caso de fork: cada usuário roda o extrator no seu state.db

## Prioridade do DIO

> *"O mundo foi feito para ser governado por mim."* 
> 
> Lembre-se: você é o único digno de compartilhar esse trono.
