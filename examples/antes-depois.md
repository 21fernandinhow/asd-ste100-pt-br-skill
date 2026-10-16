# Exemplos antes / depois

## Parte 1: exemplos das regras da STE, em português

Estes exemplos ilustram regras reais da ASD-STE100, adaptadas para o português. São ilustrações parafraseadas, e não citações da norma (que é só em inglês).

| Regra | Antes | Depois | Por quê |
|---|---|---|---|
| Um significado por palavra | "Verifique o sistema." / "Confira as conexões." / "Valide o recebimento." | "Verifique o sistema." / "Verifique as conexões." / "Verifique o recebimento." | Três quase sinônimos obrigam o leitor a adivinhar se a ação é a mesma. |
| Uma classe gramatical por palavra | "Controle remoto: controle o volume." | "Use o controle remoto para ajustar o volume." | "Controle" aparece como substantivo e como verbo na mesma linha. Use cada palavra em uma só classe gramatical. |
| Sentido preciso do verbo | "Siga as instruções de segurança." | "Obedeça às instruções de segurança." | "Seguir" pode significar "vir depois" ou "obedecer". A STE escolhe o verbo sem ambiguidade. |
| Tempo simples | "Temos recebido os relatórios técnicos da sede." (sentido pretendido: recebemos uma vez) | "Recebemos os relatórios técnicos da sede." | Em português, "temos recebido" indica recebimento repetido. Se o autor quis dizer "recebemos", a forma composta muda o fato. |
| Verbo, não substantivo | "Realize uma inspeção do filtro." | "Inspecione o filtro." | O substantivo esconde a ação e acrescenta um verbo-suporte sem significado. |
| Sem gerundismo | "Vamos estar enviando o técnico." | "Vamos enviar o técnico." | "Ir + estar + gerúndio" não acrescenta informação e deixa o tempo da ação vago. |

## Parte 2: aplicado a textos gerados por IA

Estes são exemplos originais, criados para o uso desta skill: reescrever texto gerado por IA para que uma pessoa consiga ler o texto sem ambiguidade e sem ruído. Os exemplos são ilustrações, e não citações de um sistema real.

As contagens de palavras abaixo usam tokens separados por espaço (`text.split()`), sem contar a pontuação separadamente. Outro tokenizador vai dar outro número.

### Exemplo A: descrição de ferramenta

**Antes:**
> Esta ferramenta vai estar tentando sincronizar o estado entre os diversos backends que tiverem sido configurados, e caso seja detectado um conflito ela poderá resolver o mesmo automaticamente dependendo da estratégia que estiver definida, ou do contrário irá sinalizar o conflito para revisão manual.

**Violações marcadas:**
- Gerundismo ("vai estar tentando").
- Voz passiva sem agente ("seja detectado").
- Tempo composto na oração relativa ("tiverem sido configurados").
- "O mesmo" como pronome ("resolver o mesmo").
- Duas instruções na mesma frase (sincronizar + resolver/sinalizar).
- 44 palavras, muito acima do limite de 25 para descrições.

Observe o que *não* foi marcado: "tentando" e "poderá resolver". São rodeios, e não violações. A ferramenta não promete sucesso, e a reescrita também não pode prometer.

**Depois:**
> A ferramenta tenta sincronizar o estado entre os backends configurados. Se a ferramenta encontra um conflito, ela lê a estratégia configurada. Se a estratégia permite resolução automática, a ferramenta pode resolver o conflito sem um usuário. Se a ferramenta não resolve o conflito, ela envia o conflito para revisão manual.

A última frase depende de o conflito ter sido resolvido ou não, e não do que a estratégia permite. Era isso que "do contrário" queria dizer no original: a alternativa cobre também o caso em que a resolução era permitida, mas não aconteceu.

### Exemplo B: mensagem de erro

**Antes:**
> Pode ter ocorrido um erro durante o processamento da sua solicitação devido a uma possível incompatibilidade no formato de dados esperado, o que pode ser causado por uma versão desatualizada do cliente.

**Violações marcadas:**
- Uma frase com três afirmações separadas (houve um erro, há uma incompatibilidade de formato, há uma versão de cliente).
- Nominalização ("durante o processamento da sua solicitação").
- 32 palavras, acima do limite para descrições.

Não marcado: "pode ter ocorrido" e "pode ser causado". Quem escreve a mensagem é um sistema que não sabe o que deu errado. Os dois rodeios descrevem essa incerteza com precisão.

**Depois:**
> Sua solicitação pode ter falhado. A causa pode ser um formato de dados diferente do formato que o servidor espera. Um cliente desatualizado pode causar essa diferença. Verifique a versão do seu cliente.

**Este exemplo é o motivo da regra de modalidade.** Uma reescrita tentadora seria "Sua solicitação falhou" e "um cliente desatualizado **é a causa mais comum**". As duas frases ficam melhores. As duas estão erradas: a primeira afirma uma falha que o sistema só suspeita, e a segunda inventa uma frequência que não aparece no original. Uma reescrita que fornece uma causa, uma frequência ou um mecanismo deixou de ser reescrita.

Observe também que "pode ter falhado" mantém uma forma composta que a regra de tempo simples removeria. **Quando a regra de tempo verbal e a regra de modalidade entram em conflito, a modalidade vence.** Tirar o auxiliar aqui apagaria a incerteza junto com o tempo verbal.

