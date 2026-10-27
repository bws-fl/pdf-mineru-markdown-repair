# Defect Catalog

Defect taxonomy for converted documents. Organized by failure mode, not by source format, because the same converter bug appears whether the input was a PDF scan or a Word file.

Each entry: **symptom** (what you observe) → **root cause** (why the converter did it) → **repair** (what to do) → **detect** (how to find all instances).

---

## A. Structural defects

### A1. Heading levels assigned randomly
**Symptom** — The same logical level alternates between `#`, `##`, and `###` across the document. Chapter titles appear as `#` in one place and `##` in another.
**Root cause** — Converters infer level from font size and position heuristics, which drift with layout noise.
**Repair** — Discard the converter's levels entirely. Rebuild from the numbering prefix (`1.1`, `第3章`, `附录 A`) and cross-check against the source's table of contents.
**Detect** — Group all headings by their numbering depth and list the distinct `#` counts found per group. More than one count per group = inconsistent.

### A2. Title fragments split onto their own line
**Symptom** — A line that is grammatically the tail of the previous heading, standing alone.
**Root cause** — Line wrapping at a font-size boundary; the second line gets classified as body text.
**Repair** — Merge into the previous line.
**Detect** — Look for short lines directly after a heading that do not start a sentence and end without terminal punctuation.

### A3. Section headings left as plain text
**Symptom** — A heading exists in the source and in the table of contents but appears as an ordinary paragraph in the output.
**Root cause** — The converter's heading classifier missed it, often when the number and title lack a space (`9.2Components`).
**Repair** — Restore the heading marker, using the table of contents as the authoritative list.
**Detect** — Compare the toc entry list against body headings; any toc entry with no matching body heading is either this defect or a conversion drop.

### A4. Wrong-level demotion in appendices
**Symptom** — Appendix top-level titles stay at body-chapter level.
**Repair** — Demote appendix first-level titles one level; note that appendix clause numbering may restart, which is correct and must not be "fixed".

---

## B. Table defects

### B1. Object present in a secondary container only
**Symptom** — Entire classes of tables are missing, or every continuation marker is gone.
**Root cause** — The converter writes blocks to more than one JSON key; the primary key holds `lines_deleted: true` shells. Continuation markers often get classified as page headers and routed to a discarded block list.
**Repair** — Read **all** containers the converter emits, including discarded/header buckets, and reconcile.
**Detect** — Object count in source vs count across all containers. This is the single highest-cost defect to miss, because it fails silently and completely.

### B2. Two tables fused into one
**Symptom** — One table contains what the source prints as two pages/tables; the second half has no header row.
**Root cause** — Cross-page merge during layout reconstruction.
**Repair** — Split **in place**. Slice at the row where the second table's numbering restarts, borrow the header from the source, and insert a continuation caption between the halves. Never relocate the tail to "before the next table" — that reorders identifiers.
**Detect** — Tables whose row set contains a repeated numbering sequence, or whose width changes mid-table.

### B3. Continuation pages unmarked
**Symptom** — A multi-page table appears as two adjacent blocks with no indication they are the same table.
**Root cause** — The source's continuation pages often repeat only the header row and print no "continued" label; the converter therefore has nothing to detect.
**Repair** — Classify blocks by first-row signature: a block whose first row matches the *body* signature (item numbering, "item no.") rather than the *first-page* signature (document identification fields) is a continuation. Insert a continuation caption naming the table.
**Detect** — Continuation captions count vs continuation-type block count must match; every continuation must resolve to a primary caption (zero orphans); every table must have a caption within 3 lines (zero uncaptioned tables).

### B4. Column widths wrong → cells shifted
**Symptom** — Rows appear shifted left/right; content lands in the wrong column.
**Root cause** — `colspan` mis-assigned for one row (typically a header or numbering row) while total width still matches.
**Repair** — Rebuild the offending row's span sequence from a sibling row used as template.
**Detect** — **Must simulate a grid with rowspan occupancy.** Summing `colspan` per row over-counts and reports massive false positives (observed: 609/647 tables falsely flagged; 7 genuinely wrong).

### B5. Continuation row split into its own `<tr>`
**Symptom** — A short row with fewer cells than the table, containing the tail of the previous cell's text.
**Root cause** — Wrapped cell content mistaken for a new row.
**Repair** — Merge into the previous cell with a `<br>`.

### B6. Fused cells (ID + value in one cell)
**Symptom** — A cell contains an identifier glued to a value, and the identifier is then missing from the sequence.
**Root cause** — Two adjacent source cells merged during reconstruction.
**Repair** — Split back into two cells; restore the missing identifier.
**Detect** — Sequence continuity check on the identifier column; a gap plus an over-long neighbor cell is the signature.

### B7. Captions: four failure modes
| Mode | Symptom | Repair |
|---|---|---|
| Split | number line, blank line, title line | merge into one line, then blank line before the table |
| Missing number | title only, no identifier | derive from the document's own convention |
| Glued | title immediately followed by an unrelated field label | split at the field label |
| Misplaced | caption sits above the *next* section heading | move to the object it names |

