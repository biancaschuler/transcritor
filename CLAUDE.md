# Transcritor

Repositório público com duas skills do Claude Code, `transcricao` e
`temas-transcricoes`, distribuídas como plugin pelo `.claude-plugin/`.

## Regras para quem edita

- Tudo aqui é público. Nome de pessoa, empresa, contato ou projeto em exemplo é
  fictício e genérico (Fulana de Tal, Beltrano, Sicrano, Acme, Projeto Quasar), e
  nenhum dado de gravação real entra no repositório.
- Nenhum glossário entra no repositório, nem de exemplo. O glossário nasce das
  transcrições de cada usuário, e o pacote só leva o formato, em
  `skills/transcricao/references/formato-glossario.md`.
- Caminho de pasta sai de `TRANSCRITOR_PASTA` ou da pasta do usuário, e nunca de
  letra de disco ou nome de usuário fixos.
- As mensagens que os scripts imprimem ficam em ASCII, porque a skill lê os marcadores
  do stdout e o console do Windows nem sempre está em UTF-8. Comentário e docstring
  seguem em português normal.
- Se mudar um marcador do `transcrever.py` (`tipo=`, `AUDIO_MUDO=1`, `ERRO_FFMPEG=1`,
  `SILENCIO_10MIN=`) ou do `verificar_ambiente.py` (`PYTHON=`, `AMBIENTE_OK=`),
  atualize o SKILL.md junto.
- O `extrair_temas.py` lê o campo `**Tema:**` da análise, então mudar o formato dele
  em `regras-analise.md` pede mudar o script também.
- Antes de publicar uma versão nova, rode `claude plugin validate .` e suba o
  `version` de `.claude-plugin/plugin.json`, porque quem instalou só recebe a
  atualização quando a versão muda.
