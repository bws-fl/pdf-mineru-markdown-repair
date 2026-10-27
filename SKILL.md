---
name: doc-conversion-audit
description: Audit and repair text produced by automated document conversion (MinerU, Pandoc, markitdown, docling, OCR, unstructured) from PDF, Word, Excel, PowerPoint, HTML, or scanned images into Markdown/HTML/plain text. Use when converted output has broken heading hierarchy, missing or misplaced table captions, malformed or wrongly-spanned tables, lost page continuations, OCR typos, mixed half/full-width punctuation, or when a conversion must be verified against its source before delivery. Triggers include "转出来的 md 有问题", "对比原件修正", "转换质量检查", "PDF 转 Markdown 校对", "表格错位", "标题层级乱了", "目录对不上", "帮我把这个转换结果修一下".
agent_created: true
---

# Document Conversion Audit

## Overview

Automated document conversion (MinerU, Pandoc, markitdown, docling, OCR pipelines) preserves *characters* but loses *structure*. The output is always a draft, never a deliverable: heading levels are assigned randomly, tables lose geometry, cross-page content merges or splits arbitrarily, and captions drift away from their objects.

This skill defines a reproducible audit-and-repair procedure that works for any source-to-text conversion, plus the discipline required to avoid "fixing" things that were never broken.

## Core Principles

Three rules govern everything below. Violating any one of them causes silent data loss.

1. **Never trust the converter's structure.** Heading levels, table numbering, caption placement, page breaks, and list nesting are all *guesses*. Rebuild them from authoritative signals: the source's table of contents, its numbering scheme, and its visual layout.

2. **Prove the measurement method before declaring a defect.** A wrong detector manufactures thousands of phantom defects and every subsequent "fix" destroys real data. If a check reports that most of the document is broken, the check is what's broken.

3. **Order repairs by ascending blast radius.** Encoding and character-level fixes first; structure and row-count-changing operations last. Any operation that adds or removes lines invalidates every line-number index computed before it.

## Step 1: Reconnaissance

Answer these before editing a single character. Each answer becomes an assertion later.

| Question | How to answer | Why it matters |
|---|---|---|
| Is the source machine-readable? | Extract text layer; if near-empty it's a scan | Scans allow **only** visual verification — every "the book says X" claim needs eyes on a rendered page |
| Source page ↔ output location mapping | Pin 3+ anchors (first body page, a chapter start, last table) | Needed to locate any flagged item in the source within one render |
| What is the authoritative structure? | Parse the printed table of contents / document outline | Sole ground truth for heading and caption reconstruction |
| How many objects are there? | Count tables, figures, formulas, footnotes in source vs output | The delta quantifies how much the converter dropped |
| What is the source's unit-page template? | Identify the repeating layout (e.g. every section = 3 fixed pages) | Turns layout knowledge into a checkable assertion |
| What is the numbering scheme? | Sample 5–10 instances of IDs, captions, clause numbers | Determines whether a "missing number" is a defect or the source's own convention |
| What punctuation convention does the source use? | Render 3–5 pages including inside tables | Half/full-width is a per-document fact, not a universal rule |

Record the answers as a short baseline note. Back up the file before touching it.

## Step 2: Layered Repair

Execute in this order. Finish and assert each layer before starting the next.

### Layer 1 — Encoding and line endings

Normalize BOM, line endings, and trailing whitespace. Convert line endings **before** any multi-line matching, or patterns written with `\n` will silently match nothing on `\r\n` files.

### Layer 2 — Heading hierarchy

Demote the converter's `#` markers to signals. Rebuild from numbering prefixes, not from the converter's levels: the same logical level routinely alternates between `#` and `##` within one document.

- Merge title fragments that were split onto their own line (an orphan line that is the tail of the previous sentence).
- Promote section headings the converter left as plain text (often recognizable by a missing space, e.g. `9.2Components`).
- Cross-check the heading list against the source's table of contents, one-to-one.

### Layer 3 — Specialized objects

Handle formulas, tables, figures, and footnotes. This layer carries the highest defect density — see `references/defect-catalog.md` for the full taxonomy. The highest-leverage checks:

- **Locate objects in every container the converter exposes.** Blocks are routinely written to more than one JSON key, with the primary key holding an empty shell. Reading only the obvious container silently drops entire object classes.
- **Classify tables by first-row signature** before touching them; different classes need different repairs.
- **Treat cross-page merges as split, not join.** When two tables were fused into one, split in place; moving the tail elsewhere reorders numbering.
- **Check table geometry with a grid simulation**, honoring rowspan occupancy. Summing colspan per row produces massive false positives.
- **Verify captions exist and sit adjacent to their object**, one caption per object, with a reciprocal primary/continuation relationship.

### Layer 4 — Text

- Apply the punctuation convention determined in reconnaissance, then re-scan for entities the conversion may have corrupted (entity terminators are a common casualty of half-to-full-width conversion).
- Handle ratio/colon-like glyphs **before** colon normalization, or the counts will not reconcile.
- Repair converter artifacts and typos, but preserve the source's own errata.
- Strip conversion boilerplate, watermarks, and externally-hosted images.

### Layer 5 — Numbering and cross-references

- Validate numbering by group continuity (each group runs 1..N) rather than by global uniqueness; this reliably surfaces OCR'd chapter numbers.
- Derive missing identifiers from the document's own convention — never invent a suffix pattern.
- Reconcile every table-of-contents entry against a body heading; report zero misses.

### Layer 6 — Final verification

Run `scripts/audit.py` and require every check to pass. See `references/checklist.md` for the assertion set and the false-positive traps each assertion must avoid.

## Step 3: Delivery

- Write the result back **next to the source material**, not into a scratch or download directory. Transit directories are routinely cleaned by system utilities; a backup there is not a backup.
- Name backups descriptively with a timestamp and the repair stage.
- Record what was deliberately **not** changed and why. Without this, the next pass re-litigates settled decisions and re-breaks confirmed conventions.

## Red Lines

Never change these without first rendering the corresponding source location:

1. Whether an identifier carries a suffix or not — the source may omit it by design.
2. Bracket and punctuation width — it is a per-document convention.
3. Whether a suspected typo belongs to the source or the converter.
4. Whether a blank table is a template or missing data.
5. Whether a running head exists on continuation pages.
6. Whether an image is decorative, a scan artifact, or real content.

Anything marked "leave as-is pending source access" during an earlier pass must be re-examined **first** once the source becomes available. In practice the whole "keep as-is" category is where prior judgments turn out wrong, and the interior of tables is not an exempt zone.

## Resources

- `scripts/audit.py` — runnable structural/encoding/punctuation audit for converted Markdown; prints PASS/FAIL per check and exits non-zero on failure.
- `references/defect-catalog.md` — defect taxonomy by source type, with symptom → root cause → repair.
- `references/checklist.md` — full assertion set, false-positive traps, and the repair-order rule.
- `references/case-water-standards.md` — worked case: 7 Chinese water-industry standards, with measured numbers. Use as calibration for expected defect density, not as a fixed rule set.
