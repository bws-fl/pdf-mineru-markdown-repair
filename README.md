# PDF-MinerU-Markdown-Repair

A WorkBuddy skill for repairing Markdown produced by **MinerU** from scanned or born-digital PDFs — and, since the failure modes are shared, the equivalent output of Pandoc, markitdown, docling and OCR pipelines from Word, Excel, PowerPoint or images.

MinerU preserves characters and loses structure. Heading levels get assigned by font-size heuristics, tables lose their geometry, a table spanning two pages merges into one block or splits without a marker, and captions drift away from the objects they name. The output is always a draft, never a deliverable.

This skill encodes a reproducible repair procedure plus the discipline needed to avoid "fixing" things that were never broken — the source's own misprints, its numbering conventions, and its deliberate layout.

## What it covers

| Category | Examples |
|---|---|
| Structure | Random heading levels, title fragments split onto their own line, section headings left as plain text, appendix level demotion |
| Tables | Objects present only in a secondary JSON container, two tables fused into one, unmarked continuation pages, wrong column spans shifting a whole row, fused cells, four distinct caption failures |
| Text | Mixed half/full-width punctuation, HTML entities corrupted by width conversion, ratio glyph vs colon, tilde becoming strikethrough, converter boilerplate |
| Scanned PDF | No text layer (render-only verification), page-folio mapping, page-template assertions, three-class image triage |
| Other sources | Word style hierarchy, Excel merged cells, PowerPoint shape order, HTML navigation chrome |

## Install

Clone into your WorkBuddy skills folder. The directory name must match the `name` field in `SKILL.md` (`pdf-mineru-markdown-repair`) — clone it as-is, no rename needed:

```bash
git clone https://github.com/bws-fl/pdf-mineru-markdown-repair.git \
          ~/.workbuddy/skills/pdf-mineru-markdown-repair
```

From a local copy of the repository:

```bash
# user-level: available in all projects
cp -r pdf-mineru-markdown-repair ~/.workbuddy/skills/

# project-level: shared with everyone using the repository
cp -r pdf-mineru-markdown-repair .workbuddy/skills/
```

## Use

Ask in natural language — the skill triggers on requests like:

- "PDF 转出来的 md 有问题，对比原件修一下"
- "MinerU 结果表格错位了"
- "标题层级乱了" / "目录对不上"
- "PDF 转 Markdown 校对"

Or run the standalone audit script on any converted file:

```bash
python scripts/audit.py FILE.md            # structural report
python scripts/audit.py FILE.md --cjk      # also treat half-width , ; : ~ as defects
python scripts/audit.py FILE.md --json     # machine-readable
```

Sample output on a clean 752-page conversion:

```
PASS  BOM 唯一           1
PASS  行尾统一           8532          bare LF=0 / bare CR=0
INFO  标题层级           h1=10 h2=110 h3=89
PASS  标签开闭配对        table 647/647; tr 8408/8408; td 39763/39763
PASS  公式残留           eq=0 dollar=0
PASS  外链图片           0/0 remote
PASS  3+ 连续空行        0
PASS  标题行尾空格        0
PASS  半角标点           , 0  ; 0  : 0  ~ 0
INFO  半角括号           4             样例: (010)
INFO  表格/表题          tables=647 captions=646
```

Exit code is non-zero when any check fails, so it drops straight into a pipeline.

## Core principles

1. **Never trust the converter's structure.** Heading levels, table numbering, caption placement, and page breaks are all guesses. Rebuild them from the source's table of contents, numbering scheme, and visual layout.

2. **Prove the measurement method before declaring a defect.** A wrong detector manufactures thousands of phantom defects, and every "fix" driven by it destroys real data. One colspan check once flagged 609 of 647 tables; rowspan-aware grid simulation showed only 7 were genuinely wrong.

3. **Order repairs by ascending blast radius.** Encoding first, structure last. Any operation that adds or removes lines invalidates every line-number index computed before it.

## Contents

```
SKILL.md                            three principles, 7-question recon, six repair layers, 6 red lines
references/defect-catalog.md        defect taxonomy: structure A1-A4, tables B1-B8, text C1-C8, per-source-type
references/checklist.md             five assertion classes, 7 false-positive traps, repair-order rule
references/case-water-standards.md  worked case: 7 Chinese water-industry standards with measured numbers
scripts/audit.py                    standalone structural audit, stdlib only
```

The case file holds the measurements; `SKILL.md` holds only what transfers between documents. Numbers there are calibration for expected defect density, not rules to apply blindly.

## Requirements

Python 3.8+. `audit.py` uses the standard library only. Rendering source pages for visual verification needs PyMuPDF, used ad hoc rather than by the script.

## License

MIT — see [LICENSE](LICENSE).
