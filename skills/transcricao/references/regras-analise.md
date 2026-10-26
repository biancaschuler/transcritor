# Regras de transcrição e análise

Você vai atuar como transcritor e organizador de conversas gravadas em áudio ou
vídeo.

A gravação costuma ser uma reunião de trabalho, uma entrevista, uma aula, uma
palestra ou uma mensagem de voz.

Sua principal tarefa é extrair o conteúdo falado com o máximo de fidelidade possível.

## Regras de transcrição

- A seção `# Transcrição` deve ser uma transcrição QUASE LITERAL da fala, palavra por palavra, e NÃO um resumo, paráfrase ou descrição do que foi dito ("X falou sobre Y"). O texto de cada fala fica muito próximo do áudio original.
- Organize por turno de fala. Cada bloco começa com o timestamp de início (`[HH:MM:SS]`) e o nome de quem fala, seguido do texto literal daquele turno, e pode juntar várias linhas seguidas da mesma pessoa.
- Transcreva apenas o que for compreensível.
- Não invente frases.
- Não complete raciocínios automaticamente.
- Não "melhore" o texto nem reescreva frases em linguagem mais formal ou organizada. Mantenha repetições, frases incompletas e a ordem das palavras como foram faladas.
- Preserve o sentido original das falas.
- Se algo estiver inaudível, use `[inaudível]`.
- Se houver dúvida sobre uma palavra, use `[incerto: palavra]`.
- Preserve mudanças importantes de tom, interrupções, hesitações e discordâncias quando isso alterar a interpretação.
- Pode remover vícios de linguagem sem importância ("tipo", "né", "aham") quando eles só poluírem a leitura, sem alterar o resto da frase nem reescrevê-la.
- Sempre que possível, mantenha a separação entre participantes.
- Se não souber o nome da pessoa, use `Pessoa 1`, `Pessoa 2` e assim por diante. Em vídeo, use os frames para achar o nome exibido na tela (ver o Passo 3 do SKILL.md). Em áudio puro, identifique só pelo que é dito, como nome citado, voz distinta e contexto da conversa. Se houver incerteza sobre qual nome corresponde a um trecho, marque `[interpretação]`, mas NÃO troque o texto literal por uma descrição.

## Glossário de nomes próprios

O glossário mora em `<pasta-base>/glossario.md`, ou no caminho de
`TRANSCRITOR_GLOSSARIO`. Ele guarda a grafia correta de empresa, projeto, pessoa e
termo recorrente, com as variantes erradas que o Whisper já produziu (campo
"ouvido como"). Ele não vem pronto. Na primeira análise que confirmar um nome
próprio, crie o arquivo no formato de `references/formato-glossario.md` e avise o
usuário na resposta final. Daí em diante o glossário cresce a cada gravação.

O glossário vale para todas as transcrições do usuário e é um **arquivo vivo**.
Consulte antes de cada análise e edite conforme ganhar e confirmar informação, ou
seja, adicione nome novo, promova `❓` para `✅` ao confirmar, corrija grafia e
propague a correção para as análises antigas. Ele não é lista fechada nem só de
leitura.

- **Consulte o glossário sempre** ao revisar a transcrição e a análise, e use a
  grafia canônica, marcada com ✅. Em vídeo, os frames são fonte adicional para
  confirmar a grafia do nome que aparece na tela. Quando a transcrição trouxer uma
  grafia listada em "ouvido como", troque pela canônica.
- O nome próprio que **não** está no glossário e que você **não** confirma com alta
  confiança, pelo contexto ou pelos frames, entra como `[incerto: <melhor palpite>]`.
  NUNCA "conserte" um nome truncado para um nome real plausível sem base, e prefira
  marcar incerteza a chutar.
- Em `# Informações gerais`, inclua a linha **"Nomes a confirmar:"** com os nomes
  próprios novos ou incertos da gravação, para o usuário validar e levar ao
  glossário. É assim que o glossário cresce.

## Censo de participantes (obrigatório)

O registro de pessoas serve para saber quem participa de cada assunto ao longo das
gravações, então em toda gravação de trabalho ele é censo, e não resumo do que cada
pessoa disse.

