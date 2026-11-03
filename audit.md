# Ship-surface audit, 2026-11-02 (session 6)

Scope: only what a reader of https://jamesishere.github.io/chomper/ sees, per the ship
freeze (CLAUDE.md, Next action). Findings only; no fixes applied. Every claim below was
checked this session by a command run or a file read; nothing is carried from memory.
Items the freeze put after the push (rails grep, tolerance census, code duplication,
decisions ledger sort, coherence map) were not audited.

## Verdict

The numbers hold. Every figure tested reproduces from the filing or the data, the pages
rebuild byte-identical from a clean clone with no secrets, and every internal link
resolves. What a reader sees is correct. Four things a reader sees are confusing or
imprecise (F1 to F4); two are judgment calls (F5, F6); the rest are notes.

## What was tested and passed

| Test                                                          | Evidence                                                                                                   |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| ODFL bridge foots                                             | start 1,543,998 + 12 bars (-182,953) = end 1,361,045, USD thousands; all 12 bar amounts appear on the page |
| ODFL closing bullets recompute                                | 98,213 / 135,468 = 72.5%; insurance 92,359 -> 74,416 (-19.4%); labor per ton 298.81 -> 322.29 (+7.86%)     |
| CAT 2007-2009 by hand against the FY2009 annual report        | ex_13.htm, accession 0000018230-10-000092: revenue 32,396 / 51,324 / 44,958; operating profit 577 / 4,448 / 4,921; profit before taxes 569 / 4,501 / 4,990. Page and data/headline/CAT.json agree to the million |
| CAT five-year split                                           | flex = prior pre-tax x revenue change / prior revenue, all four years; page lines are the per-line remainders with the sign as effect on income; lines sum to the "beyond revenue" row (-$813.0M, +$3.17B, +$761.0M, -$2.41B) |
| JPM 2008 by hand against the FY2008 10-K                      | y74757e10vk.htm, accession 0000950123-09-003840: Bear Stearns total purchase price 1,496; Washington Mutual 1,941; total assets 31 Dec 2007 1,562,147. All three match data/by_hand/acquisitions.json and the page |
| S&P 500 page: sectors add to the total                        | all ten years, revenue and pre-tax income, 414 companies in each                                           |
| S&P 500 page: the 11 built companies match their ten-year data | 10 exact; PGR 2022 differs by rounding (frames 49,611M vs companyfacts 49,610.7M; 922M vs 922.1M)          |
| Clean-clone rebuild                                           | git clone of the repo into a scratch folder, no .env: build.py and build_history.py exit 0; git status on docs/ empty (byte-identical). aggregate.py and membership.py were not run (network scripts; their pages are committed) |
| Internal links and anchors                                    | 82 internal links across 17 pages, 0 broken; external hosts: sec.gov (58), wikipedia.org (1)               |
| Counts shown on pages                                         | Decisioning "48 active of 55" = decisions.md; Considerations "22 open of 35" = considerations.md; All page 11 + 373 + 119 = 503 = census.md |
| Desktop render                                                | every page screenshotted at 1568px over 127.0.0.1; nothing broken                                           |
| Phone render (390px frame)                                    | All, CAT, ODFL bridge, S&P 500 screenshotted; no page-level horizontal scroll; bridge stacks cleanly        |

## Findings, most severe first

Severity: fix before the push only where a reader sees it and it is wrong or confusing.

### F1. Four company pages start in 2016 and do not say why

JNJ, PGR, PLD and UNH are headed "2016 to 2025"; the other seven reach fiscal 2007 (AAPL,
CAT, CCL, HD, JPM, MSFT, ODFL). No sentence on the four pages explains the shorter window.
The recession sentence under each table still names December 2007 to June 2009, which the
table never shows. A reader comparing two pages sees an inconsistency with no reason.
Ship fix: one sentence under the heading naming the fact (the long view for this company
has not yet been read back to fiscal 2007). Finishing the four pages is version 2.
Reader sees it: yes. Wrong: no. Confusing: yes.

### F2. JPM 2008 marker cites one filing and prints another filing's number

The marker reads "bringing at least $288.77B of assets" (Bear Stearns) and "at least
$263.99B" (Washington Mutual). Those values are tagged in the FY2010 10-K (accession
0000950123-11-019773, BusinessAcquisitionPurchasePriceAllocationAssetsAcquired, 288,768
and 263,991), where JPM uses that tag for total assets acquired, goodwill included. The
2008 10-K the deal record cites (0000950123-09-003840) prints the condensed statements of
net assets acquired: total assets $288,731M (Bear Stearns, goodwill 761 included) and
$263,649M (Washington Mutual). So "at least" understates the certainty (the tagged value
is the total, not a floor) and a reader following the citation finds a different figure.
The shares (18%, 17%) and the significance verdict do not change. The standing decision
("Significance: price or assets") already prefers a hand record from the purchase price
allocation; none exists for these two deals in data/by_hand/deal_assets.json.
Reader sees it: yes. Wrong: provenance, by 0.01%. Confusing: to anyone who clicks through.

### F3. Phone: the long table hides its right half

At 390px the 2007-2025 table scrolls sideways inside its box; the first view shows the
year, revenue and operating income only. Pre-tax income and margin, the columns the
project is about, are off-screen with a thin scrollbar as the only cue. The chart below
it fits but its tick labels are unreadable at that width. Nothing is broken.
Reader sees it: yes, on a phone. Wrong: no. Confusing: partly.
considerations.md "Phone layout unchecked" (2026-11-01) is now checked and should say so.

### F4. Membership page is a wall of blue with hover-only names

693 rows of bars, names on hover only, which a phone cannot do. Reached only from one
link on the S&P 500 page. Reads as a texture, not a chart.
Reader sees it: yes, if they click through. Wrong: no. Confusing: yes, on first sight.

### F5. The landing page buries the finished work (judgment call)

The All page opens as eleven collapsed sectors. The ODFL bridge, the one page that argues
rather than presents, is reachable from the ODFL row inside Industrials and from the ODFL
company page; nothing above the fold points to it or to any built page. A stranger
arriving from the GitHub profile sees a directory, not the product. One line of text with
a link is not a new page or column, but it is a change to what the reader sees first, so
it is James's call under the freeze.

### F6. README absent (known ship item)

No README.md in the repo. The GitHub repo page shows the file list only. Already on the
ship list.

## Notes, not blocking

- N1. PGR 2022 on the S&P 500 page differs from the company page at the rounding level
  (frames data is in whole millions). The decisions.md sentence "the 11 built companies
  match their ten-year data" is true to rounding, not exactly. No page states the claim.
- N2. Text-fragment links (22 on the bridge) are tested in Chrome only; Safari and Firefox
  unverified (considerations.md already carries this).
- N3. aggregate.py and membership.py regenerate their pages only with network access;
  the one-command rebuild (ship item) has to either skip them or state that.
- N4. The plan's "Done means" (plan.md) still describes version 1 (one page). Not reader
  visible; the README will state the current scope.
- N5. Visual checks were on Chrome at 1568px and in a 390px iframe (the extension cannot
  resize the window); a real phone check by James remains the final word.

## Phase (b) order, if James agrees

F1 (one sentence on four pages), F2 (two hand records from the 2008 10-K), then F3/F4/F5
as James rules, then F6 with the ship items.
