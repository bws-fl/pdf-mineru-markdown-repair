#!/usr/bin/env python3
"""Structural audit for converted documents (Markdown in, report out).

Checks encoding, heading structure, tag pairing, converter residue, and
punctuation width. Prints one line per check with a measured count, so that
"clean" is distinguishable from "the check never ran".

Usage:
    python audit.py FILE [-h] [--json] [--cjk] [--max-lines N]

    --json      machine-readable output
    --cjk       treat half-width , ; : ( ) as defects (Chinese-text documents);
                without it those are reported as informational counts only,
                because half-width is correct for Latin-script documents
    --max-lines only process the first N lines (quick pass on huge files)

Exit code: 0 if no check failed, 1 otherwise.
"""

import argparse
import json
import re
import sys

TAG_RE = re.compile(r"</?[A-Za-z][A-Za-z0-9]*[^>]*>")
FENCE_RE = re.compile(r"^```")
ENTITY_TAIL_RE = re.compile(r"&([a-zA-Z]+)\uff1b")          # entity closed by full-width ;
FORMULA_TAGS = ("<eq>", "</eq>")
IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)]*)\)")


def read_document(path, max_lines=None):
    with open(path, "rb") as handle:
        raw = handle.read()
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig", errors="replace")
    crlf = raw.count(b"\r\n")
    bare_lf = raw.count(b"\n") - crlf
    bare_cr = raw.count(b"\r") - crlf
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    if max_lines:
        lines = lines[:max_lines]
        normalized = "\n".join(lines)
    return {
        "raw": raw,
        "text": text,
        "normalized": normalized,
        "lines": lines,
        "has_bom": has_bom,
        "bom_count": raw.count(b"\xef\xbb\xbf"),
        "crlf": crlf,
        "bare_lf": bare_lf,
        "bare_cr": bare_cr,
    }


def strip_code_fences(lines):
    """Return (prose_lines, code_line_count). Fenced blocks are excluded from
    punctuation analysis because code legitimately uses half-width symbols."""
    out, in_fence, code_lines = [], False, 0
    for line in lines:
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            code_lines += 1
            continue
        out.append(line)
    return out, code_lines


def count_headings(lines):
    counts = {}
    for line in lines:
        match = re.match(r"^(#{1,6})\s", line)
        if match:
            level = len(match.group(1))
            counts[level] = counts.get(level, 0) + 1
    return counts


def check(results, name, value, ok, detail="", strict=True):
    """Append one measurement. strict=False records INFO only (reported, never fatal)."""
    results.append({
        "check": name,
        "value": value,
        "detail": detail,
        "status": ("PASS" if ok else "FAIL") if strict else "INFO",
    })