**Order rule:** repair missing numbers **before** splitting lines. Number repair is line-count-neutral; splitting shifts every subsequent line index.

### B8. Caption numbering convention misread
**Symptom** — You "restore" suffixes the source never printed, or delete suffixes it did.
**Root cause** — Assuming one global convention.
**Repair** — Sample the source. Real conventions coexist in one document: bare number for single-object sections, `-1/-2` pairs where both a check table and an acceptance table exist, `X.Y.N-n` for sub-processes, parenthesized qualifiers for special cases.
**Detect** — For each section, list which forms appear; a missing form is only a defect if the same document uses it elsewhere under the same conditions.

---

## C. Text defects

### C1. Punctuation width inconsistency
**Symptom** — `,` and `，` mixed; `(text)` inside otherwise full-width Chinese prose.
**Root cause** — OCR and layout engines emit whichever byte pattern matched.
**Repair** — Determine the document's convention from 3–5 rendered pages **including table interiors**, then normalize the whole document. Preserve legitimate exceptions (phone area codes, code snippets, URLs).
**Trap** — Table interiors are commonly assumed exempt. Verify; in practice they follow the same convention as body text.

### C2. Half/full-width conversion corrupts entities
**Symptom** — `&lt;1000` becomes `&lt；1000`; the entity no longer parses.
**Root cause** — The semicolon that terminates an entity is itself a punctuation character and gets converted.
**Repair** — Re-terminate with `&([a-zA-Z]+)；` → `&\1;`, or convert entities first.
**Detect** — Scan for entity names followed by a full-width semicolon.

### C3. Ratio glyph vs colon
**Symptom** — Ratios render with an ordinary colon, spacing looks wrong.
**Root cause** — Sources often print a true ratio character (U+2236), which OCR maps to `:`.
**Repair** — Normalize ratios to the ratio glyph **before** colon normalization. Doing it after makes colon counts irreconcilable.

### C4. Tilde becomes strikethrough
**Symptom** — Text renders struck through in Markdown viewers.
**Root cause** — `~` mapped to `～` is fine, but paired `~~` is GFM strikethrough.
**Repair** — Normalize all tilde characters; verify zero remaining. Do this after formula handling.

### C5. Formulas left as converter markup
**Symptom** — `<eq>` tags, `$` mismatches, or raw LaTeX leaking into prose.
**Repair** — Convert to `$...$` / `$$...$$`. Scan the **whole document including table cells** — formulas inside tables are common and easy to miss when only scanning body text.
**Assert** — For documents without formulas, all three markers must be exactly zero.

### C6. Line breaks lost wholesale
**Symptom** — Form-like or list-like blocks run together into one paragraph.
**Detect** — Zero `<br>` occurrences in a document that is mostly parallel items.
**Repair** — Restore per-cell from the source.

### C7. Converter boilerplate retained
**Symptom** — Marketing phrases about the conversion, confidence notes, or watermark images.
**Repair** — Delete. Count by **lines**, not by occurrences: a phrase can appear twice on one line, so occurrence counts exceed line counts.

### C8. Typos: three origins, three verdicts
- **Converter error** → repair (character substitutions, dropped radicals, digit/letter confusion in IDs).
- **Source errata** → preserve, and note it. Reprints and standards carry known misprints; "correcting" them makes the document unfaithful.
- **Uncertain** → render the source and look. Never guess.

---

## D. Source-type specifics

### Scanned PDF (no text layer)
- Everything rests on rendering. Build a small tool with four modes: page render, region crop, thumbnail grid, and multi-page header strips (the last is the fastest way to read many captions or headings at once).
- Page mapping must be pinned to printed folio numbers, not PDF indices; multi-volume splits can shift the offset mid-document.
- Images fall into three classes with different handling: decorative/watermark → delete; whole-page scan residue → re-transcribe; genuine content figure → convert to text or rebuild as a table.

### Born-digital PDF
- Text layer exists → grep the source directly to settle any ambiguity. Far cheaper than rendering.
- Watch for ligature and hyphenation artifacts at line ends.

### Word / Excel / PowerPoint
- Word: style names carry the real hierarchy — use them instead of inference. Track-changes and hidden text must be dropped explicitly.
- Excel: merged cells are the dominant defect; the value lives in the anchor cell and all others are empty. Rebuild merges from the source's cell range map, not from the empties.
- PowerPoint: reading order is decided by shape z-order, which rarely matches visual order. Verify slide-by-slide.

### HTML / web pages
- Preserve or strip navigation chrome deliberately; don't let boilerplate become prose.
- Relative links and lazy-loaded images need absolute resolution or removal.

---

## E. Cross-cutting: what "zero loss" means

Do not prove losslessness by comparing line counts — structure repairs change line counts legitimately. Compare at the **cell/content unit** level: extract all non-empty normalized tokens from source and output, then diff. Symmetric additions and removals (same count, same kinds) indicate only formatting normalization; asymmetric removals indicate real loss.
