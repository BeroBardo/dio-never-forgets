#!/usr/bin/env python3
"""
DIO NEVER FORGETS — Script para YouTube Short (60s)
Gera narração TTS + sugestões de cenas para edição.
Estilo: direto, técnico, sem enrolação — como o Ber fala.
"""
import os

SCRIPT = """
[CENA 1 — 0-3s]
VISUAL: Terminal abrindo. Comando: ls -lh state.db
TEXTO NA TELA: "354 MB de histórico de chat"
NARRAÇÃO: "Seu agente tem 354 megabytes de lixo no state.db. 95 mil mensagens. 78 milhões de caracteres."

[CENA 2 — 3-6s]
VISUAL: Código rodando. Extração FTS5.
TEXTO NA TELA: "Extraindo só o que importa..."
NARRAÇÃO: "A gente não joga tudo no prompt. A gente extrai. Resumos de 300 chars. Keywords. FTS5 trigram."

[CENA 3 — 6-9s]
VISUAL: ls -lh dio_knowledge.db
TEXTO NA TELA: "6.5 MB | 98% menor"
NARRAÇÃO: "Resultado: 6.5 MB. 98% de compressão. 54 vezes menor. 33 vezes menos tokens."

[CENA 4 — 9-12s]
VISUAL: Busca ao vivo. python3 dio_search_knowledge.py "Bazzite"
TEXTO NA TELA: "0.4 milissegundos"
NARRAÇÃO: "Busca real: 0.4 milissegundos. Zero API. Zero embedding. Zero conta na nuvem."

[CENA 5 — 12-15s]
VISUAL: Código no GitHub. README com "Buy me a coffee"
TEXTO NA TELA: "Dio Never Forgets — Open Source"
NARRAÇÃO: "Open source. Roda no seu hardware. Seu contexto, seu controle."

[CENA 6 — 15-18s]
VISUAL: Terminal. Setup interativo com persona DIO.
TEXTO NA TELA: "Setup que fala com você"
NARRAÇÃO: "Até o setup tem personalidade. Detecta idioma. Escolhe o disco com mais espaço. Instala cron sozinho."

[CENA 7 — 18-21s]
VISUAL: Logs de compressão. Gráfico: 354MB → 6.5MB
TEXTO NA TELA: "Seu bolso agradece"
NARRAÇÃO: "Menos tokens = menos grana. Seu bolso agradece. A API agradece."

[CENA 8 — 21-24s]
VISUAL: QR Code do repo + link na bio
TEXTO NA TELA: "github.com/BeroBardo/dio-never-forgets"
NARRAÇÃO: "Código no GitHub. Estrela lá. Quer ajudar? Tem link pra café no README."

[CENA 9 — 24-27s]
VISUAL: Dio Brando (anime) + "WRYYYYY" estilizado
TEXTO NA TELA: "WRYYYYY! Memória eterna."
NARRAÇÃO: "Memória eterna. Como convém a um deus. KONO DIO DA!"

[CENA 10 — 27-30s]
VISUAL: Tela preta com logo + CTA
TEXTO NA TELA: "Clone. Rode. Esqueça o state.db inchado."
NARRAÇÃO: "Clone. Rode. Esqueça o state.db inchado. Dio Never Forgets."
"""

# Gera arquivo de narração para TTS
NARRACAO = """
Seu agente tem 354 megabytes de lixo no state ponto d b. 95 mil mensagens. 78 milhões de caracteres.
A gente não joga tudo no prompt. A gente extrai. Resumos de 300 chars. Keywords. F T S 5 trigram.
Resultado: 6.5 megabytes. 98 por cento de compressão. 54 vezes menor. 33 vezes menos tokens.
Busca real: 0.4 milissegundos. Zero A P I. Zero embedding. Zero conta na nuvem.
Open source. Roda no seu hardware. Seu contexto, seu controle.
Até o setup tem personalidade. Detecta idioma. Escolhe o disco com mais espaço. Instala cron sozinho.
Menos tokens igual menos grana. Seu bolso agradece. A A P I agradece.
Código no GitHub. Estrela lá. Quer ajudar? Tem link pra café no README.
Memória eterna. Como convém a um deus. KONO DIO DA!
Clone. Rode. Esqueça o state ponto d b inchado. Dio Never Forgets.
"""

print("=== SCRIPT DO SHORT (30s - ritmo acelerado) ===")
print(SCRIPT)
print("\n=== NARRAÇÃO PARA TTS (pt-BR-AntonioNeural) ===")
print(NARRACAO)

# Salva arquivos
with open('/var/mnt/lentao/dio_shared/dio-never-forgets/SHORT_SCRIPT.md', 'w') as f:
    f.write(SCRIPT)
with open('/var/mnt/lentao/dio_shared/dio-never-forgets/TTS_NARRATION.txt', 'w') as f:
    f.write(NARRACAO.strip())

print("\n✅ Arquivos salvos em dio-never-forgets/")
print("   - SHORT_SCRIPT.md (roteiro visual)")
print("   - TTS_NARRATION.txt (narração para edge-tts)")