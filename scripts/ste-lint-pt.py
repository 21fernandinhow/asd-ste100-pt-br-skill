#!/usr/bin/env python3
"""Linter determinístico para as regras estruturais da skill asd-ste100-pt-br.

Adaptação para o português do Brasil do ste-lint.py de
danyuchn/asd-ste100-skill (MIT). Verifica só regras que dispensam um
dicionário. Por projeto, nunca marca rodeios nem modalidade (pode, poderia,
talvez, teria, pode ter falhado): a skill trata a confiança como conteúdo, e um
linter que pressiona para cortar rodeios reescreveria afirmações.

Uso:
    ste-lint-pt.py ARQUIVO [ARQUIVO ...]
    echo "texto" | ste-lint-pt.py [--json]
    ste-lint-pt.py --baseline 5 ARQUIVO      # passa se as graves não passarem de 5
    ste-lint-pt.py --disable voz-passiva,tempo-composto ARQUIVO
    ste-lint-pt.py --selftest

Código de saída 1 quando as violações graves passam do baseline (padrão 0).
Achados de recomendação (voz passiva, tempos compostos, "o mesmo") nunca
falham a execução. Código 2 em erro de uso (opção desconhecida, valor
inválido, regra desconhecida, arquivo ilegível).
"""
import argparse
import bisect
import contextlib
import io
import json
import os
import re
import sys
import tempfile

# Heurísticas com regex, não um parser. Sem regra de cadeia de "de": exigiria
# análise sintática para evitar falsos positivos constantes. Sem regra de
# sujeito oculto: exigiria análise de correferência.

# Particípios irregulares mais comuns.
IRREGULAR_PARTICIPLES = (
    "feit[oa]s?|dit[oa]s?|escrit[oa]s?|abert[oa]s?|post[oa]s?|vist[oa]s?|"
    "cobert[oa]s?|entregues?|aceit[oa]s?|impress[oa]s?|pag[oa]s?|ganh[oa]s?|"
    "gast[oa]s?|eleit[oa]s?|pres[oa]s?|suspens[oa]s?|solt[oa]s?|expuls[oa]s?|"
    "extint[oa]s?|vind[oa]s?"
)
REGULAR_PARTICIPLE = r"\w+(?:ad|id|íd)[oa]s?"

# Palavras em -ado/-ido que, depois de "é" ou "tem", quase sempre são
# substantivos ou adjetivos, e não particípios.
NOUN_EXCEPTIONS = {
    "cuidado", "resultado", "estado", "sentido", "significado", "mercado",
    "lado", "pedido", "ruído", "partido", "adequado", "adequada",
    "apropriado", "apropriada", "complicado", "complicada", "delicado",
    "delicada", "ocupado", "ocupada", "errado", "errada", "privado", "privada",
    "exagerado", "exagerada", "válido", "sólido", "rápido", "rápida",
    "tímido", "líquido", "nítido", "lúcido", "cândido", "ácido", "sabido",
    "vida", "nada", "cada", "medida", "saída", "entrada", "chegada", "partida",
    "jornada", "camada", "chamada", "rodada", "estrada",
}

# Mantido por compatibilidade com o núcleo do linter original. Em português
# os rodeios com "ter" no infinitivo ("pode ter falhado") nunca casam com a
# regra de tempo composto, porque a regra não inclui "ter".
MODAL_PERFECT_PREFIX = re.compile(
    r"\b(?:pode|podem|poderia|poderiam|deve|devem|deveria|deveriam)\s+$", re.I,
)

# "é o mesmo", "continua a mesma": "mesmo" com sentido de "igual", não pronome.
MESMO_IDENTITY_PREFIX = re.compile(
    r"\b(?:é|são|foi|foram|era|eram|ser|seja|sejam|será|serão|continua|"
    r"continuam|permanece|permanecem|fica|ficam|sempre)\s+$", re.I,
)