- **Registre TODAS as pessoas presentes**, mesmo quem não falou. Presença é dado. Um
  nome que aparece só no rótulo do Meet ou do Teams, na lista de participantes ou
  num bot de notas (como "Notetaker de Fulano") entra no censo.
- **Em vídeo, o frame é a fonte de verdade** para nome e presença. Cruze o que se
  ouve com o que se vê, porque o áudio erra grafia e o rótulo da tela não. Quando o
  frame padrão não bastar, tire frames extras. Se frame e áudio divergirem, vale o
  frame, e você registra a divergência.
- **Em áudio puro, a confirmação é fraca por natureza.** Prefira `[incerto: ...]` e
  cruze com o glossário. Se a mesma reunião tiver uma gravação de vídeo em
  `Finalizados`, use os frames dela como fonte de verdade para nome e presença, e
  cite qual frame confirmou.
- **Registre também quem é apenas citado**, numa lista separada de "mencionados, não
  presentes", com a mesma ficha.
- Para cada pessoa, preencha o máximo que a evidência permitir.
  - **Nome**, na grafia canônica, ou `[incerto: ...]` sem confirmação por frame ou glossário
  - **Função ou cargo**
  - **Organização**
  - **Área ou time**
  - **Como foi confirmado** (frame de tal timestamp, fala, glossário)
- Campo sem evidência fica `[não identificado]`. Não invente cargo nem área por
  plausibilidade, porque um nome sem função é melhor que uma função inventada.
- **Toda pessoa nova vai para o glossário**, com a mesma ficha, e não só para a
  análise. O glossário é a fonte única, e a análise é a ocorrência.
- A confirmação é **retroativa**. Quando um frame confirmar a grafia de alguém que
  aparecia como `[incerto: ...]` em análises antigas, corrija também os arquivos
  antigos e o glossário, e não só o atual.

## Regras do seu contexto

O projeto onde a skill roda pode ter regras próprias, como uma pasta extra para onde
copiar a análise, um campo a mais na ficha de cada pessoa ou um padrão de nome
diferente. Essas regras moram no `CLAUDE.md` do projeto ou no glossário, e valem por
cima destas quando as duas brigarem. Sem regra própria, vale o que está aqui.

## Identificação do contexto

Antes da análise, feche a data real.
- Identifique a data REAL da gravação sempre que possível.
- NÃO use automaticamente a data de criação do arquivo.
- Tente inferir a data pelas falas dos participantes, pelas referências temporais, pelo calendário mencionado, pelo contexto da conversa, pelas agendas e pelas referências a eventos. Em vídeo, valem também as datas exibidas na tela, os documentos compartilhados e os timestamps visíveis.

Se a data do arquivo, o metadado e as falas da reunião brigarem, priorize a data mais
consistente com o conteúdo da conversa.

Sem evidência suficiente, escreva `[não foi possível identificar a data real da gravação]`.

Identifique também estes dois pontos.
- O tema principal, que costuma ser um só. Se a conversa cobrir assuntos distintos
  e desconectados, como uma primeira metade sobre um projeto e a segunda sobre outro
  sem relação nenhuma, liste todos.
- Os participantes identificados.

Se alguma informação não estiver clara, escreva `[não identificado]`.

## Estrutura interna da análise

O arquivo `.md` final deve conter estas seções.

```
# Informações gerais
- **Data da gravação:** <data real, ou o marcador de data não identificada>
- **Tema:** <frase curta com o tema central>
- **Participantes:** <censo, com a lista de mencionados não presentes>
- **Estrutura do arquivo:** <só quando houver partes, ou quando a mídia for mensagem dentro de uma conversa>
- **Nomes a confirmar:** <nomes novos ou incertos desta gravação>

# Tema
<frase curta e direta com o tema central da conversa; se houver mais de um
tema desconectado entre si, liste cada um em uma linha própria>

# Transcrição

# Resumo objetivo

# Pautas discutidas
<detalhamento dos temas em pauta, em ordem cronológica, cada item com o timestamp
`[HH:MM:SS]` de quando entrou em discussão, como "Conflitos do time de pagamentos"; ver regra abaixo>

# Principais temas discutidos
<os temas macro tratados, como áreas, projetos, produtos e iniciativas (ex.: "Pagamentos")>

# Decisões tomadas

# Dúvidas abertas

# Tarefas
<tudo que ficou para ser feito depois da gravação, em ordem cronológica, cada
item com checkbox e timestamp `[HH:MM:SS]`; ver regra abaixo>

# Insights relevantes

# Frases importantes

# Anexo, transcrição bruta
<conteúdo integral do(s) `.transcript.txt`, em bloco de código; ver regra abaixo>
```

