#!/usr/bin/env python3
"""
md2deck.py — Convert Shadow.Wiki Markdown notes into Presenter JSON slide decks.

Usage:
  python3 md2deck.py                        # convert ALL new .md files in the wiki
  python3 md2deck.py linux/CLI.md           # convert a single file
  python3 md2deck.py linux/ tools/          # convert specific folders
  python3 md2deck.py --force linux/CLI.md   # overwrite existing deck
  python3 md2deck.py --all --force          # regenerate every deck

Output:
  presenter/decks/<category>/<name>.json    # one deck per .md file
  presenter/decks/index.json               # manifest of all decks

Slide generation rules:
  # H1         → Title card slide (title + subtitle from first blockquote/paragraph)
  ## H2        → New section slide (title + accumulated content below it)
  ### H3       → Sub-slide bullet header
  ```code```   → Code block slide appended to current section
  - / * list   → Bullet points on current slide
  tables       → Converted to bullet points
  blockquotes  → Subtitle / caption text
  plain text   → Body text
"""

import argparse
import json
import re
import sys
import os
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────
WIKI_ROOT   = Path(__file__).parent
DECKS_DIR   = WIKI_ROOT / "presenter" / "decks"
INDEX_FILE  = DECKS_DIR / "index.json"

# Cyber theme defaults (match Presenter cyber theme)
THEME = {
    "bgType":       "gradient",
    "bgGradient":   "linear-gradient(160deg,#030803 0%,#061206 100%)",
    "titleColor":   "#00ff41",
    "subtitleColor":"#2a6b3a",
    "bodyColor":    "#7ab87a",
    "fontFamily":   "'Courier New', 'Fira Mono', monospace",
    "textAlign":    "left",
    "transition":   "slide-r",
}

TITLE_SLIDE_THEME = {
    **THEME,
    "bgGradient":  "linear-gradient(160deg,#020602 0%,#051505 40%,#020a02 100%)",
    "titleSize":   52,
    "textAlign":   "center",
    "transition":  "zoom",
    "layout":      "center",
}

CODE_SLIDE_THEME = {
    **THEME,
    "bgGradient":  "linear-gradient(160deg,#020602 0%,#040d04 100%)",
    "layout":      "top",
    "transition":  "fade",
}

SECTION_SLIDE_THEME = {
    **THEME,
    "layout":      "top",
}

# ─── Helpers ──────────────────────────────────────────────────────────────────
_uuid_counter = 0
def new_id():
    import uuid
    return str(uuid.uuid4())