RULES = [
    ("ponto-e-virgula", "grave",
     re.compile(r";"),
     "A STE proíbe o ponto e vírgula (Regra 8.1). Divida em frases separadas."),
    ("gerundismo", "grave",
     re.compile(r"\b(?:vou|vais|vai|vamos|vão|irei|irá|iremos|irão|ia|iam|"
                r"íamos)\s+estar\s+\w+ndo\b", re.I),
     "Gerundismo. Use o futuro simples ou ir + infinitivo (vou enviar, não vou estar enviando)."),
    ("jargao-corporativo", "grave",
     re.compile(r"\b(?:(?:d[aáeê]|dar|deu|dei|dando|damos|dão|darei|dará|demos)"
                r"\s+(?:um|uma)\s+(?:start|ping|up|refresh|check|reset)|"
                r"(?:fa[zç]\w*|fez|fiz\w*)\s+(?:um|o)\s+follow[- ]?up|"
                r"start(?:ar|a|am|e|em|ou|ando|ad[oa]s?|amos)|"
                r"perform(?:ar|a|am|e|em|ou|ando|amos)|"
                r"alavanc(?:ar|a|am|ou|ando|ad[oa]s?|amos)|"
                r"endereç(?:ar|a|am|ou|ando|amos)|"
                r"agreg\w*\s+valor)\b", re.I),
     "Gíria corporativa ou estrangeirismo desnecessário. Use o verbo simples (iniciar, contatar, acompanhar, executar, resolver)."),
    ("adjetivo-de-marketing", "grave",
     re.compile(r"\b(?:robust[oa]s?|inovador(?:a|es|as)?|revolucionári[oa]s?|"
                r"disruptiv[oa]s?|poderos[oa]s?|incríve(?:l|is)|de ponta|"
                r"de última geração|sem esforço|sem complicaç(?:ão|ões)|"
                r"perfeitamente integrad[oa]s?|integração perfeita|"
                r"ultrarrápid[oa]s?|líder de mercado|best-in-class|"
                r"game[- ]changer|state-of-the-art|world-class)\b", re.I),
     "Adjetivo de marketing. Exclua ou troque pela medida que justifica a afirmação."),
    ("verbo-suporte", "grave",
     re.compile(r"\b(?:realiz\w*|efetu\w*|conduz\w*|promov\w*|proced\w*|"
                r"fa[zç]\w*|fez|fiz\w*|feit[oa]s?)\s+(?:a|à|o|ao|uma|um|as|os|às|aos)\s+"
                r"\w+(?:ção|ções|são|sões|mento|mentos|ância|ências?|agem|agens|ise|ises)\b",
                re.I),
     "Ação congelada em substantivo com verbo-suporte. Use o verbo (analise, não realize a análise)."),
    ("voz-passiva", "recomendacao",
     re.compile(r"\b(?:é|são|foi|foram|será|serão|seria|seriam|era|eram|fosse|"
                r"fossem|for|forem|sendo|sido|ser)\s+(?:" + REGULAR_PARTICIPLE
                + r"|" + IRREGULAR_PARTICIPLES + r")\b", re.I),
     "Possível voz passiva. Nomeie quem age e use a voz ativa, a menos que o agente seja desconhecido ou irrelevante."),
    ("tempo-composto", "recomendacao",
     # "teria" fica de fora: o futuro do pretérito de distanciamento é rodeio.
     re.compile(r"\b(?:tem|têm|tens|tenho|temos|tinha|tinhas|tinham|tínhamos|"
                r"havia|haviam|havíamos|terá|terão|teremos|tiver|tiverem|"
                r"tivesse|tivessem)\s+(?:sido\s+)?(?:\w+(?:ado|ido|ído)|"
                r"feito|dito|escrito|aberto|posto|visto|coberto|entregue|aceito|"
                r"impresso|pago|ganho|gasto|eleito|preso|suspenso|vindo)\b", re.I),
     "Tempo composto. 'Tem feito' indica ação repetida, não concluída. Use o pretérito perfeito simples (fez), a menos que a repetição seja o ponto (então mantenha e sinalize)."),
    ("o-mesmo-pronome", "recomendacao",
     re.compile(r"\b(?:o|a|os|as|do|da|dos|das|no|na|nos|nas|ao|à|aos|às|pelo|"
                r"pela|pelos|pelas)\s+mesm[oa]s?(?=\s*(?:[.,;:!?)]|$)|\s+(?:é|são|"
                r"foi|foram|deve|devem|pode|podem|está|estão|será|serão|precisa|"
                r"precisam|tem|têm)\b)", re.I),
     "'O mesmo' usado como pronome. Repita o substantivo ou use ele/ela."),
]

# Uma palavra, um significado: grupos de verbos que costumam alternar para a
# mesma ação. Cada membro é um rótulo (infinitivo) e um padrão de conjugação.
_AR = (r"(?:ar|o|a|as|amos|am|e|es|em|emos|ei|ou|aram|ava|avam|ando|ad[oa]s?|"
       r"arei|ará|arão|aremos|aria|ariam|asse|assem|arem|ação|ações)")
_ER = (r"(?:er|o|e|es|em|emos|i|eu|eram|ia|iam|endo|id[oa]s?|erei|erá|erão|"
       r"eremos|eria|eriam|esse|essem|erem|a|am|as|amos)")
_IR = (r"(?:ir|o|e|es|em|imos|i|iu|iram|ia|iam|indo|id[oa]s?|íd[oa]s?|irei|irá|"
       r"irão|iremos|iria|iriam|isse|issem|irem|a|am|as|amos)")
_SUBJ_QU = r"(?:e|es|em|ei|emos)"

SYNONYM_PATTERNS = {
    "verificar": r"verific" + _AR + r"|verifiqu" + _SUBJ_QU,
    "conferir": r"confer" + _IR + r"|confir(?:o|a|as|am|amos)",
    "checar": r"chec" + _AR + r"|chequ" + _SUBJ_QU,
    "confirmar": r"confirm" + _AR,
    "validar": r"valid" + _AR,
    "excluir": r"exclu" + _IR,
    "remover": r"remov" + _ER,
    "apagar": r"apag" + _AR + r"|apagu" + _SUBJ_QU,
    "deletar": r"delet" + _AR,
    "iniciar": r"inici" + _AR,
    "começar": r"começ" + _AR + r"|comec" + _SUBJ_QU,
    "parar": r"par(?:ar|e|em|ou|aram|ando|ad[oa]s?|ará|arão|aria|asse|amos)",
    "interromper": r"interromp" + _ER,
    "encerrar": r"encerr" + _AR,
    "mostrar": r"mostr" + _AR,
    "exibir": r"exib" + _IR,
    "usar": r"us" + _AR,
    "utilizar": r"utiliz" + _AR,
    "empregar": r"empreg" + _AR + r"|empregu" + _SUBJ_QU,
    "corrigir": r"corrig" + _IR + r"|corrij(?:o|a|as|am|amos)",
    "consertar": r"consert" + _AR,
    "reparar": r"repar" + _AR,
    "enviar": r"envi" + _AR,
    "mandar": r"mand" + _AR,
    "transmitir": r"transmit" + _IR,
    "obter": (r"obt(?:er|enho|ém|êm|emos|ive|eve|iveram|inha|inham|endo|id[oa]s?|"
              r"erá|erão|eria|ivesse|iver|iverem|enha|enham)"),
    "buscar": r"busc" + _AR + r"|busqu" + _SUBJ_QU,
    "recuperar": r"recuper" + _AR,
    "alterar": r"alter" + _AR,
    "mudar": r"mud" + _AR,
    "modificar": r"modific" + _AR + r"|modifiqu" + _SUBJ_QU,
}