def audit(path, cjk=False, max_lines=None):
    doc = read_document(path, max_lines)
    lines = doc["lines"]
    text = doc["normalized"]
    prose, code_lines = strip_code_fences(lines)
    prose_text = "\n".join(prose)
    visible = TAG_RE.sub("", prose_text)          # drop tags, keep their text

    # Punctuation rules only apply to Chinese prose. English sentences, URLs and
    # e-mail addresses legitimately use half-width marks, so exclude those lines
    # rather than forcing a whole-document decision.
    cjk_visible = "\n".join(
        line for line in visible.split("\n")
        if re.search(r"[\u4e00-\u9fff]", line)
        and "://" not in line
        and not re.search(r"[\w.+-]+@[\w.-]+\.\w+", line)
    )
    results = []

    # ---- encoding ----
    check(results, "BOM 唯一", doc["bom_count"],
          doc["bom_count"] == 1, "utf-8-sig writes exactly one")
    check(results, "行尾统一", doc["crlf"],
          doc["bare_lf"] == 0 and doc["bare_cr"] == 0,
          "bare LF=%d / bare CR=%d" % (doc["bare_lf"], doc["bare_cr"]))

    # ---- structure ----
    heads = count_headings(lines)
    deepest = max(heads) if heads else 0
    check(results, "标题层级", " ".join("h%d=%d" % (k, heads[k]) for k in sorted(heads)) or "none",
          True, "deepest=h%d" % deepest, strict=False)

    pairs = {}
    for tag in ("table", "tr", "td", "th"):
        opens = len(re.findall(r"<%s[\s>]" % tag, text))
        closes = len(re.findall(r"</%s>" % tag, text))
        if opens or closes:
            pairs[tag] = (opens, closes)
    unbalanced = {k: v for k, v in pairs.items() if v[0] != v[1]}
    check(results, "标签开闭配对", "; ".join("%s %d/%d" % (k, v[0], v[1]) for k, v in pairs.items()) or "no tags",
          not unbalanced, "" if not unbalanced else "不配对: %s" % ",".join(unbalanced),
          strict=bool(pairs))

    # ---- residue ----
    eq_count = sum(text.count(tag) for tag in FORMULA_TAGS)
    dollar = visible.count("$")
    check(results, "公式残留", "eq=%d dollar=%d" % (eq_count, dollar),
          eq_count == 0, "有公式的文档请忽略此项")

    images = IMG_RE.findall(text)
    remote = [u for u in images if u.startswith(("http://", "https://"))]
    check(results, "外链图片", "%d/%d remote" % (len(remote), len(images)),
          not remote, "离线交付必须为 0")

    runs = len(re.findall(r"\n{3,}", text))
    check(results, "3+ 连续空行", runs, runs == 0)
    ideo = text.count("\u3000")
    ideo_samples = sorted(set(re.findall(r".{0,5}\u3000.{0,5}", text)))[:3]
    check(results, "全角空格", ideo, True,
          "样例: %s；表单格位（如「共　页　第　页」）属原书版式应保留，正文缩进应清理"
          % (" | ".join(s.replace("\u3000", "·") for s in ideo_samples) if ideo_samples else "无"),
          strict=False)

    trailing = sum(1 for line in lines if line.startswith("#") and line != line.rstrip())
    check(results, "标题行尾空格", trailing, trailing == 0,
          "line != line.rstrip()，不要用 \\s$（会匹配 CRLF 的 \\r）")

    # ---- punctuation (informational unless --cjk) ----
    cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", visible))
    entity_semis = len(re.findall(r"&[a-zA-Z]+;", cjk_visible))   # entity terminators are legitimate
    punct = {
        ",": cjk_visible.count(","),
        ";": max(0, cjk_visible.count(";") - entity_semis),
        ":": cjk_visible.count(":"),
    }
    half_parens = len(re.findall(r"[()]", cjk_visible))
    paren_samples = sorted(set(re.findall(r"\([^()]{1,12}\)", cjk_visible)))[:4]
    tilde = cjk_visible.count("~")
    entity_tails = len(ENTITY_TAIL_RE.findall(text))
    check(results, "半角标点", ", %d  ; %d  : %d  ~ %d" % (punct[","], punct[";"], punct[":"], tilde),
          (not cjk) or (sum(punct.values()) == 0 and tilde == 0),
          "汉字 %d 个；分号已扣实体 %d 个；仅中文行参与判定（英文行/URL/邮箱已排除），代码行 %d 行已排除"
          % (cjk_chars, entity_semis, code_lines),
          strict=cjk)
    check(results, "半角括号", half_parens,
          (not cjk) or half_parens == 0,
          "样例: %s" % (" ".join(paren_samples) if paren_samples else "无") +
          "；区号/型号/代码中的半角括号属合法例外", strict=False)
    check(results, "实体被全角化", entity_tails, entity_tails == 0,
          "形如 &lt； 的实体会失去终止符")

    # ---- objects ----
    n_table = len(re.findall(r"<table[\s>]", text))
    caps = len(re.findall(r"(?m)^\s*(?:continued\s+|续)?表\s*[\dA-Z]", text))
    check(results, "表格/表题", "tables=%d captions=%d" % (n_table, caps),
          True, "差额 %d（封面/版权/索引等非正文表）" % (n_table - caps), strict=False)

    # ---- totals ----
    results.append({"check": "规模", "value": "%d bytes / %d lines"
                    % (len(doc["raw"]), len(lines)), "detail": "", "status": "INFO"})
    return results


def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("file")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--cjk", action="store_true")
    parser.add_argument("--max-lines", type=int, default=None)
    args = parser.parse_args()

    results = audit(args.file, cjk=args.cjk, max_lines=args.max_lines)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        failed = 0
        for item in results:
            if item["status"] == "FAIL":
                failed += 1
            print("%-5s %-16s %-52s %s"
                  % (item["status"], item["check"], item["value"], item["detail"]))
        print("\n%d check(s) failed" % failed if failed else "\nall checks passed")

    sys.exit(1 if any(r["status"] == "FAIL" for r in results) else 0)


if __name__ == "__main__":
    main()