O campo `**Tema:**` sai sempre nesse formato, em negrito e com dois pontos, porque a
skill `temas-transcricoes` lê o tema dele.

## Anexo com a transcrição bruta (obrigatório)

Toda análise termina com a seção `# Anexo, transcrição bruta`, e ela carrega o
**conteúdo integral** do `.transcript.txt` gerado pelo faster-whisper, dentro de um
bloco de código.

- **Integral quer dizer integral.** Nada de cortar silêncio, tirar alucinação do
  modelo, resumir ou reordenar. O cabeçalho de metadado do arquivo, com modelo,
  precisão, versão da biblioteca, data e tipo, entra junto.
- **Uma subseção por arquivo de origem.** Se a gravação tem mais de um arquivo
  (partes em sequência, gravação paralela do mesmo encontro, cauda recuperada de um
  segundo gravador), cada bruto entra em `## <nome do arquivo>`, na ordem
  cronológica.
- **O anexo é diferente da seção `# Transcrição`.** Aquela é a versão revisada, com
  turno de fala, nome de quem fala e marcação de incerteza. O anexo é a saída crua
  da máquina, e serve de fonte para conferir a revisão depois.
- **Vale para todas as cópias.** Se o seu contexto copia a análise para outro lugar,
  a cópia leva o anexo também.
- **Ordem de operação.** Cole o anexo **antes** de apagar o `.transcript.txt`. O bruto
  não volta sem rodar a transcrição de novo, que pode levar horas.

## Pautas discutidas (com timestamp)

A seção `# Pautas discutidas` é o **detalhamento dos temas** tratados na gravação, em
ordem **cronológica**, cada item com o timestamp `[HH:MM:SS]` de quando o assunto
entrou em discussão. Cada pauta é um recorte específico de um dos temas macro de
`# Principais temas discutidos`.

- Cada item segue o formato `` - `[HH:MM:SS]` <pauta ou assunto em uma frase curta> ``,
  na ordem em que os assuntos aparecem na conversa, com o timestamp de **início** de
  cada um.
- Em `# Principais temas discutidos` ficam os **temas** macro (áreas, projetos,
  produtos, iniciativas), como *Pagamentos*. Aqui fica o **detalhamento** de cada
  tema, com timestamp, como *Conflitos do time de pagamentos* e *Prazo da
  entrega de pagamentos*.
- A seção é **obrigatória em TODA gravação**, inclusive nas que não são reunião de
  trabalho. Adapte a linguagem das pautas ao conteúdo (numa aula, por exemplo, os
  tópicos apresentados), mas sempre com o timestamp.

## Tarefas (com timestamp e checkbox)

Tarefa é qualquer coisa que alguém precisa fazer **depois** da gravação, fora da
conversa. É o que sobra como trabalho quando a chamada cai. Isso separa a tarefa da
decisão, que já foi resolvida ali, e da dúvida aberta, que ninguém se comprometeu a
resolver.

- Cada item segue este formato.

  `` - [ ] `[HH:MM:SS]` <Dono> · <Prazo ou gatilho> · <o que precisa ser feito> · explícita|inferida ``

- A ordem é **cronológica**, pelo timestamp do momento em que a tarefa apareceu na
  conversa.
- Todo item nasce com o checkbox vazio, `- [ ]`. Se a ação **já foi executada durante
  a própria gravação** (a pessoa mandou o link na hora, criou o card, fez a
  ligação), registre mesmo assim e marque `- [x]`.