SYNONYM_GROUPS = [
    ("verificar", "conferir", "checar", "confirmar", "validar"),
    ("excluir", "remover", "apagar", "deletar"),
    ("iniciar", "começar"),
    ("parar", "interromper", "encerrar"),
    ("mostrar", "exibir"),
    ("usar", "utilizar", "empregar"),
    ("corrigir", "consertar", "reparar"),
    ("enviar", "mandar", "transmitir"),
    ("obter", "buscar", "recuperar"),
    ("alterar", "mudar", "modificar"),
]

MAX_WORDS = 25  # limite de descrições. O de instruções é 20, mas o linter não sabe o tipo do texto.

CODE_FENCE = re.compile(r"^(```|~~~)")
INLINE_CODE = re.compile(r"`[^`]*`")
LIST_ITEM_START = re.compile(
    r"^(?P<indent> {0,3})(?P<marker>[-*+]|[0-9]+[.)])(?P<gap> +)(?P<body>.*)$"
)
CONJUNCTION_END = re.compile(r"\b(?:e|ou)\s*$", re.I)
TABLE_SEPARATOR_CELL = re.compile(r"^:?-{3,}:?$")
# Headings, thematic breaks, front-matter delimiters, and HTML lines stand alone.
STANDALONE_LINE = re.compile(r"^ {0,3}(?:#|<|(?:[-*_=] *){3,}$)")
BLOCKQUOTE_PREFIX = re.compile(r"^ {0,3}(?:> ?)+")
# Any list marker at any depth starts a new prose block.
ANY_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|[0-9]+[.)])(?:\s|$)")
# A token that ends in terminal punctuation, optionally followed by closing
# quotes, brackets, or Markdown emphasis markers ("**Lead.**").
SENTENCE_END = re.compile(r"[.!?][\"'”’)\]*_]*$")
OPENERS = "\"'“‘([*_"
# Abbreviations whose period never ends a sentence.
ABBREVIATIONS = {"vs.", "cf.", "aprox.", "sr.", "sra.", "srs.", "dr.", "dra.", "fig.",
                 "n.", "nº.", "ex.", "p.ex.", "p. ex.", "obs.", "pág.", "p.", "art.", "prof.", "profa.",
                 "av.", "tel.", "máx.", "mín.", "cap.", "vol."}
# Dotted initialisms such as "e.g." and "U.S." end a sentence only when the
# next word starts with a capital letter.
DOTTED_ABBREVIATION = re.compile(r"(?:[a-z]\.){2,}", re.I)


def _word_re(base):
    return re.compile(r"\b(?:" + SYNONYM_PATTERNS[base] + r")\b", re.I)


def _mask_inline_code(text):
    """Blank code spans with equal-length spaces so columns stay true."""
    return INLINE_CODE.sub(lambda match: " " * len(match.group(0)), text)


def _sentence_starts(text):
    """Return the offset of each sentence start in text.

    A sentence ends at a word that ends in terminal punctuation, after any
    closing quotes or brackets. Known abbreviations do not end a sentence.
    One pass over the words keeps the cost linear in the text length.
    """
    words = list(re.finditer(r"\S+", text))
    if not words:
        return [0]
    starts = [words[0].start()]
    for word, next_word in zip(words, words[1:]):
        end = SENTENCE_END.search(word.group())
        if not end:
            continue
        core = word.group()[:end.start() + 1].lstrip(OPENERS)
        if core.lower() in ABBREVIATIONS:
            continue
        if (DOTTED_ABBREVIATION.fullmatch(core)
                and not next_word.group().lstrip(OPENERS)[:1].isupper()):
            continue
        starts.append(next_word.start())
    return starts


def _long_sentence_findings(pieces, filename):
    """Flag long sentences in one prose block.

    pieces is a list of (lineno, source_column, text) tuples. The texts are
    joined with spaces, so a sentence wrapped across source lines is counted
    once, and each finding points at the line and column where it starts.
    """
    offsets, position = [], 0
    for _, _, text in pieces:
        offsets.append(position)
        position += len(text) + 1
    joined = " ".join(text for _, _, text in pieces)
    findings = []
    starts = _sentence_starts(joined)
    for start, end in zip(starts, starts[1:] + [len(joined)]):
        n = len(joined[start:end].split())
        if n <= MAX_WORDS:
            continue
        index = bisect.bisect_right(offsets, start) - 1
        offset = offsets[index]
        lineno, source_column, _ = pieces[index]
        findings.append({"file": filename, "line": lineno,
                         "col": source_column + start - offset + 1,
                         "rule": "frase-longa", "level": "grave",
                         "match": f"{n} palavras",
                         "message": f"A frase tem {n} palavras (limite {MAX_WORDS}). Divida a frase."})
    return findings


