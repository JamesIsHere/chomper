"""The site header shared by every Chomper page: the main menu, Chomper (home), Decisioning, Considerations.

Pages one folder down pass prefix="../" so every link resolves from where the page lives.
"""

MENU = [("index.html", "Chomper"), ("decisions.html", "Decisioning"), ("considerations.html", "Considerations")]

CSS = """
.menu { display: flex; flex-wrap: wrap; align-items: center; gap: .25rem; margin: 0 0 1.5rem;
  padding-bottom: .75rem; border-bottom: 1px solid var(--rule); }
.menu a { padding: .3rem .65rem; border-radius: 4px; text-decoration: none; font-size: .9rem; font-weight: 600;
  color: var(--ink-2); }
.menu a:hover { background: var(--rule); }
.menu a[aria-current="page"] { background: var(--ink); color: var(--bg); }
.crossref { font-size: .9rem; color: var(--ink-2); margin: 0 0 1rem; }
"""


def nav(current=None, prefix=""):
    """current: the menu href of the page being built, or None for pages outside the menu."""
    here = ' aria-current="page"'
    links = "".join(f'<a href="{prefix}{href}"{here if href == current else ""}>{label}</a>'
                    for href, label in MENU)
    return f'<nav class="menu">{links}</nav>'