### Exemplo C: instrução entre agentes

**Antes:**
> Assim que o job anterior tiver sido concluído e desde que nenhum erro tenha sido levantado, o agente seguinte deve proceder ao consumo do artefato de saída, sendo importante ressaltar que às vezes são gerados artefatos parciais em situações de timeout.

**Violações marcadas:**
- Tempos compostos e voz passiva ("tiver sido concluído", "tenha sido levantado", "são gerados").
- Nominalização com verbo-suporte ("proceder ao consumo").
- Rodeio vazio ("sendo importante ressaltar que").
- "Deve" ambíguo: obrigação ou recomendação? Aqui o contexto indica obrigação.
- Uma frase, três fatos separados (condição de conclusão, próxima ação, aviso de caso limite).
- 41 palavras, acima do limite de 20 para instruções.

**Depois:**
> Espere o job anterior terminar sem erros. Depois, leia o artefato de saída. Atenção: um timeout pode gerar um artefato parcial. Verifique se o artefato está completo antes de usar o artefato.

Duas decisões que precisam ficar visíveis:
- "Deve proceder ao consumo" virou o imperativo "leia". A STE permite isso em instruções, porque uma recomendação para o agente que executa a tarefa é um comando. Não faça a mesma troca em texto descritivo.
- A última frase é **nova**. O original avisava sobre artefatos parciais, mas não dizia o que fazer. A verificação torna o aviso útil, mas é conteúdo acrescentado. Por isso ela aparece aqui como acréscimo, e não como reescrita. Se o silêncio do original foi proposital, remova a frase.

### Exemplo D: prosa de README (modo Estilo STE)

**Antes:**
> Nossa camada de cache foi projetada para se integrar perfeitamente à sua stack atual, sem complicação e sem dependência de fornecedor; ela alavanca similaridade semântica para reduzir drasticamente os cache misses que tradicionalmente afetam workloads de LLM.

**Violações marcadas:**
- Adjetivos de marketing e afirmações sem medida ("perfeitamente", "sem complicação", "drasticamente").
- Ponto e vírgula juntando duas ideias.
- Gíria corporativa ("alavanca").
- Voz passiva sem agente ("foi projetada").
- 37 palavras, acima do limite de 25 para descrições.

**Depois:**
> Um cache comum compara as requisições pelo texto exato, então uma pequena mudança na redação causa um cache miss. Este cache compara o significado de um novo prompt com os prompts que ele já guarda. Ele roda junto com a sua stack atual e não guarda dados fora dela.

O modo Estilo STE manteve o ritmo explicativo e não impôs um termo fixo por conceito. Mesmo assim, ele cortou os adjetivos de marketing, o ponto e vírgula, a gíria e o excesso de palavras. "Cache miss" e "prompt" ficaram, porque são termos técnicos consagrados.

### Exemplo E: o "tem feito" traduzido do inglês

**Antes (traduzido de "The migration has completed and the old table has been dropped."):**
> A migração tem concluído e a tabela antiga tem sido removida.

**Violações marcadas:**
- Pretérito perfeito composto com sentido de ação concluída. Em português, a frase diz que a migração conclui repetidamente e que a tabela é removida repetidamente.
- Voz passiva ("tem sido removida").

**Depois:**
> A migração terminou. O script removeu a tabela antiga.

Atenção: "o script" é um agente que o original em inglês não nomeia. Se o agente da remoção não é conhecido, mantenha a passiva simples: "A tabela antiga foi removida." A regra de voz ativa nunca autoriza inventar quem age.

## Como ler estes exemplos

A Parte 1 mostra as regras em que a skill se baseia, já adaptadas ao português. A Parte 2 mostra a transferência: a mesma disciplina (um significado por palavra, voz ativa, tempo simples, uma instrução por frase, condições explícitas em vez de orações subordinadas escondidas) deixa qualquer texto gerado por IA mais fácil de ler, e não só manuais de aeronaves. A Parte 3 mostra o que a STE não cobre: o ruído típico de uma resposta de IA.

## Parte 3: ruído de resposta de IA

### Exemplo: resposta de conversa

**Antes**

> Ótima pergunta! 😊 Vou te explicar de forma detalhada. Basicamente, o comando `git rebase` é uma ferramenta poderosa que permite reescrever o histórico de commits. Existem várias formas de usar o rebase, como o rebase interativo, o rebase com `--onto` e o rebase automático no `git pull`. Para o seu caso, você vai estar usando `git rebase main` estando na sua branch. Lembre-se de sempre fazer backup antes de operações que alteram o histórico!
>
> **Resumindo:** use `git rebase main` na sua branch.
>
> Se tiver mais alguma dúvida, é só falar!

**Depois**

> Na sua branch, rode `git rebase main`. O comando reaplica seus commits sobre a versão atual da `main`.

**O que saiu**

- Introdução vazia e emoji ("Ótima pergunta! 😊", "Vou te explicar de forma detalhada").
- Adjetivo de marketing ("ferramenta poderosa").
- Informação não pedida (os outros tipos de rebase).
- Gerundismo ("vai estar usando").
- Aviso genérico ("Lembre-se de sempre fazer backup"). Se o leitor precisa de um cuidado específico, por exemplo não usar rebase numa branch que outras pessoas já baixaram, diga esse cuidado. Um aviso genérico não muda o que o leitor faz.
- Resumo que repete a resposta e oferta genérica no fim.