def _leading_spaces(line):
    return len(line) - len(line.lstrip(" "))


def _is_list_continuation(line, content_indent):
    if not line.strip():
        return True
    if LIST_ITEM_START.match(line):
        return False
    return _leading_spaces(line) >= content_indent


def _split_table_row(line):
    """Return trimmed table cells and their zero-based source columns.

    A pipe must separate at least two cells. Escaped pipes stay in their cell.
    This deliberately implements only the ordinary Markdown table shape; it is
    enough to distinguish a table from prose that happens to contain a pipe.
    """
    left = len(line) - len(line.lstrip())
    right = len(line.rstrip())
    content = line[left:right]
    if "|" not in content:
        return None
    if content.startswith("|"):
        content = content[1:]
        left += 1
    if content.endswith("|"):
        content = content[:-1]
    raw_cells = re.split(r"(?<!\\)\|", content)
    if len(raw_cells) < 2:
        return None

    cells = []
    column = left
    for raw_cell in raw_cells:
        leading = len(raw_cell) - len(raw_cell.lstrip())
        cells.append((raw_cell.strip(), column + leading))
        column += len(raw_cell) + 1
    return cells


def _markdown_table_cells(lines):
    """Map ordinary Markdown table rows to their prose cells.

    The separator row anchors detection, so pipe-containing prose is not
    treated as a table. Both leading-pipe and no-leading-pipe table styles are
    accepted when their header and body use the same number of cells.
    """
    table_cells = {}
    index = 1
    while index < len(lines):
        separator = _split_table_row(lines[index])
        header = _split_table_row(lines[index - 1])
        if (not separator or not header or len(separator) != len(header)
                or not all(TABLE_SEPARATOR_CELL.fullmatch(cell)
                           for cell, _ in separator)):
            index += 1
            continue

        table_cells[index - 1] = header
        table_cells[index] = []
        index += 1
        while index < len(lines):
            row = _split_table_row(lines[index])
            if not row or len(row) != len(separator):
                break
            table_cells[index] = row
            index += 1
    return table_cells


def _dangling_conjunction_findings(text, filename):
    lines = text.splitlines()
    findings = []
    in_fence = False
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if CODE_FENCE.match(stripped):
            in_fence = not in_fence
            index += 1
            continue
        if in_fence:
            index += 1
            continue
        start = LIST_ITEM_START.match(line)
        if not start:
            index += 1
            continue

        content_indent = (len(start.group("indent"))
                          + len(start.group("marker"))
                          + len(start.group("gap")))
        item_lines = [(index, start.group("body"))]
        next_index = index + 1
        item_fence = False
        while next_index < len(lines):
            candidate = lines[next_index]
            candidate_stripped = candidate.strip()
            if CODE_FENCE.match(candidate_stripped):
                # Fence delimiters are state markers, not meaningful item lines.
                item_fence = not item_fence
                next_index += 1
                continue
            if item_fence:
                next_index += 1
                continue
            if not _is_list_continuation(candidate, content_indent):
                break
            item_lines.append((next_index, candidate))
            next_index += 1

        meaningful = []
        for line_index, item_line in item_lines:
            # Preserve code spans as neutral operands while ignoring their contents.
            cleaned = INLINE_CODE.sub(" CODE ", item_line).strip()
            if cleaned:
                meaningful.append((line_index, cleaned))
        if meaningful:
            end_line_index, end_line = meaningful[-1]
            conjunction = CONJUNCTION_END.search(end_line)
        else:
            end_line_index, end_line, conjunction = None, None, None
        if conjunction:
            if end_line_index == index:
                finding_line = index + 1
                finding_col = start.start("marker") + 1
            else:
                raw_end_line = next(
                    raw for line_index, raw in item_lines
                    if line_index == end_line_index
                )
                masked_end_line = INLINE_CODE.sub(
                    lambda match: " " * len(match.group(0)), raw_end_line
                )
                raw_conjunction = CONJUNCTION_END.search(masked_end_line)
                finding_line = end_line_index + 1
                finding_col = raw_conjunction.start() + 1 if raw_conjunction else 1
            findings.append({
                "file": filename,
                "line": finding_line,
                "col": finding_col,
                "rule": "conjuncao-solta",
                "level": "grave",
                "match": end_line,
                "message": "Item de lista termina com conjunção (e/ou). Complete o item ou junte o item com o próximo.",
            })
        index = next_index
    return findings


