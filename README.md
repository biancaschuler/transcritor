# Transcritor

Duas skills do Claude Code que transcrevem gravações de reunião, entrevista e aula no
seu próprio computador, com o [faster-whisper](https://github.com/SYSTRAN/faster-whisper),
e transformam cada gravação num arquivo `.md` com a transcrição revisada e uma
análise do que as pessoas conversaram.

[In English](#in-english)

## O que você recebe

Cada gravação vira um `.md` com estas partes.

- A data real da gravação, o tema e a lista de quem participou, com cargo e
  organização quando a conversa diz.
- A transcrição revisada, por turno de fala e com o nome de quem fala.
- O resumo, as pautas com o minuto em que cada uma começou, as decisões, as dúvidas
  abertas, as tarefas com dono e prazo, os insights e as frases importantes.
- A transcrição bruta inteira no fim, para conferir a revisão.

A skill `transcricao` faz esse trabalho, e a `temas-transcricoes` lê o que já está
pronto e lista os temas agrupados por assunto.

## Passo a passo para quem está começando

1. **Instale o Claude Code** seguindo as instruções de https://claude.com/claude-code.
2. **Instale as skills.** Abra o Claude Code e rode estes dois comandos.

   ```
   /plugin marketplace add biancaschuler/transcritor
   /plugin install transcritor@transcritor
   ```

   Se preferir não usar plugin, baixe o repositório pelo botão **Code** e depois
   **Download ZIP**, aqui no GitHub. Descompacte e copie as pastas
   `skills/transcricao` e `skills/temas-transcricoes` para a pasta `.claude/skills`
   da sua pasta de usuário, que no Windows é `C:\Users\<seu usuário>\.claude\skills`
   e no macOS e no Linux é `~/.claude/skills`.
3. **Peça ao Claude para preparar a máquina.** Escreva algo como "prepara a minha
   máquina para transcrever gravações". A skill confere o que falta, explica cada
   peça e instala com o seu ok. Algumas instalações pedem a senha do computador, e
   nesses casos o Claude mostra o comando para você mesmo rodar.
4. **Coloque as gravações na pasta `Entrada`.** Na primeira vez, o Claude pergunta
   onde você quer guardar tudo e só cria as pastas com o seu ok. Se você não escolher
   outro lugar, elas ficam em `Transcricoes`, dentro da sua pasta de usuário.
5. **Peça a transcrição**, como em "transcreve as gravações pendentes".

## O que precisa estar instalado

O passo 3 cuida disso, e a tabela serve para quem prefere instalar à mão.

| Programa | Para que serve | Windows | macOS | Ubuntu e Debian |
|---|---|---|---|---|
| Python 3.10 ou mais novo | roda os scripts | `winget install -e --id Python.Python.3.12` | `brew install python@3.12` | `sudo apt install python3 python3-venv python3-pip` |
| ffmpeg | abre áudio e vídeo e tira os frames | `winget install -e --id Gyan.FFmpeg` | `brew install ffmpeg` | `sudo apt install ffmpeg` |
| Homebrew | instala programas no macOS | não precisa | https://brew.sh | não precisa |
| faster-whisper | transcreve a fala | ver abaixo | ver abaixo | ver abaixo |

No Windows sem o winget, o Python também sai do site https://www.python.org/downloads/.
Na primeira tela da instalação, marque "Add python.exe to PATH".

O faster-whisper vai num ambiente virtual próprio, para não mexer no Python do
sistema. No macOS e no Linux, rode estes dois comandos no terminal.

```bash
python3 -m venv ~/.transcritor/venv
~/.transcritor/venv/bin/python -m pip install faster-whisper
```

No Windows, os mesmos dois comandos ficam assim no PowerShell.

```powershell
py -3 -m venv "$env:USERPROFILE\.transcritor\venv"
& "$env:USERPROFILE\.transcritor\venv\Scripts\python.exe" -m pip install faster-whisper
```

Depois de instalar o Python ou o ffmpeg, feche e abra de novo o terminal e o Claude
Code, para o sistema achar o programa novo. Na primeira transcrição, o faster-whisper
baixa o modelo de voz, que tem perto de 3 GB no `large-v3`, então deixe uns 5 GB
livres no disco e a internet ligada nessa hora.

Para conferir tudo de uma vez, rode o script de conferência da skill.

```bash
python skills/transcricao/scripts/verificar_ambiente.py
```

## Pastas

```
Transcricoes/
├── Entrada/        gravações por transcrever
├── Finalizados/    uma pasta por gravação pronta, com a mídia e o .md
├── Corrompidos/    arquivos que o ffmpeg não consegue abrir
├── Duplicados/     cópias idênticas de algo que já foi finalizado
├── registro/       log de cada rodada
└── glossario.md    grafia certa dos nomes próprios, criado pela própria skill
```

Para usar outra pasta, defina a variável de ambiente `TRANSCRITOR_PASTA`.

Mensagem de voz e vídeo exportados do WhatsApp, do Instagram ou do Telegram ficam
juntos numa pasta por conversa, como `Finalizados/WhatsApp <contato>/`, com um `.md`
por mensagem.

## Glossário

O Whisper erra nome próprio com frequência. Por isso a skill mantém um
`glossario.md` com a grafia certa de pessoas, empresas, projetos e termos, e com as
grafias erradas que já apareceram. O glossário não vem pronto. A skill cria o arquivo
na primeira transcrição que confirmar um nome, no formato descrito em
[`formato-glossario.md`](skills/transcricao/references/formato-glossario.md), e
acrescenta nomes a cada gravação. O script usa os nomes confirmados para orientar a
transcrição seguinte.

## Configuração

Todas as variáveis são opcionais.

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

Quem tem GPU NVIDIA e quer usar `WHISPER_DEVICE=cuda` precisa das bibliotecas da
NVIDIA listadas no [README do faster-whisper](https://github.com/SYSTRAN/faster-whisper).

## Quanto tempo leva

Como referência, num notebook com 8 threads e sem GPU, o modelo `large-v3` leva perto
de 0,8x a duração do áudio, então uma reunião de uma hora fica pronta em uns 50
minutos. O `small` leva perto de 0,16x, mas erra bem mais nome próprio. A transcrição
ocupa quase toda a CPU, e uma chamada de vídeo no mesmo computador pode ficar com o
som pior enquanto ela roda.

## Privacidade

A transcrição roda no seu computador, e o áudio fica nele. Quem escreve a análise é
o Claude, então o texto da transcrição e os frames do vídeo passam pelos servidores
da Anthropic, como qualquer arquivo que o Claude lê numa sessão. Leve isso em conta
antes de processar gravação com dado sensível ou sob contrato de confidencialidade.

Se você clonar este repositório para mexer nele, o `.gitignore` bloqueia mídia,
transcrição, log e `glossario.md`, para nada seu subir por engano.

## Problemas comuns

- **O Windows abre a Microsoft Store quando você digita `python`.** O Python não está
  instalado, e quem respondeu foi um atalho do Windows. Instale pelo winget ou pelo
  python.org e abra o terminal de novo.
- **A mensagem "ffmpeg nao encontrado" aparece logo depois da instalação.** Feche e
  abra o terminal e o Claude Code, para o sistema ler o caminho novo.
- **O download do modelo para no meio.** Defina `HF_HUB_DISABLE_XET=1` e rode de
  novo, porque em algumas redes o backend xet do Hugging Face bloqueia o download.
- **O `pip install` dá erro de "externally-managed-environment" no macOS ou no
  Linux.** Instale dentro do ambiente virtual, com os comandos da seção acima.
- **O acento aparece quebrado no Windows PowerShell 5.1.** Leia os arquivos com
  `Get-Content -Encoding UTF8`, ou peça ao Claude, que lê em UTF-8.
- **A transcrição repete texto ou escreve "Legendas pela comunidade Amara.org".** É o
  Whisper inventando texto sobre silêncio. O script pula a gravação muda e corta o
  silêncio longo do fim, e a análise marca os trechos que sobrarem.

## Licença

O código sai sob a licença MIT, com os termos em [LICENSE](LICENSE).

## In English

Two Claude Code skills that transcribe meeting, interview and class recordings on
your own computer with faster-whisper, and turn each one into a Markdown file with a
reviewed transcript, a structured analysis (real date, topic, participants,
timestamped agenda, decisions, open questions, tasks with owner and deadline,
insights, key quotes) and the full raw transcript at the end. The skill instructions
and the analysis are written in Brazilian Portuguese, and the speech language is set
with `WHISPER_IDIOMA` (`pt` by default, or `en`, `es`, `auto`).

To install, run `/plugin marketplace add biancaschuler/transcritor` and
`/plugin install transcritor@transcritor` inside Claude Code, or copy the folders
under `skills/` to `~/.claude/skills/`. Then ask Claude to get your machine ready for
transcription. The skill checks for Python 3.10+, ffmpeg and faster-whisper, explains
what each one does and installs what is missing after you say yes.

Transcription runs locally and the audio stays on your machine. Claude writes the
analysis, so the transcript text and the video frames go through Anthropic's servers
like any file Claude reads in a session.
