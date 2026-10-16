# ASD-STE100 PT-BR: Português Técnico Simplificado para respostas de IA

Uma skill para Claude que reescreve português denso e ambíguo seguindo a disciplina da [ASD-STE100 Simplified Technical English](https://www.asd-ste100.org/) (STE), a norma de linguagem controlada que a indústria aeroespacial e de defesa criou para que instruções de manutenção de aeronaves não possam ser lidas de forma errada.

A skill usa a mesma disciplina para outro leitor: **uma pessoa que lê a resposta de uma IA**. Respostas de IA costumam vir com ruído: introduções vazias, resumos do que já foi dito, informação que ninguém pediu, rodeios empilhados e vícios de linguagem repetidos. A skill entrega a resposta de forma direta, sem ambiguidade e sem ruído.

Este projeto é uma adaptação para o português do Brasil da skill [danyuchn/asd-ste100-skill](https://github.com/danyuchn/asd-ste100-skill), de Dustin Yuchen Teng, publicada sob a licença MIT.

> **Não é uma norma oficial.** A ASD-STE100 só define o inglês. As regras para o português são uma adaptação deste projeto. A ASD não certifica nem endossa este projeto.

## Por que STE, e por que para respostas de IA

A STE existe porque uma instrução mal interpretada em uma aeronave pode matar pessoas, e os leitores eram muitas vezes técnicos não nativos em inglês, sem um autor para tirar dúvidas. A solução da norma: um significado por palavra, voz ativa, tempos simples, uma instrução por frase, frases curtas, nenhuma palavra omitida.

Quem lê uma resposta de IA está em uma posição parecida. A resposta precisa ser entendida na primeira leitura, sem ida e volta para perguntar "você quis dizer X ou Y?". As mesmas regras que impedem um mecânico de ler errado um valor de torque deixam uma resposta de IA fácil de ler. A skill acrescenta uma lista de ruídos típicos de IA que a STE original não cobre, porque a norma foi feita para manuais, e não para conversas.

## Antes / depois

| Antes | Depois |
|---|---|
| "Esta ferramenta vai estar tentando sincronizar o estado entre os diversos backends que tiverem sido configurados, e caso seja detectado um conflito ela poderá resolver o mesmo automaticamente dependendo da estratégia que estiver definida, ou do contrário irá sinalizar o conflito para revisão manual." | "A ferramenta tenta sincronizar o estado entre os backends configurados. Se a ferramenta encontra um conflito, ela lê a estratégia configurada. Se a estratégia permite resolução automática, a ferramenta pode resolver o conflito sem um usuário. Se a ferramenta não resolve o conflito, ela envia o conflito para revisão manual." |
| "Ótima pergunta! Vou te explicar. Basicamente, o erro acontece porque a variável não foi inicializada. Em resumo, você precisa inicializar a variável antes de usar. Se quiser, posso ajudar com mais alguma coisa!" | "O erro acontece porque a variável não foi inicializada. Inicialize a variável antes de usar." |
| "Pode ter ocorrido um erro durante o processamento da sua solicitação devido a uma possível incompatibilidade no formato de dados esperado, o que pode ser causado por uma versão desatualizada do cliente." | "Sua solicitação pode ter falhado. A causa pode ser um formato de dados diferente do formato que o servidor espera. Um cliente desatualizado pode causar essa diferença. Verifique a versão do seu cliente." |

Mais exemplos em [`examples/antes-depois.md`](examples/antes-depois.md).

## O que muda em relação à versão em inglês

O português tem problemas que o inglês não tem, e vice-versa. As principais adaptações:

- **Gerundismo** ("vou estar enviando") entra no lugar das formas em "-ing".
- **Gíria corporativa e estrangeirismo** ("dar um start", "startar", "endereçar") entram no lugar dos phrasal verbs, que quase não existem em português.
- **Pretérito perfeito composto** ("tem feito") é tratado com cuidado especial. Em português ele indica ação repetida, e não ação concluída como o present perfect. Traduções do inglês erram muito aqui.
- **Cadeias de "de"** ("válvula de entrada da bomba de combustível de alta pressão") entram no lugar dos noun clusters.
- **Regras novas:** "o mesmo" como pronome, possessivo "seu" ambíguo, sujeito oculto ambíguo, "deve" (obrigação ou probabilidade) e "pode" (permissão ou possibilidade), e uma só forma de imperativo por documento.

A tabela completa de decisões está em [`references/regras-de-escrita.md`](references/regras-de-escrita.md).

## O que a skill faz

1. Escolhe um modo. **Estrito** cobre procedimentos, passo a passo e mensagens de erro. **Estilo STE** cobre respostas de conversa, explicações, READMEs e descrições de PR, e é o modo padrão para responder ao usuário. O Estilo STE mantém a disciplina das frases, mas não impõe um vocabulário fixo.
2. Lê o texto em português para entender o sentido.
3. Marca cada violação e cada ruído de IA (introdução vazia, resumo repetido, oferta genérica, formatação decorativa, informação não pedida), frase por frase.
4. Reescreve cada frase marcada sem perder nenhum fato, condição ou limite de escopo. Se uma forma mais curta perderia uma precisão necessária, a skill mantém a forma longa e sinaliza o conflito.
5. Entrega só o texto reescrito, sem introdução, anúncio de modo ou resumo das mudanças, mais uma linha `Mantido:` quando deixou algo sem simplificar de propósito.

Peça o raciocínio ("mostre o diff", "quais regras ele quebrou") e a skill entrega uma tabela antes/depois com o nome de cada regra.

## O linter

`scripts/ste-lint-pt.py` é um linter determinístico, só com a biblioteca padrão do Python 3. Ele é uma adaptação do `ste-lint.py` original: o núcleo (leitura de Markdown, tabelas, listas, contagem de frases, linha de comando) é o mesmo, e as regras de idioma são novas.

```bash
python3 scripts/ste-lint-pt.py ARQUIVO.md
echo "Vou estar enviando o relatório; ok." | python3 scripts/ste-lint-pt.py --json
python3 scripts/ste-lint-pt.py --baseline 10 --disable voz-passiva ARQUIVO.md
python3 scripts/ste-lint-pt.py --selftest
```

Regras **graves** (falham a execução): `ponto-e-virgula`, `gerundismo`, `jargao-corporativo`, `adjetivo-de-marketing`, `verbo-suporte`, `frase-longa`, `rotacao-de-sinonimos`, `conjuncao-solta`.

Regras de **recomendação** (nunca falham a execução): `voz-passiva`, `tempo-composto`, `o-mesmo-pronome`.

O linter nunca marca rodeios nem modalidade. "Pode ter falhado", "pode estar reiniciando" e "o servidor teria falhado" passam sem alertas, e o `--selftest` confirma isso.

Limites conhecidos: o linter usa regex, não análise sintática. Ele não verifica cadeias de "de", sujeito oculto, possessivo ambíguo nem o duplo sentido de "deve" e "pode". A detecção de voz passiva e de tempo composto usa uma lista de exceções para palavras em "-ado/-ido" que costumam ser substantivos ou adjetivos ("cuidado", "resultado", "adequado"). Por isso, a detecção tem falsos positivos e falsos negativos. A passiva sintética ("remove-se o arquivo") não é detectada, porque a regex não separa a passiva de imperativos como "certifique-se". O linter não compara o original com a reescrita e não prova que o sentido foi preservado. Zero violações significa só que as verificações configuradas não encontraram problemas.

A prosa do próprio repositório não passa limpa: as tabelas citam os padrões que proíbem. Rode `python3 scripts/ste-lint-pt.py --baseline 100 SKILL.md` e leia os achados como exemplos, e não como defeitos.

O arquivo `examples/casos-limite-linter.md` é inválido de propósito. Rode `python3 scripts/ste-lint-pt.py examples/casos-limite-linter.md` para confirmar que o linter informa os dois achados esperados.

## O dicionário oficial

A skill **não** reproduz o dicionário oficial da ASD, de cerca de 900 palavras. A norma é gratuita para obter, mas não é livre para redistribuir: a Issue 9 só permite reprodução com autorização escrita da ASD ou para oito categorias de organizações às quais este projeto não pertence. O dicionário também é só em inglês. A skill aplica o *princípio* (a palavra mais simples disponível, usada sempre do mesmo jeito) em vez de verificar uma lista fixa de palavras.

## Instalação

### Instalação rápida (npx skills)

Na raiz do seu projeto:

```bash
npx skills add 21fernandinhow/asd-ste100-pt-br-skill
```

### Clone

```bash
git clone https://github.com/21fernandinhow/asd-ste100-pt-br-skill ~/.claude/skills/asd-ste100-pt-br
```

O clone em `~/.claude/skills/` deixa a skill disponível em todos os projetos do Claude Code.

## Uso

Com a skill instalada, o Claude aplica as regras quando escreve respostas em português para você. Você também pode pedir para simplificar um texto:

```
Deixe esta resposta mais legível
Tire a enrolação deste texto
Aplique a STE100 a esta explicação
```

Uma skill só carrega quando o Claude acha que ela combina com o pedido. Para garantir o estilo em todas as respostas, acrescente uma linha nas suas preferências do claude.ai ou no `~/.claude/CLAUDE.md`: *"Ao me responder em português, use sempre a skill asd-ste100-pt-br."*

Você recebe só o texto reescrito. Para ver as regras aplicadas, acrescente "mostre o diff" ou "explique as mudanças".

## Escopo

Feita para: respostas de IA em conversa, explicações, resumos, relatórios, mensagens de erro e instruções. Ou seja, qualquer texto em português que uma pessoa precisa ler e entender na primeira leitura.

Não é para: texto criativo, de marketing ou qualquer texto em que voz e nuance são o objetivo. A STE é seca e literal de propósito.

Um limite importante: a skill corrige a forma de um texto, e não o conteúdo. Um parágrafo sem nada a dizer sai curto, limpo e ainda vazio.

## Outros idiomas

- **Inglês (original):** [danyuchn/asd-ste100-skill](https://github.com/danyuchn/asd-ste100-skill)
- **Hebraico:** [g4lb/asd-ste100-hebrew-skill](https://github.com/g4lb/asd-ste100-hebrew-skill)

## Fontes

- [ASD-STE100: site oficial](https://www.asd-ste100.org/)
- [ASD-STE100: About STE](https://www.asd-ste100.org/about_STE.html)
- [ASD Europe: Simplified Technical English](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)
- [Simplified Technical English: Wikipedia](https://en.wikipedia.org/wiki/Simplified_Technical_English)
- [TechScribe: ASD-STE100 Simplified Technical English](https://www.techscribe.co.uk/techw/asd-simplified-technical-english.htm)

## Licença

MIT. Veja [LICENSE](LICENSE). O arquivo mantém o aviso de copyright do projeto original, como a licença exige.
