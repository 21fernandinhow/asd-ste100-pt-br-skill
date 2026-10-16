# Regras de escrita da ASD-STE100: resumo, fontes e adaptação ao português

Este arquivo resume a descrição pública e oficial da ASD-STE100 (Simplified Technical English). Ele parafraseia as *categorias* de regras. Ele não reproduz o texto da norma nem o dicionário de cerca de 900 palavras. Para o documento oficial, peça o download gratuito no site oficial.

A segunda parte explica as decisões de adaptação para o português do Brasil. Essas decisões são deste projeto, e não da ASD.

## O que é a ASD-STE100

A ASD-STE100 é uma linguagem natural controlada. A primeira versão saiu em 1986 (como documento AECMA PSC-85-16598), publicada pela organização que hoje se chama ASD (AeroSpace and Defence Industries Association of Europe). A norma nasceu a pedido de companhias aéreas europeias, com equipes em grande parte não nativas em inglês. Essas empresas precisavam de documentação de manutenção que não pudesse ser lida de forma errada, porque uma instrução mal interpretada em uma aeronave pode matar pessoas. O Simplified Technical English Maintenance Group (STEMG) mantém a norma. O download é gratuito desde a Issue 6 (2013). A edição atual é a Issue 9 (janeiro de 2025).

## Estrutura

- **53 regras de escrita em 9 seções**: escolha de palavras, gramática, estrutura de frase e estilo.
- **Um dicionário** de cerca de 900 palavras aprovadas, cada uma com um só significado e uma só classe gramatical, mais cerca de 1.200 palavras a evitar, com sugestões de substituição.
- **Uma permissão de terminologia**: organizações podem definir um dicionário próprio de substantivos e verbos técnicos aprovados, além das 900 palavras base, para o vocabulário do domínio.

## Categorias de regras (paráfrase)

**Escolha de palavras**
- Use palavras aprovadas só no significado e na classe gramatical aprovados.
- Cada palavra tem um só significado. Não dependa do contexto para escolher entre vários sentidos de uma palavra.
- Prefira a palavra mais simples, curta e comum a um sinônimo formal ou raro.
- Use um verbo aprovado para uma ação, e não um substantivo derivado desse verbo (Regra 3.7).
- Não forme phrasal verbs (verbo + preposição) (Regra 9.3). O sentido deles não é previsível pelas partes.

**Formas verbais**
- Formas permitidas: infinitivo, imperativo, presente simples, passado simples, futuro simples e particípio usado só como adjetivo.
- Sem present perfect, past perfect ou outras construções compostas.
- Formas em "-ing" só são permitidas como substantivo técnico ou parte de um.

**Voz**
- Voz ativa obrigatória em procedimentos e instruções.
- Voz passiva só em texto descritivo, e só quando o agente da ação é desconhecido ou irrelevante para o leitor.

**Estrutura da frase**
- Uma instrução por frase.
- No máximo cerca de 20 palavras por frase em procedimentos e instruções. No máximo cerca de 25 em texto descritivo.
- Não omita partes da frase (verbo, sujeito, artigo) só para encurtar. A norma avisa que isso cria ambiguidade.
- Cadeias de substantivos usados como modificador ficam limitadas a 3 palavras.
- Ponto e vírgula não é permitido (Regra 8.1). Todos os outros sinais de pontuação padrão, incluindo o travessão, continuam permitidos.

**Parágrafo e documento**
- Um assunto por parágrafo.
- No máximo cerca de 6 frases por parágrafo.
- Use listas verticais (numeradas ou com marcadores) para sequências, condições ou enumerações complexas.

**Instruções de segurança**
- Instruções críticas para a segurança começam com um comando ou uma condição clara. Não esconda a instrução no meio da frase.

## Adaptação para o português do Brasil

A ASD-STE100 só define o inglês. Não existe norma oficial equivalente para o português. As decisões abaixo são deste projeto.

