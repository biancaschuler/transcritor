---
name: temas-transcricoes
description: >-
  Lê as transcrições já concluídas pela skill transcricao, na pasta Finalizados, e
  devolve uma lista dos temas tratados, agrupada por assunto. Use sempre que o
  usuário pedir para verificar ou listar os temas, perguntar do que já foi
  transcrito, pedir um resumo dos temas das transcrições concluídas ou quiser saber
  que reuniões já foram processadas, mesmo que não diga o nome da skill. Diferente
  da skill transcricao, que cria transcrição nova, esta só lê o que está pronto e
  não transcreve nem reprocessa gravação nenhuma.
---

# Temas das transcrições concluídas

## Objetivo

Dar uma visão rápida e organizada do que já foi transcrito. A skill varre as
transcrições concluídas, extrai o tema de cada arquivo e apresenta uma **lista
agrupada por assunto**, e não um arquivo atrás do outro.

A origem é a pasta `Finalizados`, dentro da pasta-base da skill `transcricao`, que
vem da variável `TRANSCRITOR_PASTA` e, sem ela, fica em `~/Transcricoes`. Cada
gravação é uma subpasta com um `.md` de mesmo nome, e a mídia de app de conversa tem
uma subpasta por conversa, com vários `.md` dentro.

O script marca cada item como vídeo ou áudio pelo `tipo=` do anexo bruto e, sem ele,
pela pasta `.frames` ao lado do `.md`. Use o rótulo para separar a lista, e não como
prova do tipo, porque uma transcrição antiga pode estar sem os dois.

## Como cada arquivo guarda o tema

- O campo `**Tema:**` da seção `# Informações gerais` é a frase mais concisa e tem
  preferência.
- Todo arquivo tem a seção `# Resumo objetivo`, e o primeiro parágrafo dela é o
  melhor resumo do assunto quando falta o `**Tema:**`.

O script já aplica essa preferência.

## Passo 1, extrair os temas com o script

O script fica em `${CLAUDE_SKILL_DIR}/scripts/extrair_temas.py`, na pasta desta
skill. Ele lê tudo em UTF-8 e varre a pasta `Finalizados` por padrão.

```bash
python "${CLAUDE_SKILL_DIR}/scripts/extrair_temas.py"
```

A saída lista cada pasta com o seu tema, separada por tipo de mídia. Para processar
em JSON, acrescente `--json`. Para varrer outras pastas, use `--bases "<caminho>"`.

Sem o script, leia os `.md` direto com a ferramenta Read, que respeita UTF-8, e pegue
o `**Tema:**` ou o primeiro parágrafo de `# Resumo objetivo`. No Windows PowerShell
5.1, **não** use `Get-Content` sem `-Encoding UTF8`, porque os acentos saem
corrompidos.

## Passo 2, agrupar por tema e responder

A extração entrega um item por transcrição, e o valor está em **agrupar**. Leia os
temas e junte as transcrições que tratam do mesmo assunto, projeto ou cliente sob um
rótulo curto. Várias gravações costumam ser do mesmo fio condutor (um projeto, um
cliente, uma pauta recorrente), então agrupe por esse fio, e não
pela data.

Use este formato de resposta.

```
## <emoji opcional> <Rótulo do tema> (<nº de gravações>)
<1 frase do que esse grupo cobre.>
- `<pasta>` · `<pasta>` · ...

## <próximo tema> ...
```

Feche com um parágrafo curto de **resumo geral**, com o assunto dominante e o que
aparece à parte, e ofereça desdobramentos, como detalhar um grupo, gerar um índice em
Markdown ou cruzar decisões e tarefas pendentes entre gravações do mesmo grupo.

Diretrizes de agrupamento.

- Agrupe por **fio condutor**, e não por data. O fio pode ser um projeto ou cliente
  ("Projeto Quasar, redesenho do app"), uma pauta interna (contratações), uma
  iniciativa (novo processo de compras) ou uma natureza (aulas, reuniões de
  status). Um item pode aparecer em mais de um grupo quando cobre dois assuntos.
- Mantenha os rótulos curtos e o resumo de cada grupo numa frase, porque o usuário
  quer uma visão de relance, e não os resumos longos na íntegra.
- Use o nome da pasta como identificador da gravação. A data no padrão
  `AAAA-MM-DD_HH-MM-SS` já serve de referência cronológica.
- Informe sempre o total de transcrições e, quando ajudar, separe áudio de vídeo.

## Escopo

Esta skill só **lê e resume** o que já está em `Finalizados`. Para transcrever uma
gravação nova ou reprocessar um pendente, use a skill `transcricao`, que lê a
`Entrada`.