def slug(text):
    """Turn text into a safe filename slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return text[:60]

def strip_md_inline(text):
    """Remove inline markdown: **bold**, *italic*, `code`, [text](url)."""
    text = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', text)  # links
    text = re.sub(r'`([^`]+)`', r'\1', text)               # inline code
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)         # bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)             # italic
    text = re.sub(r'__([^_]+)__', r'\1', text)             # bold alt
    text = re.sub(r'_([^_]+)_', r'\1', text)               # italic alt
    return text.strip()

def table_to_data(lines):
    """Parse a markdown table into {headers: [], rows: [[]]}."""
    headers = []
    rows = []
    header_done = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Separator row: | --- | :---: | etc.
        if re.match(r'^\|[\s\-:]+([\|][\s\-:]+)+\|?\s*$', line):
            header_done = True
            continue
        cells = [strip_md_inline(c.strip()) for c in line.strip('|').split('|') if c.strip()]
        if not cells:
            continue
        if not header_done:
            headers = cells
            header_done = True  # first row = header
        else:
            rows.append(cells)
    return {"headers": headers, "rows": rows}

def default_slide(overrides=None):
    base = {
        "id":           new_id(),
        "layout":       "top",
        "bgType":       "gradient",
        "bgColor":      "#080b08",
        "bgGradient":   THEME["bgGradient"],
        "bgImage":      "",
        "titleText":    "",
        "titleColor":   THEME["titleColor"],
        "titleSize":    48,
        "subtitleText": "",
        "subtitleColor":THEME["subtitleColor"],
        "bodyText":     "",
        "bodyColor":    THEME["bodyColor"],
        "bodySize":     22,
        "bullets":      [],
        "tableData":    {"headers": [], "rows": []},
        "codeText":     "",
        "codeLang":     "",
        "imageUrl":     "",
        "showTitle":    True,
        "showSubtitle": False,
        "showBody":     False,
        "showBullets":  False,
        "showTable":    False,
        "showCode":     False,
        "showImage":    False,
        "textAlign":    THEME["textAlign"],
        "fontFamily":   THEME["fontFamily"],
        "transition":   THEME["transition"],
    }
    if overrides:
        base.update(overrides)
    return base


# ─── Parser ────────────────────────────────────────────────────────────────────
class MdParser:
    def __init__(self, text, source_path):
        self.lines = text.splitlines()
        self.source = source_path
        self.slides = []
        self.pos = 0

    def peek(self):
        if self.pos < len(self.lines):
            return self.lines[self.pos]
        return None

    def consume(self):
        line = self.lines[self.pos]
        self.pos += 1
        return line

    def parse(self):
        current = None          # slide being built
        pending_body = []       # plain text lines
        pending_bullets = []    # bullet lines
        pending_tables = []     # table dicts
        in_code = False
        code_lines = []
        code_lang = ""
        in_table = False
        table_lines = []

        def flush_body_bullets(slide):
            """Apply accumulated body/bullets/tables to the slide."""
            if not slide:
                return
            if pending_bullets:
                slide["bullets"] = list(pending_bullets)
                slide["showBullets"] = True
                pending_bullets.clear()
            if pending_tables:
                # Use the first table; subsequent tables become bullets fallback
                slide["tableData"] = pending_tables[0]
                slide["showTable"] = True
                pending_tables.clear()
            if pending_body:
                body = "\n".join(pending_body).strip()
                if body:
                    if slide["bodyText"]:
                        slide["bodyText"] += "\n" + body
                    else:
                        slide["bodyText"] = body
                    slide["showBody"] = True
                pending_body.clear()

        def push(slide):
            if slide:
                flush_body_bullets(slide)
                # Only add slide if it has real content
                has_content = (
                    slide.get("titleText") or
                    slide.get("bodyText") or
                    slide.get("bullets") or
                    slide.get("codeText") or
                    slide.get("subtitleText")
                )
                if has_content:
                    self.slides.append(slide)

        while self.pos < len(self.lines):
            line = self.consume()

            # ── Code fence ──
            if line.strip().startswith("```"):
                if not in_code:
                    in_code = True
                    code_lang = line.strip()[3:].strip()
                    code_lines = []
                else:
                    in_code = False
                    code = "\n".join(code_lines).strip()
                    if code:
                        # If current slide already has code, push it and start fresh
                        if current and current.get("codeText"):
                            push(current)
                            current = default_slide({
                                **CODE_SLIDE_THEME,
                                "id": new_id(),
                                "titleText":    current["titleText"],
                                "subtitleText": "",
                            })
                            pending_body.clear()
                            pending_bullets.clear()
                        elif current is None:
                            current = default_slide({**CODE_SLIDE_THEME, "id": new_id()})
                        else:
                            # Section slide with only a title and no other content →
                            # reuse it as the code slide (avoids a wasted empty slide)
                            slide_is_title_only = (
                                not current.get("bodyText") and
                                not current.get("bullets") and
                                not current.get("subtitleText") and
                                not pending_body and
                                not pending_bullets
                            )
                            if slide_is_title_only:
                                current.update(CODE_SLIDE_THEME)
                        flush_body_bullets(current)
                        current["codeText"] = code
                        current["codeLang"] = code_lang
                        current["showCode"] = True
                    code_lines = []
                    code_lang = ""
                continue

            if in_code:
                code_lines.append(line)
                continue

            # ── Table detection ──
            if '|' in line and line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                    table_lines = []
                table_lines.append(line)
                continue
            else:
                if in_table:
                    in_table = False
                    td = table_to_data(table_lines)
                    if td["headers"] and td["rows"]:
                        pending_tables.append(td)
                    table_lines = []

            # ── H1 — title card ──
            if line.startswith("# ") and not line.startswith("## "):
                push(current)
                pending_body.clear()
                pending_bullets.clear()
                pending_tables.clear()
                title = strip_md_inline(line[2:].strip())
                current = default_slide({
                    **TITLE_SLIDE_THEME,
                    "id": new_id(),
                    "titleText": title,
                })
                continue

            # ── H2 — section slide ──
            if line.startswith("## ") and not line.startswith("### "):
                push(current)
                pending_body.clear()
                pending_bullets.clear()
                pending_tables.clear()
                title = strip_md_inline(line[3:].strip())
                current = default_slide({
                    **SECTION_SLIDE_THEME,
                    "id": new_id(),
                    "titleText": title,
                })
                continue

            # ── H3 — sub-heading becomes bold bullet / new slide ──
            if line.startswith("### "):
                # Flush existing content and start a new slide with this as title
                push(current)
                pending_body.clear()
                pending_bullets.clear()
                pending_tables.clear()
                title = strip_md_inline(line[4:].strip())
                current = default_slide({
                    **SECTION_SLIDE_THEME,
                    "id": new_id(),
                    "titleText": title,
                    "titleSize": 36,
                })
                continue

            # ── Blockquote → subtitle ──
            if line.startswith("> "):
                text = strip_md_inline(line[2:].strip())
                # Skip navigation links (Previous/Next)
                if re.search(r'\b(previous|next)\b', text, re.I):
                    continue
                if current and not current["subtitleText"]:
                    current["subtitleText"] = text
                    current["showSubtitle"] = True
                continue

            # ── Bullet / list item ──
            m = re.match(r'^(\s*)([-*+]|\d+\.)\s+(.*)', line)
            if m:
                text = strip_md_inline(m.group(3))
                if text:
                    pending_bullets.append(text)
                continue

            # ── Horizontal rule — section break ──
            if re.match(r'^[-*_]{3,}\s*$', line):
                continue

            # ── Blank line ──
            if not line.strip():
                continue

            # ── Plain paragraph text ──
            text = strip_md_inline(line.strip())
            if text:
                pending_body.append(text)

        # Flush table if file ended mid-table
        if in_table and table_lines:
            td = table_to_data(table_lines)
            if td["headers"] and td["rows"]:
                pending_tables.append(td)

        push(current)
        return self.slides


# ─── Convert one file ─────────────────────────────────────────────────────────
def convert_file(md_path: Path) -> dict | None:
    """Convert a single .md file to a deck dict. Returns None if no slides."""
    text = md_path.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        return None

    parser = MdParser(text, md_path)
    slides = parser.parse()

    if not slides:
        return None

    # Determine category from parent folder name
    rel = md_path.relative_to(WIKI_ROOT)
    parts = rel.parts
    category = parts[0] if len(parts) > 1 else "misc"
    name = md_path.stem

    # Title: first H1 or filename
    title = name
    for s in slides:
        if s.get("titleText"):
            title = s["titleText"].lstrip("/#> ").strip()
            break

    return {
        "title":    title,
        "category": category,
        "source":   str(rel),
        "slides":   slides,
        "transition": "fade",
    }


# ─── Write deck ───────────────────────────────────────────────────────────────
def write_deck(deck: dict, md_path: Path, force: bool = False) -> Path | None:
    rel = md_path.relative_to(WIKI_ROOT)
    parts = rel.parts
    category = parts[0] if len(parts) > 1 else "misc"
    out_dir = DECKS_DIR / category
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / (slug(md_path.stem) + ".json")
    if out_file.exists() and not force:
        return None  # already exists — do not overwrite
    out_file.write_text(json.dumps(deck, indent=2, ensure_ascii=False))
    return out_file


# ─── Build index ──────────────────────────────────────────────────────────────
def build_index():
    """Scan decks/ and write index.json manifest."""
    entries = []
    for json_file in sorted(DECKS_DIR.rglob("*.json")):
        if json_file.name == "index.json":
            continue
        try:
            data = json.loads(json_file.read_text())
            rel = json_file.relative_to(DECKS_DIR)
            entries.append({
                "title":    data.get("title", json_file.stem),
                "category": data.get("category", "misc"),
                "source":   data.get("source", ""),
                "slides":   len(data.get("slides", [])),
                "path":     str(rel).replace("\\", "/"),
            })
        except Exception:
            pass

    # Group by category
    categories = {}
    for e in entries:
        cat = e["category"]
        categories.setdefault(cat, []).append(e)

    index = {"categories": categories, "total": len(entries)}
    DECKS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, indent=2, ensure_ascii=False))
    return len(entries)


# ─── Collect target files ─────────────────────────────────────────────────────
SKIP_PATTERNS = re.compile(
    r'(^README\.md$|presenter/|node_modules/|\.git/)',
    re.IGNORECASE
)

def collect_md_files(targets: list[str]) -> list[Path]:
    files = []
    if not targets:
        # All .md files in wiki root
        for f in WIKI_ROOT.rglob("*.md"):
            rel = str(f.relative_to(WIKI_ROOT))
            if not SKIP_PATTERNS.search(rel):
                files.append(f)
    else:
        for t in targets:
            p = Path(t)
            if not p.is_absolute():
                p = WIKI_ROOT / p
            if p.is_file() and p.suffix == ".md":
                files.append(p)
            elif p.is_dir():
                for f in sorted(p.rglob("*.md")):
                    rel = str(f.relative_to(WIKI_ROOT))
                    if not SKIP_PATTERNS.search(rel):
                        files.append(f)
            else:
                print(f"  [WARN] Not found: {t}")
    return sorted(set(files))


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        prog="md2deck.py",
        description="Convert Shadow.Wiki Markdown files into Presenter JSON slide decks.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        metavar="PATH",
        help=".md files or directories to convert (omit to convert all new files)",
    )
    parser.add_argument(
        "-f", "--force",
        action="store_true",
        help="overwrite existing decks instead of skipping them",
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="convert all .md files in the wiki (same as omitting PATH arguments)",
    )
    args = parser.parse_args()

    targets = [] if args.all else args.paths
    files = collect_md_files(targets)

    if not files:
        print("[!] No .md files found.")
        sys.exit(1)

    force_label = "  [force=on]" if args.force else ""
    print(f"[*] Converting {len(files)} file(s) → presenter/decks/{force_label}\n")
    ok = 0
    skipped = 0

    for md_path in files:
        rel = md_path.relative_to(WIKI_ROOT)
        try:
            deck = convert_file(md_path)
            if deck is None:
                print(f"  [SKIP] {rel}  (empty)")
                skipped += 1
                continue
            out = write_deck(deck, md_path, force=args.force)
            if out is None:
                print(f"  [EXIST] {rel}  (skipped — use --force to overwrite)")
                skipped += 1
                continue
            slide_count = len(deck["slides"])
            print(f"  [OK]  {rel}  →  {out.relative_to(WIKI_ROOT)}  ({slide_count} slides)")
            ok += 1
        except Exception as e:
            print(f"  [ERR] {rel}  —  {e}")
            skipped += 1

    print(f"\n[*] Building index...")
    total = build_index()
    print(f"[+] Done. {ok} decks written, {skipped} skipped. Index: {total} total decks.")
    print(f"[+] Output: {DECKS_DIR.relative_to(WIKI_ROOT)}/")


if __name__ == "__main__":
    main()