| Regra da STE | Como a adaptação trata em português | Motivo |
|---|---|---|
| Phrasal verbs (9.3) | Trocada pela proibição de gíria corporativa e estrangeirismo desnecessário ("dar um start", "dar um ping", "startar", "performar", "endereçar") | O português quase não tem phrasal verbs. O problema equivalente é o jargão de escritório, que um leitor não nativo ou um tradutor automático interpreta mal. |
| Present perfect | Evitar pretérito perfeito composto ("tem feito") e mais-que-perfeito composto ("tinha feito") | O pretérito perfeito composto em português indica ação repetida ou contínua, e não ação concluída. Traduções do inglês erram aqui com frequência. |
| Formas em "-ing" | Proibição do gerundismo ("vou estar enviando") | É o uso do gerúndio que mais gera ruído em português. O gerúndio em si é permitido ("o processo está rodando"). "Pode estar rodando" é modalidade e também é permitido. |
| Noun clusters (3 palavras) | Limite de 3 substantivos ligados por "de/da/do" | O português não empilha substantivos como o inglês. O equivalente é a cadeia de complementos com "de". |
| Omissão de partes da frase | Inclui o sujeito oculto ambíguo | O português permite sujeito oculto. Em instruções, o sujeito oculto pode deixar dúvida sobre quem age. |
| Um significado por palavra | Inclui "deve" (obrigação ou probabilidade) e "pode" (permissão ou possibilidade) | São as duas palavras de modalidade mais ambíguas do português técnico. A skill sinaliza a dúvida em vez de escolher um sentido. |
| (sem equivalente) | Proibição de "o mesmo" como pronome e cuidado com o possessivo "seu" | Problemas próprios do português: "o mesmo" burocrático e "seu" que pode se referir a "você" ou a uma terceira pessoa. |
| (sem equivalente) | Uma forma de imperativo por documento | Procedimentos em português alternam imperativo ("Abra") e infinitivo ("Abrir"). A mistura parece mudança de tipo de instrução. |
| Limites de 20 e 25 palavras | Mantidos | Um texto em português costuma ter mais palavras que o mesmo texto em inglês, por causa de artigos e preposições. O limite fica, portanto, um pouco mais exigente. O projeto preferiu manter os números da norma a inventar números novos. |

## Por que esta skill usa a STE para respostas de IA

A STE foi criada para eliminar a ambiguidade para um leitor que não pode fazer uma pergunta de volta: um técnico na pista, com um manual na mão e sem o autor por perto. Quem lê uma resposta de IA está numa posição parecida. A pessoa quer entender a resposta na primeira leitura, sem precisar perguntar o que uma frase ambígua quer dizer. As mesmas regras que protegem um mecânico de ler errado um valor de torque protegem o leitor de ler errado uma resposta.

A STE não trata do ruído típico de conversa com IA (introduções vazias, resumos repetidos, ofertas genéricas, formatação decorativa, informação não pedida), porque a norma foi feita para manuais. Por isso, a skill acrescenta a seção "Ruído de IA". Essa seção é uma regra deste projeto, e não da norma.

## Fontes

- [ASD-STE100: site oficial](https://www.asd-ste100.org/)
- [ASD-STE100: About STE](https://www.asd-ste100.org/about_STE.html)
- [ASD Europe: Simplified Technical English](https://www.asd-europe.org/standards-specifications/simplified-technical-english/)
- [Simplified Technical English: Wikipedia](https://en.wikipedia.org/wiki/Simplified_Technical_English)
- [TechScribe: ASD-STE100 Simplified Technical English](https://www.techscribe.co.uk/techw/asd-simplified-technical-english.htm)
- [SKYbrary: Simplified Technical English (STE)](https://skybrary.aero/articles/simplified-technical-english-ste)
- [danyuchn/asd-ste100-skill](https://github.com/danyuchn/asd-ste100-skill): a skill original em inglês, base deste projeto.