def lint(text, filename="<stdin>"):
    findings = []
    words_total = 0
    in_fence = False
    lines = text.splitlines()
    table_cells = _markdown_table_cells(lines)
    # first occurrence of each synonym-group member: (group_idx, base) -> (line, col, match)
    seen_synonyms = {}
    # consecutive prose lines form one block, so wrapped sentences count once
    block = []
    in_quote = False

    def flush():
        findings.extend(_long_sentence_findings(block, filename))
        block.clear()

    for lineno, raw_line in enumerate(lines, 1):
        if CODE_FENCE.match(raw_line.strip()):
            flush()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        segments = table_cells.get(lineno - 1, [(raw_line, 0)])
        is_table = (lineno - 1) in table_cells
        quote = BLOCKQUOTE_PREFIX.match(raw_line)
        is_quote = bool(quote)
        # judge block boundaries on the text inside any blockquote prefix
        content = raw_line[quote.end():] if quote else raw_line
        standalone = STANDALONE_LINE.match(content)
        if (is_table or not content.strip() or standalone
                or ANY_LIST_ITEM.match(content) or is_quote != in_quote):
            flush()
        in_quote = is_quote
        for segment, source_column in segments:
            line = _mask_inline_code(segment)
            words_total += len(line.split())
            for rule_id, level, pattern, msg in RULES:
                for m in pattern.finditer(line):
                    if rule_id == "tempo-composto" and MODAL_PERFECT_PREFIX.search(
                        line[:m.start()]
                    ):
                        continue
                    if (rule_id in ("voz-passiva", "tempo-composto")
                            and m.group(0).split()[-1].lower() in NOUN_EXCEPTIONS):
                        continue
                    if rule_id == "o-mesmo-pronome" and MESMO_IDENTITY_PREFIX.search(
                        line[:m.start()]
                    ):
                        continue
                    findings.append({"file": filename, "line": lineno,
                                     "col": source_column + m.start() + 1,
                                     "rule": rule_id, "level": level,
                                     "match": m.group(0), "message": msg})
            for gi, group in enumerate(SYNONYM_GROUPS):
                for base in group:
                    if (gi, base) in seen_synonyms:
                        continue
                    m = _word_re(base).search(line)
                    if m:
                        seen_synonyms[(gi, base)] = (
                            lineno, source_column + m.start() + 1, m.group(0)
                        )
            # the blockquote prefix is markup, not words in the sentence
            skip = quote.end() if quote and not is_table else 0
            if line[skip:].strip():
                block.append((lineno, source_column + skip, line[skip:]))
            if is_table:
                flush()  # each table cell is its own block
        if standalone:
            flush()
    flush()
    # synonym rotation: flag each member after the first, at its first occurrence
    for gi, group in enumerate(SYNONYM_GROUPS):
        present = [(seen_synonyms[(gi, b)], b) for b in group if (gi, b) in seen_synonyms]
        if len(present) > 1:
            present.sort()  # document order
            first_base = present[0][1]
            for (lineno, col, match), base in present[1:]:
                findings.append({"file": filename, "line": lineno, "col": col,
                                 "rule": "rotacao-de-sinonimos", "level": "grave",
                                 "match": match,
                                 "message": f"'{base}' e '{first_base}' nomeiam a mesma ação. Escolha um verbo e use sempre esse verbo."})
    findings.extend(_dangling_conjunction_findings(text, filename))
    findings.sort(key=lambda f: (f["line"], f["col"]))
    return findings, words_total


def report(findings, words_total, as_json, hard_count, baseline):
    rate = round(len(findings) * 100 / words_total, 1) if words_total else 0.0
    if as_json:
        print(json.dumps({"violations": findings, "count": len(findings),
                          "hard_count": hard_count, "baseline": baseline,
                          "words": words_total, "per_100_words": rate}, indent=2))
        return
    for f in findings:
        print(f"{f['file']}:{f['line']}:{f['col']} {f['rule']}: {f['message']} [{f['match']}]")
    print(f"\n{len(findings)} violações ({hard_count} graves, baseline {baseline}), "
          f"{words_total} palavras, {rate} por 100 palavras")
    print("Rodeios e modalidade (pode, talvez, teria) nunca são marcados: a confiança é conteúdo.")


