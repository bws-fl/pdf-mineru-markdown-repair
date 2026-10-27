# Verification Checklist

Run these before delivering any converted document. Every check must produce a count, not a boolean — a count lets you tell "clean" from "the check never ran".

`scripts/audit.py` implements the mechanical subset. Use it first, then run the judgement-based checks below.

---

## Class 1 — Encoding

| Check | Assertion | Trap |
|---|---|---|
| BOM | exactly one, at offset 0 | `utf-8-sig` writes it; adding it manually produces two |
| Line endings | uniform; report CRLF vs bare-LF counts separately | bare LF count must be 0 in a CRLF document |
| Trailing whitespace on headings | 0 | `.*\s$` matches the `\r` of CRLF and reports every heading — compare `line != line.rstrip()` instead |
| Full-width space | 0 | |
| Runs of 3+ blank lines | 0 | |
| Line-ending normalization before multi-line matching | — | read with universal newlines, or a pattern containing `\n` matches nothing |

## Class 2 — Structure

| Check | Assertion |
|---|---|
| Heading level distribution | matches the baseline you recorded in reconnaissance |
| Deepest level used | no accidental level (a stray `####` silently created by a typo in the demotion step) |
| Tag pairing | `<table>`/`</table>`, `<tr>`/`</tr>`, `<td>`/`</td>` all equal |
| Heading ↔ toc | one-to-one; the miss list is empty |
| Heading fragments | 0 lines that are the tail of the previous heading |

## Class 3 — Objects

| Check | Assertion | Trap |
|---|---|---|
| Caption + continuation + uncaptioned = object count | equality | non-tabular tables exist (cover pages, CIP blocks, index tables) — add an explicit `EXTRA` constant rather than loosening the check |
| Primary identifiers unique | no duplicates | |
| Continuation captions resolve to a primary | 0 orphans | |
| Object has a caption within 3 lines above | 0 uncaptioned | |
| Formula markers | 0 `<eq>`, 0 unmatched `$`, 0 raw LaTeX (for non-formula documents) | formulas inside cells are missed by body-only scans |
| Image references | 0 externally-hosted URLs if offline delivery | |
| Tag-stripping regex | `</?[A-Za-z][A-Za-z0-9]*[^>]*>` | a looser `<[^>]+>` eats real text such as `<9.81` or `<35kV` |

## Class 4 — Text

| Check | Assertion |
|---|---|
| Half-width comma / semicolon / colon | 0 (subtract entity terminators first) |
| Half-width parentheses | 0, or an explicit allow-list (area codes) |
| Half-width tilde | 0 |
| Space after enumerated parenthesis | 0 |
| Percent sign width | uniform |
| HTML entities intact | 0 entities terminated by a full-width semicolon |

## Class 5 — Content preservation

Do not compare line counts. Compare normalized content units:

```
1. Extract all text from source and output.
2. Normalize: strip tags, strip math delimiters, collapse whitespace, normalize punctuation width.
3. Build multisets of non-empty tokens.
4. Diff both directions.
```

Symmetric delta (same token kinds, same counts on both sides) = pure formatting normalization, acceptable.
Asymmetric delta = real loss. Stop and investigate before delivering.

---

## False-Positive Traps

These produced real, expensive wrong conclusions. Check each before acting on a failure.

1. **Row-width check ignoring rowspan.** Summing `colspan` per row flags nearly every table. Simulate a grid, skipping cells already occupied by a rowspan. Observed ratio: 609 false, 7 real.
2. **Occurrence counts instead of line counts.** A phrase appearing twice on one line makes occurrence count exceed line count. Assert on lines.
3. **`\s` matching `\r`.** See the trailing-whitespace row above.
4. **Entity terminators as punctuation.** 8 "half-width semicolons" were 8 `;` characters closing HTML entities.
5. **Missing `EXTRA` in object count.** One object legitimately uncaptioned (a copyright-page table) makes the equality check fail.
6. **Regex that cannot match its own normalized form.** A continuation-caption pattern written as `^(continued\s*)?table` fails on `continued table 3` when the separator is absent; use a lookahead `(?=\s|$)` for the trailing boundary instead of requiring `\s`.
7. **Shell-interpolated regex.** Any pattern containing `$` in a `python -c` string gets expanded by the shell. Write the script to a file.

---

## Repair Order Rule

Sort all pending repairs by blast radius and execute ascending:

```
encoding → character substitution → punctuation width → heading levels
  → caption text → missing identifiers → line splits/merges → block splits
  → continuation insertion
```

Anything that changes the number of lines invalidates every line-index-based fix computed earlier. Observed failure: applying a "fill in missing caption numbers by original line number" pass *after* a line-splitting pass wrote every caption onto the wrong row.

Practical consequence: run the line-count-neutral passes to completion and assert them **first**.

---

## Sign-off Template

```
Encoding   BOM x1 / CRLF n / bare-LF 0 / bytes / lines
Structure  h1..h6 counts / tag pairs / heading-vs-toc misses
Objects    captions + continuations + extras = objects / duplicate IDs / orphan continuations
Text       half-width , ; : ( ) ~ counts / entity terminators / percent
Content    token diff: added N (kinds) / removed N (kinds) — symmetric or not
Residual   <eq> / $ / raw LaTeX / image links / 3+ blank runs / full-width spaces
```
