"""The site header shared by every chomper page: the chomper name (home), then the main menu.

Pages one folder down pass prefix="../" so every link resolves from where the page lives.
"""

MENU = [("index.html", "All"), ("decisions.html", "Decisioning")]

CSS = """
.menu { display: flex; flex-wrap: wrap; align-items: center; gap: .25rem; margin: 0 0 1.5rem;
  padding-bottom: .75rem; border-bottom: 1px solid var(--rule); }
.menu a { padding: .3rem .65rem; border-radius: 4px; text-decoration: none; font-size: .9rem; font-weight: 600;
  color: var(--ink-2); }
.menu a:hover { background: var(--rule); }
.menu a[aria-current="page"] { background: var(--ink); color: var(--bg); }
.menu a.brand { color: var(--ink); font-size: 1.05rem; padding-left: 0; margin-right: .75rem; }
.menu a.brand:hover { background: none; text-decoration: underline; }
.crossref { font-size: .9rem; color: var(--ink-2); margin: 0 0 1rem; }
"""


def nav(current=None, prefix=""):
    """current: the menu href of the page being built, or None for pages outside the menu."""
    here = ' aria-current="page"'
    links = "".join(f'<a href="{prefix}{href}"{here if href == current else ""}>{label}</a>'
                    for href, label in MENU)
    return f'<nav class="menu"><a class="brand" href="{prefix}index.html">chomper</a>{links}</nav>'
