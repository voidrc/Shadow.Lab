# Shadow.Wiki — Markdown Format Guide

> Reference for writing `.md` notes that convert cleanly into Presenter slide decks via `md2deck.py`.

---

## How it works

Each `.md` file becomes **one deck**. Slides are generated from the heading structure:

| Markdown element | → Slide result |
|---|---|
| `# H1` | Title card slide (centered, large, zoom transition) |
| `## H2` | Section slide (title at top, content below) |
| `### H3` | Treated as a sub-header bullet on the current slide |
| ` ```code``` ` | Standalone code slide (dark bg, neon green mono text) |
| `- item` / `* item` | Bullet points on the current section slide |
| `\| table \|` | Each row → one bullet (`col1  ::  col2  ::  col3`) |
| `> blockquote` | Subtitle text on the current slide |
| Plain paragraph | Body text on the current slide |

---

## File structure

```
# Topic Title
> Short description or tagline (becomes subtitle on title card)

## First Section
Short intro paragraph (body text).

- Point one
- Point two
- Point three

## Second Section
> Optional subtitle for this section

| Tool     | Purpose          |
|----------|------------------|
| nmap     | Port scanning    |
| gobuster | Dir enumeration  |

## Code Example

\```bash
nmap -sV -p- 10.10.10.1
\```
```

---

## Rules & best practices

### Headings

- **Always start with a single `# H1`** — this becomes the title card. Without it, there is no title slide.
- Use `## H2` for each major topic/section. Each `##` starts a new slide.
- `### H3` is treated as a bullet prefix, not a new slide. Use it sparingly.
- Do **not** skip levels (e.g. jumping from `#` to `###`).

### Blockquotes

- A `>` right after `# H1` becomes the **subtitle on the title card**.
- A `>` right after `## H2` becomes the **subtitle on that section slide**.
- Blockquotes elsewhere (e.g. navigation links like `> ← Back`) are **ignored** if they contain markdown links.

### Bullet lists

- Use `-` or `*` for bullets. Nested lists are flattened.
- Keep bullets short — they render as single lines on the slide.
- Each `## H2` section gets its own set of bullets. Don't mix unrelated lists under one heading.

### Tables

- Tables are converted to bullets using `col1  ::  col2  ::  col3` format.
- The header row becomes the first bullet.
- Separator rows (`|---|---|`) are ignored automatically.
- Best for: tool lists, command references, comparisons.

### Code blocks

- Use triple backtick fences with an optional language hint:
  ````
  ```bash
  your code here
  ```
  ````
- Each code block becomes its own slide, titled after the current section.
- If a section has **multiple code blocks**, each gets a separate slide.
- Keep code blocks focused — long blocks get clipped on small screens.

### Plain text / paragraphs

- A paragraph under a `## H2` becomes **body text** on that slide.
- Body text and bullets on the same slide both render — body appears above bullets.
- Avoid long paragraphs; use bullets instead for readability in presentations.

### Inline formatting

All inline markdown is **stripped** during conversion — bold, italic, inline code, and links become plain text. Write content as if it will be read without formatting.

---

## What to avoid

- **Images** — `![alt](url)` is ignored. Slides don't embed wiki images.
- **HTML tags** — raw HTML blocks are treated as plain text.
- **Deeply nested lists** — only the top level is captured.
- **Multiple `# H1` headings** — only the first one becomes the title card; subsequent H1s start a new section slide.
- **Leaving `## H2` with no content** — an empty section produces no slide and is silently skipped.

---

## Minimal working example

```markdown
# GPG Encryption
> Encrypt, sign, and manage keys with GNU Privacy Guard

## What is GPG?
GPG is an open-source implementation of the OpenPGP standard.

- Asymmetric encryption using public/private key pairs
- Used for email signing, file encryption, and package verification
- Pre-installed on most Linux distros

## Generate a Key Pair

\```bash
gpg --full-generate-key
\```

## Key Management

| Command | Action |
|---|---|
| gpg --list-keys | List all public keys |
| gpg --list-secret-keys | List private keys |
| gpg --delete-key NAME | Remove a public key |
```

This produces **5 slides**: title card + 3 section slides + 1 code slide.

---

## Running the converter

```bash
# Convert all .md files (skips already-existing decks)
python3 md2deck.py

# Convert a single file
python3 md2deck.py tools/GPG.md

# Force regenerate: delete the existing deck first
rm presenter/decks/tools/gpg.json
python3 md2deck.py tools/GPG.md
```

Output goes to `presenter/decks/<category>/<name>.json`.  
The manifest at `presenter/decks/index.json` is always rebuilt on every run.