def selftest():
    def rules_of(text):
        return {f["rule"] for f in lint(text)[0]}

    def count(text, rule):
        return sum(1 for f in lint(text)[0] if f["rule"] == rule)

    bad = ("O painel é removido; vou estar enviando o job. "
           "Realize a análise do log robusto. "
           "Dê um start no processo. "
           "O job tem falhado. Salve o mesmo.")
    rules = rules_of(bad)
    for expected in ("ponto-e-virgula", "gerundismo", "verbo-suporte",
                     "adjetivo-de-marketing", "jargao-corporativo",
                     "voz-passiva", "tempo-composto", "o-mesmo-pronome"):
        assert expected in rules, expected
    # rodeios e modalidade nunca são marcados
    findings, _ = lint("A requisição pode ter falhado. Talvez seja um timeout. "
                       "O disco deve ter enchido. O servidor teria falhado. "
                       "O servidor pode estar reiniciando. Isso poderia ajudar.")
    assert findings == [], findings
    # gerundismo só com ir + estar + gerúndio
    assert count("Vamos estar verificando o pedido.", "gerundismo") == 1
    assert count("Amanhã vou estar viajando o dia todo.", "gerundismo") == 1
    assert count("O processo está rodando.", "gerundismo") == 0
    assert count("O processo deve estar rodando.", "gerundismo") == 0
    # tempo composto, inclusive com particípio irregular e mais-que-perfeito
    text = "O job tem rodado. Temos feito testes. O agente tinha terminado."
    assert count(text, "tempo-composto") == 3, lint(text)
    assert count("O job tem cuidado com o disco.", "tempo-composto") == 0
    assert count("O agente tem que terminar.", "tempo-composto") == 0
    assert count("O job pode ter rodado.", "tempo-composto") == 0
    # voz passiva, com exceções para adjetivos comuns
    assert count("O arquivo foi excluído pelo agente.", "voz-passiva") == 1
    assert count("O relatório foi escrito ontem.", "voz-passiva") == 1
    assert count("O formato é adequado.", "voz-passiva") == 0
    assert count("O arquivo é grande.", "voz-passiva") == 0
    # verbo-suporte
    assert count("Efetue o pagamento da fatura.", "verbo-suporte") == 1
    assert count("Faça uma verificação do disco.", "verbo-suporte") == 1
    assert count("Proceda à instalação.", "verbo-suporte") == 1
    assert count("Verifique o disco.", "verbo-suporte") == 0
    # jargão: o substantivo "endereço" não é o verbo "endereçar"
    assert count("Informe o endereço IP.", "jargao-corporativo") == 0
    assert count("Vamos endereçar o problema.", "jargao-corporativo") == 1
    assert count("Faça um follow-up com o cliente.", "jargao-corporativo") == 1
    assert count("O app tem boa performance.", "jargao-corporativo") == 0
    # "o mesmo": pronome é marcado, identidade e adjetivo não
    assert count("Feche o arquivo e salve o mesmo.", "o-mesmo-pronome") == 1
    assert count("A mesma deve ser preenchida.", "o-mesmo-pronome") == 1
    assert count("O valor é o mesmo.", "o-mesmo-pronome") == 0
    assert count("Use o mesmo arquivo.", "o-mesmo-pronome") == 0
    assert count("Rode os dois ao mesmo tempo.", "o-mesmo-pronome") == 0
    # blocos de código são ignorados
    findings, _ = lint("```\nx = a; y = b\n```")
    assert findings == []
    # todos os marcadores de lista, maiúsculas e espaço no fim
    findings, _ = lint(
        "- Confirme o destino e\n"
        "* Registre o resultado OU  \n"
        "+ Feche o painel\n"
        "1. Inicie a tarefa e\n"
        "2) Pare a tarefa ou"
    )
    dangling = [f for f in findings if f["rule"] == "conjuncao-solta"]
    assert len(dangling) == 4, dangling
    assert [f["line"] for f in dangling] == [1, 2, 4, 5], dangling
    assert [f["col"] for f in dangling] == [1, 1, 1, 1], dangling
    assert all(f["level"] == "grave" for f in dangling), dangling
    # "de" no fim do item não é a conjunção "e"
    findings, _ = lint("- Leia o arquivo de")
    assert not any(f["rule"] == "conjuncao-solta" for f in findings)

    # linhas de continuação válidas e código com quatro espaços são ignorados
    findings, _ = lint("  - Confirme o destino e\n    registre o resultado.")
    assert not any(f["rule"] == "conjuncao-solta" for f in findings)
    findings, _ = lint("- Confirme o destino\n  e")
    dangling = [f for f in findings if f["rule"] == "conjuncao-solta"]
    assert len(dangling) == 1 and dangling[0]["line"] == 2, dangling
    assert dangling[0]["col"] == 3, dangling
    findings, _ = lint("    - código e")
    assert not any(f["rule"] == "conjuncao-solta" for f in findings)
    findings, _ = lint("> - Confirme o destino e\n> - Registre o resultado ou")
    assert not any(f["rule"] == "conjuncao-solta" for f in findings)
    findings, _ = lint("- Faça isto e\n~~~\ncódigo e\n~~~")
    dangling = [f for f in findings if f["rule"] == "conjuncao-solta"]
    assert len(dangling) == 1 and dangling[0]["line"] == 1, dangling
    findings, _ = lint("```text\n- código e\n```")
    assert not any(f["rule"] == "conjuncao-solta" for f in findings)

    # marcadores com um e três espaços e largura de continuação ordenada
    findings, _ = lint(" - Inicie a tarefa e\n   registre o resultado.")
    assert not any(f["rule"] == "conjuncao-solta" for f in findings)
    findings, _ = lint("-  Inicie a tarefa e\n   registre o resultado.")
    assert not any(f["rule"] == "conjuncao-solta" for f in findings)
    findings, _ = lint("-\tInicie a tarefa e")
    assert not any(f["rule"] == "conjuncao-solta" for f in findings)
    findings, _ = lint("   - Inicie a tarefa e", filename="fixture.md")
    dangling = [f for f in findings if f["rule"] == "conjuncao-solta"]
    assert len(dangling) == 1 and dangling[0]["col"] == 4, dangling
    assert dangling[0]["file"] == "fixture.md"
    assert dangling[0]["match"].endswith("e")
    assert "Complete o item" in dangling[0]["message"]
    findings, _ = lint("100. Inicie a tarefa e\n  texto sem relação")
    dangling = [f for f in findings if f["rule"] == "conjuncao-solta"]
    assert len(dangling) == 1, dangling
    findings, _ = lint("- Inicie a tarefa e.\n- Pare a tarefa ou,")
    assert not any(f["rule"] == "conjuncao-solta" for f in findings)
    findings, _ = lint("- Inicie a tarefa e\n\n  registre o resultado.")
    assert not any(f["rule"] == "conjuncao-solta" for f in findings)
    findings, _ = lint("- Item pai e\n  - Item aninhado ou")
    dangling = [f for f in findings if f["rule"] == "conjuncao-solta"]
    assert [f["line"] for f in dangling] == [1, 2], dangling

    # prosa comum, código inline e código cercado são ignorados
    findings, _ = lint("O processo pode incluir etapas e")
    assert not any(f["rule"] == "conjuncao-solta" for f in findings)
    findings, _ = lint("- Use `e` como rótulo")
    assert not any(f["rule"] == "conjuncao-solta" for f in findings)
    findings, _ = lint("- Combine `left` e `right`")
    assert not any(f["rule"] == "conjuncao-solta" for f in findings), findings
    findings, _ = lint("~~~\n- código e\n~~~")
    assert not any(f["rule"] == "conjuncao-solta" for f in findings)
    findings, _ = lint(("palavra " * 30).strip() + ".")
    assert any(f["rule"] == "frase-longa" for f in findings)
    # a sintaxe de tabela Markdown é layout, não prosa. Cada célula é verificada.
    short_cell = " ".join(f"termo{number}" for number in range(1, 25)) + "."
    for table in (
            "| Rótulo | Detalhe |\n"
            "| --- | --- |\n"
            f"| Claro | {short_cell} |",
            "Rótulo | Detalhe\n"
            "--- | ---\n"
            f"Claro | {short_cell}"):
        findings, words_total = lint(table)
        assert not any(f["rule"] == "frase-longa" for f in findings), findings
        assert words_total == 27, words_total
    long_cell = " ".join(f"termo{number}" for number in range(1, 27)) + "."
    findings, _ = lint(
        "| Rótulo | Detalhe |\n"
        "| --- | --- |\n"
        f"| Claro | {long_cell} |"
    )
    long_sentences = [f for f in findings if f["rule"] == "frase-longa"]
    assert len(long_sentences) == 1, long_sentences
    assert long_sentences[0]["match"] == "26 palavras", long_sentences
    # rotação de sinônimos: o segundo membro é marcado, o primeiro é o mantido
    findings, _ = lint("Verifique o arquivo de config. Depois confira a saída. Confira duas vezes.")
    rot = [f for f in findings if f["rule"] == "rotacao-de-sinonimos"]
    assert len(rot) == 1 and "'conferir' e 'verificar'" in rot[0]["message"], rot
    findings, _ = lint("Exclua o arquivo. O agente removeu o backup.")
    rot = [f for f in findings if f["rule"] == "rotacao-de-sinonimos"]
    assert len(rot) == 1 and "'remover' e 'excluir'" in rot[0]["message"], rot
    # um termo só: sem alerta. "para" (preposição) não é o verbo "parar".
    findings, _ = lint("Verifique a config. Verifique a saída.")
    assert not any(f["rule"] == "rotacao-de-sinonimos" for f in findings)
    findings, _ = lint("Interrompa o job para liberar o disco.")
    assert not any(f["rule"] == "rotacao-de-sinonimos" for f in findings)
    findings, _ = lint("O usuário usa o painel.")
    assert not any(f["rule"] == "rotacao-de-sinonimos" for f in findings)
    # rótulos por arquivo
    findings, _ = lint("a; b", filename="x.md")
    assert findings[0]["file"] == "x.md"
    # código inline é mascarado, não apagado, para as colunas baterem
    findings, _ = lint("Rode `make all` e dê um start no nó.")
    jargon = [f for f in findings if f["rule"] == "jargao-corporativo"]
    assert len(jargon) == 1 and jargon[0]["col"] == 19, jargon
    # uma frase termina depois de aspas e parênteses de fechamento
    twenty = " ".join(["palavra"] * 20)
    findings, _ = lint(f'Ele perguntou "{twenty}?" Então {twenty} acabou. (Isso {twenty}.) Fim.')
    assert not any(f["rule"] == "frase-longa" for f in findings), findings
    # abreviações não terminam a frase
    findings, _ = lint(f"Use uma ferramenta, p.ex. o {twenty} linter aqui agora.")
    assert any(f["rule"] == "frase-longa" for f in findings), findings
    findings, _ = lint(f"Compare A vs. B no {twenty} teste.")
    assert any(f["rule"] == "frase-longa" for f in findings), findings
    findings, _ = lint(f"Veja o ex. do {twenty} teste aqui.")
    assert any(f["rule"] == "frase-longa" for f in findings), findings
    # uma frase quebrada em várias linhas conta uma vez, no início
    findings, _ = lint(f"Texto de introdução.\nO {twenty}\ncauda quebrada vem aqui agora.")
    long_sentences = [f for f in findings if f["rule"] == "frase-longa"]
    assert len(long_sentences) == 1, long_sentences
    assert (long_sentences[0]["line"], long_sentences[0]["col"]) == (2, 1), long_sentences
    findings, _ = lint(f"- Item {twenty}\n  continua no mesmo item.")
    assert any(f["rule"] == "frase-longa" for f in findings), findings
    # linhas vazias, títulos, regras, itens de lista e citações fecham um bloco
    for sep in ("\n\n", "\n# Título\n", "\n---\n", "\n- ", "\n> "):
        findings, _ = lint(f"Primeira {twenty} linha{sep}Segunda {twenty} linha.")
        assert not any(f["rule"] == "frase-longa" for f in findings), (sep, findings)
    # uma frase de abertura em negrito ou itálico termina no marcador
    findings, _ = lint(f"**Abertura.** O {twenty} mais palavras aqui agora.")
    assert not any(f["rule"] == "frase-longa" for f in findings), findings
    findings, _ = lint(f"_Nota._ O {twenty} mais palavras aqui agora.")
    assert not any(f["rule"] == "frase-longa" for f in findings), findings
    findings, _ = lint(f"Veja **p.ex.** o {twenty} linter aqui agora.")
    assert any(f["rule"] == "frase-longa" for f in findings), findings
    # uma abreviação com pontos termina a frase antes de palavra maiúscula
    findings, _ = lint(f"A equipe lançou nos E.U.A. Depois {twenty} hoje.")
    assert not any(f["rule"] == "frase-longa" for f in findings), findings
    # itens aninhados, itens citados e linhas HTML fecham um bloco
    for text in (f"- Primeiro item\n    - Primeira {twenty} linha\n      - Segunda {twenty} linha",
                 f"> - Primeira {twenty} linha\n> - Segunda {twenty} linha",
                 f"<!-- Primeira {twenty} linha -->\nSegunda {twenty} linha.",
                 f"> Primeira {twenty} linha.\n>\n> Segunda {twenty} linha."):
        findings, _ = lint(text)
        assert not any(f["rule"] == "frase-longa" for f in findings), (text, findings)
    # o prefixo de citação não é uma palavra da frase citada
    findings, _ = lint("> " + "\n> ".join(["palavra palavra palavra palavra palavra"] * 5) + ".")
    assert not any(f["rule"] == "frase-longa" for f in findings), findings
    # um bloco longo continua linear: uma frase curta por linha, sem linhas vazias
    findings, _ = lint("O agente leu o log.\n" * 20000)
    assert not any(f["rule"] == "frase-longa" for f in findings)
    # opções podem aparecer entre caminhos de arquivo
    with tempfile.TemporaryDirectory() as tmp:
        paths = [os.path.join(tmp, name) for name in ("a.md", "b.md")]
        for path in paths:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("Linha curta aqui.\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            assert main([paths[0], "--json", paths[1]]) == 0
        assert json.loads(out.getvalue())["words"] == 6, out.getvalue()
    # a linha de comando rejeita erros de digitação e valores inválidos
    for bad in (["--basline", "3"], ["--baseline"], ["--baseline", "x"],
                ["--baseline", "-1"], ["--disable", "passiva"], ["--base", "3"]):
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                main(bad)
        except SystemExit as e:
            assert e.code == 2, (bad, e.code)
        else:
            raise AssertionError(bad)
    assert _rule_list("voz-passiva,tempo-composto") == {"voz-passiva", "tempo-composto"}
    print("selftest OK")


RULE_IDS = {rule_id for rule_id, *_ in RULES} | {
    "frase-longa", "rotacao-de-sinonimos", "conjuncao-solta"}


def _rule_list(value):
    rules = {r for r in value.split(",") if r}
    unknown = rules - RULE_IDS
    if unknown:
        raise argparse.ArgumentTypeError(
            f"regra(s) desconhecida(s): {', '.join(sorted(unknown))}. "
            f"Regras conhecidas: {', '.join(sorted(RULE_IDS))}")
    return rules


def _non_negative_int(value):
    try:
        n = int(value)
    except ValueError:
        n = -1
    if n < 0:
        raise argparse.ArgumentTypeError(f"esperado um inteiro não negativo, recebido {value!r}")
    return n


def main(argv):
    parser = argparse.ArgumentParser(
        prog="ste-lint-pt.py", allow_abbrev=False,
        description="Linter determinístico para as regras estruturais da STE em português. "
                    "Lê o stdin quando nenhum ARQUIVO é informado.")
    parser.add_argument("paths", nargs="*", metavar="ARQUIVO")
    parser.add_argument("--json", action="store_true", help="imprime os achados em JSON")
    parser.add_argument("--baseline", type=_non_negative_int, default=0, metavar="N",
                        help="passa se as violações graves não passarem de N (padrão 0)")
    parser.add_argument("--disable", type=_rule_list, default=set(), metavar="REGRAS",
                        help="IDs de regras separados por vírgula para silenciar")
    parser.add_argument("--selftest", action="store_true", help="roda os testes embutidos")
    # intermixed parsing keeps flags valid between file paths
    args = parser.parse_intermixed_args(argv)
    if args.selftest:
        selftest()
        return 0
    as_json, baseline, disabled, paths = args.json, args.baseline, args.disable, args.paths

    findings, words_total = [], 0
    if paths:
        for p in paths:
            try:
                with open(p, encoding="utf-8") as fh:
                    text = fh.read()
            except OSError as e:
                parser.error(f"não foi possível ler {p}: {e.strerror}")
            f, w = lint(text, filename=p)
            findings.extend(f)
            words_total += w
    else:
        findings, words_total = lint(sys.stdin.read())

    findings = [f for f in findings if f["rule"] not in disabled]
    hard_count = sum(1 for f in findings if f["level"] == "grave")
    report(findings, words_total, as_json, hard_count, baseline)
    return 1 if hard_count > baseline else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