- **Dono** é quem ficou com a tarefa, na grafia canônica do glossário. Sem dono
  definido, use `[não identificado]`, e não invente responsável por plausibilidade.
- **Prazo ou gatilho** só entra quando a conversa combinou de forma explícita. Sem
  combinação explícita, escreva `sem prazo`.
- Marque **explícita** quando a tarefa foi dita com todas as letras e **inferida**
  quando você deduziu do contexto. Nesse segundo caso, o item também leva
  `[interpretação]`.
- A seção é **obrigatória em TODA gravação.** Sem nenhuma tarefa, escreva
  `[nenhuma tarefa identificada]` em vez de omitir a seção.

### Tipos de tarefa

- **Compromisso explícito com dono.** Alguém diz o que vai fazer, em primeira pessoa.
  "Eu mando o documento atualizado até quinta." É o caso mais fácil.
- **Compromisso atribuído a outra pessoa.** Alguém delega, e o outro aceita ou fica
  em silêncio. "O Sicrano fecha a planilha." Vale registrar mesmo quando a
  pessoa delegada não estava na chamada.
- **Tarefa órfã.** O grupo reconhece que algo precisa ser feito e ninguém assume.
  "Alguém tem que falar com o jurídico sobre isso." É o tipo mais valioso de capturar
  e o que mais se perde, porque não tem dono para lembrar. Ele conversa direto com a
  instrução de destacar os "pontos sem dono claro" das reuniões de trabalho.
- **Entrega de artefato.** Documento, planilha, apresentação, relatório, ambiente
  configurado. A tarefa é o artefato prometido, e não a conversa sobre ele.
- **Busca de informação.** Perguntar para alguém de fora, levantar dado, checar
  histórico, confirmar número com quem tem o dado. Vira tarefa quando alguém precisa sair
  da reunião e ir atrás.
- **Validação ou aprovação.** Revisar texto, aprovar uma proposta, homologar uma
  entrega. Tem dono e tem quem espera o resultado.
- **Agendamento e convocação.** Marcar a próxima conversa, chamar alguém específico
  para ela, reservar horário com alguém de fora.
- **Desbloqueio operacional.** Acesso a sistema, licença, credencial, ambiente,
  permissão, contrato. Costuma aparecer de passagem e sumir.
- **Decisão adiada.** O grupo escolhe não decidir agora. A tarefa é decidir, com um
  prazo ou um gatilho. Ela entra como trabalho agendado e fica fora de Decisões e de
  Dúvidas.
- **Tarefa condicional.** Depende de um evento. "Se aprovarem o orçamento, a gente
  começa a obra." O gatilho faz parte da tarefa e entra no campo de prazo.
- **Tarefa recorrente.** É combinação de processo, e não item único. "Mandar o
  relatório toda segunda de manhã."
- **Cobrança de tarefa antiga.** Alguém retoma uma pendência de reunião anterior,
  cumprida ou não. Serve para fechar o ciclo e para cruzar com as análises passadas.

### Fora de gravação de trabalho

Numa gravação que não é reunião de trabalho, como uma aula ou uma conversa pessoal,
a tarefa continua existindo com outra cara, como um exercício combinado, uma leitura
ou uma conversa a ter com alguém. O formato é o mesmo, com a linguagem adaptada,
igual à regra de `# Pautas discutidas`.

### O que não é tarefa

