"""Static page generator for the research and software pages.

One shared shell (head, nav, hero, footer) so every page stays
byte-consistent with the hand-built project pages; only the body
sections differ. Run from repo root; writes into site/.
"""
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent / "site"

SHELL_TOP = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#0B1220">
<title>{title} - Nooruldeen Mustafa</title>
<meta name="description" content="{desc}">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>

<header class="nav">
  <div class="wrap nav-inner">
    <a class="brand" href="index.html" aria-label="Home">
      <svg class="glyph" viewBox="0 0 32 32" aria-hidden="true">
        <line x1="8" y1="12" x2="20" y2="12" stroke="#4FD1C5" stroke-width="2.4" stroke-linecap="round"/>
        <line x1="20" y1="12" x2="25" y2="22" stroke="#FF8A5B" stroke-width="2.4" stroke-linecap="round"/>
        <circle cx="8" cy="12" r="3" fill="#0B1220" stroke="#4FD1C5" stroke-width="2.4"/>
        <circle cx="20" cy="12" r="2.6" fill="#0B1220" stroke="#E8EDF4" stroke-width="2.2"/>
        <circle cx="25" cy="22" r="2.6" fill="#FF8A5B"/>
      </svg>
      Nooruldeen Mustafa
    </a>
    <button class="nav-toggle" aria-label="Menu">
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M2 5h14M2 9h14M2 13h14"/></svg>
    </button>
    <nav class="nav-links">
      <a href="research.html">research</a>
      <a href="index.html#projects">projects</a>
      <a href="software.html">software</a>
      <a href="index.html#about">about</a>
      <a class="gh" href="https://github.com/nem6557-cmyk/nem-portfolio" target="_blank" rel="noopener">GitHub</a>
    </nav>
  </div>
</header>

<section class="doc-hero wrap">
  <a class="back" href="{back_href}">&larr; {back_label}</a>
  <span class="eyebrow real">{eyebrow}</span>
  <h1>{h1}</h1>
  <p class="lede">{lede}</p>
  <div class="tags">{tags}</div>
  <div class="readout-bar">{readout}</div>
</section>

<div class="wrap">
<div class="doc" id="main">
"""

SHELL_BOTTOM = """
</div>
</div>

<nav class="wrap next-nav">
  <a href="{prev_href}">&larr; {prev_label}</a>
  <a href="{next_href}">{next_label} &rarr;</a>
</nav>

<footer class="footer">
  <div class="wrap">
    <div class="colophon">
      <span>{colophon}</span>
      <span>&copy; <span id="year">2026</span> Nooruldeen Mustafa</span>
    </div>
  </div>
</footer>

<script src="main.js"></script>
</body>
</html>
"""

def tag(t): return f'<span class="tag">{t}</span>'
def cell(val, lbl, real=True):
    c = ' real' if real else ''
    return (f'<div class="cell{c}"><div class="val">{val}</div>'
            f'<div class="lbl">{lbl}</div></div>')

def build(fname, **kw):
    kw["tags"] = "".join(tag(t) for t in kw["tags"])
    kw["readout"] = "".join(kw["readout"])
    body = kw.pop("body")
    html = SHELL_TOP.format(**kw) + body + SHELL_BOTTOM.format(**kw)
    (SITE / fname).write_text(html)
    print("wrote", fname)

if __name__ == "__main__":
    import pages_content
    for fname, kw in pages_content.PAGES.items():
        build(fname, **kw)
