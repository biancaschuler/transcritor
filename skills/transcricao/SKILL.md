---
name: transcricao
description: Transcreve e analisa gravações de áudio e vídeo (reunião de trabalho, entrevista, aula, palestra, mensagem de voz) com o faster-whisper rodando na própria máquina, e gera um .md por gravação com a transcrição revisada, a análise (tema, pautas, decisões, dúvidas, tarefas, insights, frases importantes) e a transcrição bruta anexa. Use sempre que o usuário pedir para transcrever, analisar ou processar uma gravação, apontar um arquivo de áudio ou vídeo, citar a pasta Entrada das transcrições, pedir para continuar as gravações pendentes ou quiser preparar a máquina para transcrever, mesmo que não diga o nome da skill.
---

# Transcrição e análise de gravações

Esta skill transforma uma gravação de áudio ou vídeo num `.md` com a transcrição
fiel e uma análise crítica do que as pessoas conversaram. A transcrição roda na máquina do
usuário com o [faster-whisper](https://github.com/SYSTRAN/faster-whisper), e a
análise segue à risca as regras de `references/regras-analise.md`.

O script fica em `${CLAUDE_SKILL_DIR}/scripts/transcrever.py`, na pasta desta skill.

## Pastas

Tudo mora numa pasta-base, que vem da variável de ambiente `TRANSCRITOR_PASTA`. Sem
ela, a pasta-base é `~/Transcricoes`, que no Windows fica em
`%USERPROFILE%\Transcricoes`. Dentro dela ficam quatro pastas, e áudio e vídeo
dividem todas.

| Pasta | O que guarda |
|---|---|
| `Entrada` | áudio e vídeo que ainda não foram transcritos |
| `Finalizados` | uma subpasta por gravação pronta, com a mídia original e o `.md` |
| `Corrompidos` | arquivo que o ffmpeg provou que não abre |
| `Duplicados` | cópia idêntica, por SHA256, de mídia que já está em `Finalizados` |

Na primeira vez, se a pasta-base não existir, pergunte ao usuário onde ficam as
gravações e só crie as quatro pastas com o ok dele. O script grava log em
`registro/` e lê o glossário em `glossario.md`, os dois dentro da pasta-base. O
glossário não vem pronto. Ele nasce na primeira análise que confirmar um nome
próprio, no formato de `references/formato-glossario.md`.

Quando o usuário apontar um arquivo fora da `Entrada`, pergunte se ele pode ir para
lá antes de começar, porque a mídia original termina em `Finalizados`.

Nada sai de `Corrompidos` e `Duplicados` sem pedido do usuário, e nenhuma mídia se
apaga. Arquivo só muda de pasta.

## Preparar a máquina

Parta do princípio de que o usuário está começando, nunca instalou nada disso e talvez
nem saiba o que é um terminal. Explique cada peça numa frase simples, peça o ok antes
de cada instalação e avise quando ele mesmo precisa agir, como ao digitar a senha do
computador.

A skill depende de quatro peças.

| Peça | Para que serve |
|---|---|
| Python 3.10 ou mais novo (o 3.12 é o recomendado) | roda os scripts da skill |
| ffmpeg, que traz junto o ffprobe | abre o áudio e o vídeo, mede o volume e tira os frames |
| faster-whisper | transcreve a fala no próprio computador |
| modelo do Whisper | baixa sozinho na primeira transcrição, perto de 3 GB no `large-v3`, e precisa de internet nessa hora |

Na primeira vez que a skill rodar, ou quando o usuário pedir para preparar a máquina,
siga esta ordem.

1. **Ache o Python.** Rode `python --version`. No Windows, tente também
   `py --version`, e no macOS e no Linux, `python3 --version`. No Windows, a mensagem
   "Python was not found" ou a Microsoft Store abrindo quer dizer que o Python não
   está instalado, e quem respondeu foi um atalho do próprio Windows.
2. **Sem Python 3.10 ou mais novo, instale.** No Windows, ofereça rodar
   `winget install -e --id Python.Python.3.12`. Sem o winget, o usuário baixa em
   https://www.python.org/downloads/ e marca "Add python.exe to PATH" na primeira tela.
   No macOS, ele instala o Homebrew por https://brew.sh, que pede a senha do Mac, e
   depois você roda `brew install python@3.12`. No Ubuntu e no Debian, ele roda
   `sudo apt install python3 python3-venv python3-pip`, que também pede senha. Depois
   de instalar, o usuário fecha e abre de novo o terminal e o Claude Code, para o
   sistema achar o programa novo.
3. **Rode a conferência** com o Python que respondeu no item 1.

   ```bash
   python "${CLAUDE_SKILL_DIR}/scripts/verificar_ambiente.py"
   ```

   O script diz o que está pronto (`[ok]`), o que falta (`[falta]`), com o comando de
   instalação do sistema do usuário logo abaixo, e o que só merece atenção
   (`[aviso]`). Ele termina com `PYTHON=` e `AMBIENTE_OK=`.
4. **Instale o que faltar, um item por vez, com o ok do usuário.** O ffmpeg sai com
   `winget install -e --id Gyan.FFmpeg` no Windows, `brew install ffmpeg` no macOS e
   `sudo apt install ffmpeg` no Linux. O faster-whisper vai num ambiente virtual em
   `~/.transcritor/venv`, para não mexer no Python do sistema, e a conferência mostra
   os dois comandos exatos, o que cria o ambiente e o que instala.
5. **Confira de novo** até sair `AMBIENTE_OK=1`. O `transcrever.py` acha sozinho o
   ambiente virtual em `~/.transcritor/venv`, então os comandos da skill continuam
   com o Python do item 1.

GPU é opcional. Quem tem placa NVIDIA pode usar `WHISPER_DEVICE=cuda`, que pede as
bibliotecas da NVIDIA listadas no [README do faster-whisper](https://github.com/SYSTRAN/faster-whisper).
Sem GPU, nada disso é necessário.

## Configuração

Tudo é opcional e vai por variável de ambiente, definida antes de chamar o script.

| Variável | Padrão | Para que serve |
|---|---|---|
| `TRANSCRITOR_PASTA` | `~/Transcricoes` | pasta-base das gravações |
| `TRANSCRITOR_GLOSSARIO` | `<pasta-base>/glossario.md` | glossário de nomes próprios |
| `WHISPER_MODELO` | `large-v3` | modelo do faster-whisper, `small` para rodada rápida |
| `WHISPER_IDIOMA` | `pt` | idioma da fala, como `en` ou `es`, ou `auto` |
| `WHISPER_DEVICE` | `cpu` | `cuda` em máquina com GPU NVIDIA |
| `WHISPER_COMPUTE` | `int8` | precisão do modelo |
| `WHISPER_THREADS` | o menor entre 8 e os núcleos lógicos | threads de CPU |
| `WHISPER_BEAM` | `1` | beam size, mais alto fica mais lento e um pouco mais preciso |
| `WHISPER_CHUNK_THRESHOLD_MIN` | `60` | acima disso, em minutos, transcreve em blocos |
| `WHISPER_CHUNK_MIN` | `30` | tamanho de cada bloco, em minutos |
| `TRANSCRITOR_FRAMES_MIN` | `15` | intervalo entre os frames do vídeo, em minutos |

### Tempo de rodada

Como referência, num notebook com 8 threads e sem GPU, o `large-v3` com int8 leva
perto de 0,8x a duração do áudio, então uma hora de reunião fica pronta em uns 50
minutos. O `small` leva perto de 0,16x. Para prometer horário ao usuário, meça a máquina dele
com dez minutos de rodada ou mais, porque o `.part` é gravado por bloco e anda aos
saltos. O modelo, a precisão e o tipo entram no cabeçalho de cada
`.transcript.txt`, então dá para saber depois o que gerou cada arquivo.

## Passo 1, escolher o arquivo

Liste as mídias da `Entrada` (`.mp4`, `.mov`, `.mkv`, `.webm`, `.m4a`, `.mp3`, `.wav`,
`.ogg`, `.opus` e outras), sem contar os intermediários `.audio.wav`,
`.transcript.txt`, `.part` e as pastas `.frames`.

- **Não escolha o caminho pela extensão.** Um `.mp4` pode ser só mensagem de voz. O
  script do Passo 2 olha se o arquivo tem faixa de vídeo, só tira frames quando tem
  e diz no stdout `tipo=video` ou `tipo=audio`. Esse tipo decide o Passo 3.
- **Duplicata se prova por SHA256.** Arquivo cujo nome-base já tem pasta em
  `Finalizados/<nome-base>/` não é pendente. Antes de deixá-lo de lado, compare o
  SHA256 da mídia da entrada com o da mídia da pasta final (`Get-FileHash` no
  PowerShell, `shasum -a 256` no macOS, `sha256sum` no Linux). Com SHA256 igual, a
  cópia da entrada vai para `Duplicados`. Com SHA256 diferente nada se move nem se
  sobrescreve, e o usuário decide. Nome, duração ou tamanho parecidos não provam
  nada.
- **Mídia de conversa tem outro alvo.** Em mensagem de voz ou vídeo de app de
  conversa, a pasta é da conversa (ver a seção abaixo), então pendente é o arquivo
  cuja mídia ainda não está dentro dela. A pasta da conversa existir não prova nada.
- **A mais recente vem primeiro.** Entre os pendentes, vá do mais novo para o mais
  antigo. Use a data embutida no nome quando houver (`AAAA-MM-DD_HH-MM-SS`,
  `Gravação AAAA-MM-DD HHMMSS`, `Screen Recording AAAA-MM-DD at HH.MM.SS`), e a data
  de modificação quando não houver.
- **O pedido por período** ("todas as gravações de maio de 2023") monta a fila pela
  data do nome e, sem ela, pela data de modificação. Se o nome traz um mês que
  conflita com a data de modificação, como `Entrevista12junho.m4a` modificado em 3
  de julho, confirme o escopo com o usuário antes de incluir ou excluir o arquivo.
- **Arquivo corrompido vai para `Corrompidos`.** Quando o script sai com
  `ERRO_FFMPEG=1` e o ffmpeg acusa defeito no arquivo (`moov atom not found`,
  `Invalid data found when processing input`), mova a mídia para `Corrompidos` e
  siga para o próximo pendente, sem tentar de novo. Confira antes que lá não existe
  arquivo de mesmo nome, porque nada se sobrescreve, e leve junto os intermediários
  que ficaram na entrada. Outro erro do ffmpeg vai para o usuário, com as linhas que
  o script mostrou.

## Mídia de app de conversa, uma pasta por conversa

Mensagem de voz e vídeo exportados de app de conversa (WhatsApp, Telegram)
não abrem pasta por gravação. A pasta é da conversa, porque o que importa
ali é o fio com a pessoa.

- **Nome da pasta.** A conversa fecha em `Finalizados/<App> <Contato>/`, como
  `Finalizados/WhatsApp Fulana de Tal/`. O contato sai do nome do arquivo, do nome da
  pasta ou do zip da exportação (`Conversa do WhatsApp com Fulana de Tal`) e, por
  último, do texto da conversa que veio junto. Use a grafia que a exportação traz,
  para a pasta e os arquivos de dentro baterem.
- **Um `.md` por mídia.** Cada mídia tem o seu `.md`, com o mesmo nome-base, e não
  existe `.md` consolidado da conversa.
- **Sem subpasta por mensagem.** A mídia, o `.md` e, no vídeo, a pasta `.frames`
  ficam lado a lado na pasta da conversa.
- **A pasta só cresce.** Mensagem nova do mesmo contato entra na pasta que já
  existe. Encontrar a pasta pronta não é conflito de nome nem prova de duplicata.
- **Sem contato firme, sem chute.** Quando nem o nome do arquivo nem a exportação
  dizem o contato, como num `PTT-20240115-WA0001.opus` solto, a gravação fica numa
  pasta com o nome-base dela e você avisa o usuário.
- **O texto exportado manda.** O `.txt` da exportação diz quem mandou cada mídia e o
  que veio antes e depois. Leia antes de fechar a análise, porque ele decide quem
  fala melhor que o áudio.

Reunião, aula, entrevista e gravação de tela continuam com uma pasta por gravação.

## Passo 2, rodar o pré-processamento

Rode o script **em background rastreado pela ferramenta** (`run_in_background: true`
no Bash ou no PowerShell), para o harness avisar quando terminar. Não use
`Start-Process` nem `&` soltos, porque o processo desacopla, não gera aviso de
conclusão e obriga a ficar consultando.

```bash
python "${CLAUDE_SKILL_DIR}/scripts/transcrever.py" "<pasta-base>/Entrada/<arquivo>"
```

No Windows, `py -3` no lugar de `python` escolhe a versão certa quando a máquina tem
mais de uma. As variáveis da seção Configuração vão antes do comando, como
`$env:WHISPER_MODELO = "small"` no PowerShell ou `WHISPER_MODELO=small python ...` no
bash.

O script gera estes arquivos ao lado da mídia.

- `<arquivo>.audio.wav`, o áudio mono 16 kHz, que é intermediário.
- `<arquivo>.transcript.txt`, a transcrição bruta com timestamps, em UTF-8.
- `<arquivo>.frames/frame_HHhMMmSSs.jpg`, só em vídeo, com um frame a cada 15 minutos.

Durante a transcrição, os segmentos vão para `<arquivo>.transcript.txt.part`, com
flush a cada linha, e o arquivo só vira `.transcript.txt` quando a transcrição
termina. Dá para acompanhar o progresso lendo o `.part`, e o `.transcript.txt` só
existe quando está completo. O script também é idempotente. Se o `.audio.wav`, o
`.transcript.txt` ou os frames já existirem, ele pula a etapa, e um `.part` com
segmentos faz a transcrição retomar do último timestamp.

### Áudio mudo

Logo depois de extrair o áudio, o script mede o volume com o `volumedetect` do
ffmpeg e imprime `[audio] nivel: mean=... dB | max=... dB`. Com pico abaixo de
-50 dB, como numa gravação de tela sem som, ele pula a transcrição, imprime
`AUDIO_MUDO=1` e encerra, porque o Whisper fica preso alucinando sobre o silêncio
("Legendas pela comunidade Amara.org", linhas só com "."). Nesse caso não tente
transcrever fala. Em vídeo, analise pelos frames (texto na tela, slide, chat) e
registre no `.md` uma nota técnica dizendo que o áudio é mudo. Em áudio puro não há
frames, então registre que o arquivo é silencioso e pergunte ao usuário o que fazer.

### Silêncio longo dentro da gravação

Quando o arquivo tem som mas traz uma janela de silêncio de 5 minutos ou mais, o
script olha onde ela está.

- **No fim**, que é o caso da reunião que acabou com a gravação ligada, ele corta e
  transcreve só até o fim do conteúdo, e imprime
  `[audio] silencio FINAL longo ... transcrevendo so ate HH:MM:SS`. Se sobrarem menos
  de 10 segundos de conteúdo, o arquivo conta como mudo.
- **No meio ou no começo**, ele não corta, porque perderia o que vem depois. Só
  imprime `[audio] silencio longo NO MEIO ...`, e você avalia o trecho na análise.

A janela acima de 10 minutos também sai resumida na linha `SILENCIO_10MIN=`, para
entrar no `.md`.

### Parciais de rodada interrompida

Nunca apague os parciais de uma rodada interrompida (`.audio.wav`,
`.transcript.txt.part`, pasta `.frames`). Antes de relançar, confira se o `.wav` tem
duração compatível com a mídia original e se o `.part` e os frames têm dado válido,
e só refaça o que faltar ou estiver corrompido. Se não der para saber com segurança,
pergunte ao usuário antes de descartar qualquer parcial.

A saída começa vazia, porque o script primeiro extrai o áudio e os frames e carrega
o modelo. Não narre o progresso além de confirmações breves, porque o usuário já
conta com uma rodada longa.

**Assim que o `.transcript.txt` existir e a tarefa em background terminar, siga
direto para o Passo 3, sem esperar confirmação nem novo pedido do usuário.**

## Passo 3, identificar quem fala

**Em vídeo**, leia as imagens de `<arquivo>.frames/`. Zoom, Meet e Teams costumam
mostrar o nome de quem fala na legenda, no destaque do quadro ou na lista de
participantes. Use as imagens para trocar `Pessoa 1` e `Pessoa 2` pelo nome real,
sempre que ele bater com o áudio.

Se os frames de 15 em 15 minutos não bastarem, tire até 10 frames extras em momentos
escolhidos, como quando um falante novo começa no `.transcript.txt`, quando o
destaque troca de quadro ou quando a lista de participantes aparece.

```bash
ffmpeg -ss HH:MM:SS -i "<arquivo>.mp4" -frames:v 1 -q:v 2 "<arquivo>.frames/frame_HHhMMmSSs.jpg"
```

Só mantenha `Pessoa N` se nem os frames extras derem certeza.

**Em áudio puro** não há frames. O nome sai só do que é dito (nome citado, voz
distinta, contexto) e do glossário. Se a mesma reunião tiver uma gravação de vídeo
em `Finalizados`, os frames dela valem como fonte para nome e presença.

## Passo 4, transcrição final e análise (interno, nunca no chat)

Leia o `<arquivo>.transcript.txt`, que traz linhas `[HH:MM:SS -> HH:MM:SS] texto`. A
partir dele, dos frames e do glossário, produza a transcrição revisada e a análise
completa seguindo **à risca** `references/regras-analise.md`. Ali estão as regras de
fidelidade, os marcadores `[inaudível]`, `[incerto: ...]` e `[interpretação]`, a
inferência da data real, o censo de participantes, a estrutura de seções e as regras
próprias de entrevista e de reunião de trabalho.

## Passo 5, salvar e organizar a pasta final

1. Salve o documento em `Entrada/<arquivo>.md`, com **exatamente** o nome-base da
   mídia. O nome não ganha data, prefixo, sufixo nem tradução, então
   `2024-01-15_10-00-00-000.mp4` vira `2024-01-15_10-00-00-000.md`.
2. **Antes de apagar qualquer coisa, cole a transcrição bruta dentro do `.md`.** O
   conteúdo integral do `.transcript.txt` vai para a seção final
   `# Anexo, transcrição bruta`, num bloco de código, sem corte nem resumo. A
   gravação com mais de um arquivo (partes em sequência, gravação paralela, cauda
   recuperada) ganha uma subseção por arquivo de origem.
3. Crie `Finalizados/<arquivo>/`, com o mesmo nome-base. Se ela já existir, pare e
   volte à regra de duplicata do Passo 1, porque áudio e vídeo dividem a mesma pasta
   final e nada se mistura nem se sobrescreve. A mídia de conversa vai para a pasta
   da conversa, que costuma já existir.
4. Mova para a pasta final a mídia original, o `.md` e, em vídeo, a pasta `.frames`.
5. Remova o `.transcript.txt` e o `.audio.wav` só depois de conferir que o anexo
   está completo. O script refaz o `.audio.wav` em segundos a partir da mídia, mas o
   bruto só volta com uma nova rodada de transcrição, que pode levar horas.

No fim, a pasta guarda a mídia original, o `.md` e, em vídeo, os frames, e a
`Entrada` não tem mais nenhum arquivo daquela gravação.

## Passo 6, resposta final

Siga a regra de resposta de `references/regras-analise.md`. Não mostre a
transcrição, a análise nem trecho delas no chat. Responda só algo como "Transcrição
e análise concluídas com sucesso.", com a pasta final e a lista dos termos marcados
como incertos.

## Próxima gravação

Se houver outros pendentes na `Entrada` e o usuário pedir para continuar, repita a
partir do Passo 1, sempre pegando o mais recente entre os que faltam.

## Modo lote

Vale quando o usuário pede várias gravações, um período ou um mês inteiro, sem
confirmação entre uma e outra.

- Processe em sequência, da mais recente para a mais antiga, sem pausar entre os
  arquivos.
- Use o disco como fonte de verdade. Pendente é a gravação do escopo que ainda não
  tem pasta em `Finalizados` ou, em mídia de conversa, que ainda não está dentro da
  pasta da conversa. Recalcule a cada ciclo, porque assim a conta se corrige sozinha
  mesmo se o contexto for resumido no meio do lote.
- **A CPU não fica ociosa.** A transcrição é o gargalo e ocupa as threads da CPU,
  enquanto a análise é trabalho do modelo e quase não usa CPU local. Enquanto houver
  gravação do escopo sem transcrição, tem de existir exatamente uma transcrição
  rodando.
  - No instante em que a transcrição da gravação N termina, a primeira ação é lançar
    em background a da N+1, antes de qualquer análise, frame, `.md` ou pasta da N.
  - Só depois, com a N+1 rodando, faça os Passos 3 a 5 da N.
  - Mantenha uma transcrição por vez, porque duas disputam as mesmas threads e as
    duas ficam mais lentas.
  - A fila de análise pode acumular, já que análise não usa CPU. **Nunca segure uma
    transcrição para zerar análise.**
- Dê um panorama inicial do lote, com a quantidade e a previsão de tempo, que pode
  passar de horas, e depois siga sem narrar cada passo.

## Retomando um lote numa sessão nova

Ao retomar numa sessão nova, com contexto resumido ou depois de qualquer
interrupção, siga esta ordem.

1. Recalcule do disco o que falta, com a mesma regra de pendente do Modo lote.
2. **A primeira ação é garantir uma transcrição rodando.** A transcrição de uma
   sessão anterior não sobrevive à troca de sessão, então quase sempre não há
   nenhuma ativa ao retomar. Lance já a do próximo pendente (Passos 1 e 2), antes de
   qualquer análise.
3. Só então, com ela rodando, zere a fila de análise, que são os `.transcript.txt` da
   `Entrada` cuja gravação ainda não tem pasta em `Finalizados`. Faça os Passos 3 a 5
   de cada um, sempre com a seção `# Tema`.
4. Quando a transcrição terminar, lance a próxima na hora e só depois volte às
   análises.
5. Se houver um arquivo de inventário do lote, recalcule a fila pelo disco, sem
   confiar em lista antiga, e atualize o inventário a cada gravação concluída.