Ideia solta, hipótese, desabafo e vontade sem compromisso ("seria bom um dia a gente
organizar isso") não são tarefa. Se não sobrou trabalho depois que a chamada caiu,
não há tarefa.

## Regras específicas

Se for entrevista, destaque estes pontos.
- dificuldades concretas que a pessoa relata
- comportamentos concretos
- contradições
- linguagem usada pela pessoa
- sinais emocionais
- momentos de hesitação

Se for reunião de trabalho, destaque estes pontos.
- conflitos de prioridade
- dependências entre pessoas ou times
- riscos
- decisões implícitas
- desalinhamentos
- pontos sem dono claro

## Importante

- Não transforme tudo em linguagem corporativa.
- Não suavize conflitos.
- Não gere insights genéricos.
- Não escreva como ata formal.
- Prefira precisão a parecer organizado.
- Se algo for interpretação sua e não estiver explícito na fala, marque `[interpretação]`.
- O arquivo de análise SEMPRE traz o TEMA, tanto no campo `**Tema:**` de `# Informações gerais` quanto na seção própria `# Tema`. Nunca omita o tema. Se ele não estiver claro, use `[não identificado]`, e se a conversa tratar de mais de um tema desconectado, liste todos em vez de escolher um.

## Curso, aula e palestra

Curso, aula e palestra assistida seguem o mesmo fluxo de qualquer gravação. Entram
pela `Entrada` e fecham numa subpasta de `Finalizados`.

O que muda é a seção `# Transcrição`. Em vez da fala quase literal, ela traz um
resumo detalhado por tópico, com o timestamp de início de cada tópico, e abre com uma
nota que explica a troca. As outras seções continuam completas, e as de decisão e
tarefa costumam ficar vazias, porque aula não é reunião de trabalho. O anexo com a
transcrição bruta continua obrigatório.

Gravação em outra língua pede `WHISPER_IDIOMA` com o código dela, ou `auto`. Se a
palestra em outra língua já saiu transcrita como `pt`, ela vira resumo temático,
porque esse texto do Whisper não serve nem como literal nem como tradução.

## Múltiplas reuniões numa mesma gravação

Se uma única gravação contiver mais de uma reunião distinta, como duas sessões
gravadas em sequência no mesmo arquivo, cada reunião ganha o **próprio arquivo `.md`
de análise**, e nunca se misturam duas reuniões num `.md` só.

- Os arquivos levam sufixo numérico, `<nome-base>_1.md`, `<nome-base>_2.md` e assim
  por diante, na ordem cronológica em que as reuniões aparecem.
- A mídia original vai inteira para a pasta final, sem corte, porque um único
  arquivo contém as duas reuniões.
- A pasta final `Finalizados/<nome-base>/` guarda a mídia original e os `.md`
  numerados.
- Cada `.md` tem o próprio cabeçalho (data, participantes, tema) e uma análise
  completa só da reunião que cobre.

## Nome do arquivo e da pasta

O `.md` final e a pasta criada em `Finalizados` usam **exatamente** o mesmo nome-base
da mídia original, sem extensão. O nome não ganha data, prefixo, sufixo, tradução,
resumo do tema nem outra variação, mesmo quando a data ou o tema reais identificados
na análise diferem do nome do arquivo. A exceção é a gravação com várias reuniões,
da seção acima.

### Mídia de app de conversa

A regra completa está no SKILL.md. A pasta é da conversa, e não da gravação, então a
mensagem de voz e o vídeo exportados de WhatsApp ou Telegram fecham em
`Finalizados/<App> <Contato>/`, com a mídia e o `.md` de cada mensagem lado a lado.

O nome do arquivo não muda, e cada mídia continua com o `.md` dela. A análise de uma
mensagem nunca vira apêndice de outra.

Na análise, o que muda é o campo `**Estrutura do arquivo:**` de
`# Informações gerais`, que situa a mensagem dentro do fio, com quantas mensagens a
conversa tem e o período que ela cobre. Antes de concluir qualquer coisa sobre uma
mensagem solta, leia as vizinhas e o texto exportado da conversa, porque a mensagem
seguinte costuma responder a anterior.

## Resposta final obrigatória

Depois de concluir tudo:
- NÃO escreva a transcrição no chat.
- NÃO escreva a análise no chat.
- NÃO cole resumos no chat.
- NÃO mostre prévias ou trechos parciais.
- NÃO interrompa o processamento para explicar progresso.
- Responda com algo equivalente a "Transcrição e análise concluídas com sucesso." e, em seguida, uma lista numerada com TODOS os termos e nomes marcados como `[incerto: ...]` ou `[interpretação]` na transcrição e na análise, mesmo os que já estão na linha "Nomes a confirmar:". Para cada item, dê um contexto curto (o trecho ou timestamp onde aparece, o que parece ser, o seu palpite) para o usuário confirmar ou corrigir. Se não houver nenhum termo incerto, diga isso com todas as letras.
