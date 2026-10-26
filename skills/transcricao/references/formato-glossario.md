# Formato e uso do glossário

O glossário é um arquivo `glossario.md` que mora na pasta-base, ou no caminho de
`TRANSCRITOR_GLOSSARIO`. Ele não vem pronto e não existe modelo com nomes. A skill
cria o arquivo na primeira análise que confirmar um nome próprio e acrescenta nomes a
cada gravação, então o conteúdo sai das transcrições de cada usuário e só vale para
elas.

## Para que serve

O glossário tem dois usos.

1. **Orientar o Whisper.** O script de transcrição lê os nomes confirmados e manda
   para o modelo no `initial_prompt`, o que puxa a grafia certa de nome próprio.
2. **Revisar a análise.** Na revisão, a skill troca a grafia errada pela canônica e
   marca como `[incerto: ...]` o nome que não está no glossário e que ela não
   conseguiu confirmar.

## Formato de cada linha

Cada nome é um item de lista numa linha só, com a marca, o nome canônico em negrito e
o que se sabe dele.

```
- ✅ **<nome canônico>**. <quem ou o que é>. Ouvido como <variante>, <variante>.
- ❓ **<nome a confirmar>**. <onde apareceu e o que falta confirmar>.
```

- ✅ marca o nome confirmado por frame, fala, documento ou pelo próprio usuário, e ❓
  marca o nome a confirmar.
- "Ouvido como" lista as grafias erradas que o Whisper já produziu para aquele nome.
- A linha de pessoa leva a ficha do censo de participantes de `regras-analise.md`,
  com função ou cargo, organização e lado (cliente ou fornecedor), área ou time,
  frente de trabalho e como o nome foi confirmado. Campo sem evidência fica
  `[não identificado]`.
- Títulos `##` podem separar o arquivo por projeto, organização ou tipo de nome. Eles
  só organizam a leitura e não mudam o que o script lê.

## Como o script lê o arquivo

O script usa só as linhas que começam com `- ` e têm ✅, e de cada uma pega o
primeiro trecho em negrito. A linha com ❓ fica de fora, para não espalhar grafia
chutada. O `initial_prompt` do Whisper tem orçamento curto, perto de 900 caracteres,
e o corte segue a ordem do arquivo, por isso os nomes que mais aparecem ficam no topo.

## Como o glossário cresce

- Na primeira análise que confirmar um nome próprio, a skill cria o arquivo neste
  formato e avisa o usuário na resposta final.
- Cada pessoa, empresa, projeto ou termo novo entra com ✅ ou ❓, conforme a
  evidência da gravação.
- Quando uma gravação confirma um nome marcado com ❓, a marca vira ✅, e a correção
  vale também para as análises antigas em que o nome aparecia como `[incerto: ...]`.
- A linha "Nomes a confirmar:" de cada análise lista o que o usuário ainda precisa
  validar.
