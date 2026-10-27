# Case: Seven Chinese Water-Industry Standards

Worked example used to calibrate expected defect density. **Numbers are measurements, not rules** — a different document set will have a different distribution.

## Corpus

All sources were pure scan PDFs (612×792 pt, one full-page image per page, **zero text layer**), converted with MinerU, then audited page-by-page against renders.

| Document | Lines | Tables | Continuations | h1 | h2 | Page offset |
|---|---|---|---|---|---|---|
| SL/T 631.1-2025 Earthwork | 1164 | 72 | 30 | 18 | 36 | — |
| SL/T 631.2-2025 Concrete | 1521 | 105 | 34 | 23 | 43 | −6 (p≤93) / −5 (p≥94) |
| SL/T 631.3-2025 Ground treatment | 1616 | 91 | 21 | 20 | 45 | +6 |
| SL/T 631.4-2025 Levee & river training | 1370 | 75 | 20 | 21 | 32 | +5 |
| SL/T 824-2024 Records archiving | 960 | 17 | 0 | 18 | 30 | +4 |
| SL 631-2025 Inspection/acceptance forms (1 volume, 4 parts merged) | 8533 | 647 | 134 | 10 | 110 | +11 (no shift) |
| SL/T 223-2025 Acceptance code | 2457 | 17 | 0 | 15 | 186 | not audited |

Note the last column: the offset is **not constant across the corpus**, and in one document it changes mid-file because a volume split added a page. Pin offsets per document; never reuse one.

## What the audit actually found (631 forms volume, 752 pages)

Repairs applied, in execution order:

| Volume of defect | Count |
|---|---|
| Half-width punctuation inside tables | 5784 commas / 231 semicolons / 3479 colons / 1642 bracket pairs |
| Ratio glyphs normalized | 6 |
| Date ranges with hyphen instead of en-dash | 270 |
| Captions with a lost identifier | 30 |
| Captions glued to a following field label | 38 |
| Captions split across two lines | 72 |
| Continuation captions inserted | 108 |
| Continuation caption format normalized | 26 |
| Space after enumerated parentheses removed | 549 |
| OCR errors corrected | 5 |

The 647 tables broke down as 512 primary captions + 134 continuations + 1 copyright-page table. Orphan continuations: 0. Uncaptioned tables: 0.

## Three judgments that were reversed by access to the source

This is the most transferable part of the case.

**1. "Leave table-interior punctuation as-is."** Made during a pass without source access, on the reasoning that table interiors were a separate convention zone. Rendering showed table interiors used **full-width punctuation exactly like body text**. The whole "exempt zone" assumption was wrong, and it affected ~11,000 characters.

**2. "132 adjacent table pairs are unmarked continuations, don't merge them."** Assumption was that continuing pages carry no label. Rendering confirmed: most continuing pages repeat only the header row and print no "continued" marker. Conclusion was right (keep them split) but the action was incomplete — each needed a continuation caption inserted. 108 were missing one.

**3. "7 tables have over-counted header spans."** Reported by a checker that summed `colspan` per row. Applying rowspan-aware grid simulation showed the same 7 were genuine but the checker had *also* flagged 609 correct tables. The original measurement was wrong by two orders of magnitude; the 7 were real, but the number that mattered was "the detector is unreliable", not "609 tables are broken".

## Numbering convention that look like defects but are not

Extracted from the source by sampling, not from a rule book:

| Form | Example | Meaning |
|---|---|---|
| Bare | `表 2.2`, `表 4.19` | Section prints a single acceptance table — **no `-2` suffix** |
| Pair | `表 X.Y-1` / `表 X.Y-2` | Section prints both a check table and an acceptance table |
| Sub-process | `表 X.Y.N-1/-2` | |
| Qualified | `表 3.1（单孔）-1` | Full-width parentheses around the qualifier |
| Item table | `表 A-1` (source prints `表 A - 1`) | Normalized in output |

A restoration pass driven by a single assumed pattern would have added suffixes to ~90 bare captions and deleted qualifiers from others.

## Layout template as an assertion

Each section occupied exactly three pages: section heading + item tables, then the check table, then the acceptance table. Sections with sub-processes ran longer.

Knowing this made verification cheap: "page 3 of a section should be the acceptance table" is a checkable claim. Building the equivalent template for a new document set is usually the highest-return reconnaissance step.

## Operational note

Finished files were written back to the directory holding the source PDFs. Staging copies placed in the system download folder were wiped by a cleanup utility mid-task — the staging directory is not storage. Backups written only there were lost; the deliverables survived only because they had already been copied to the archive directory.
