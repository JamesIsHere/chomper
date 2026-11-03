"""The site header shared by every Chomper page: the main menu, Chomper (home), Decisioning, Considerations.

Pages one folder down pass prefix="../" so every link resolves from where the page lives.
"""

MENU = [("index.html", "Chomper"), ("aggregate.html", "S&amp;P 500"), ("decisions.html", "Decisioning"),
        ("considerations.html", "Considerations")]

# The site's colour tokens (light, dark by system preference, dark by data-theme) and base rules, shared by every
# page; a page adds its own tokens in its own :root block.
BASE = """
:root { color-scheme: light; --bg: #ffffff; --ink: #0b0b0b; --ink-2: #52514e; --ink-3: #75746f; --rule: #e2e1dc;
  --up: #1f8a4c; --down: #d03b3b; --link: #1c5cab; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { color-scheme: dark; --bg: #1a1a19;
  --ink: #f0efec; --ink-2: #c3c2b7; --ink-3: #9a9992; --rule: #383835; --up: #3fb36b; --down: #e05252;
  --link: #86b6ef; } }
:root[data-theme="dark"] { color-scheme: dark; --bg: #1a1a19; --ink: #f0efec; --ink-2: #c3c2b7; --ink-3: #9a9992;
  --rule: #383835; --up: #3fb36b; --down: #e05252; --link: #86b6ef; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
  font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width: 60rem; margin: 0 auto; padding: 2rem 1rem 4rem; }
a { color: var(--link); }
"""

CSS = BASE + """
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
