# Decisions

Hand-edited source for the Decisioning page. One entry per decision:

    ## YYYY-MM-DD | Short title
    Group: Scope, Method, Presentation, Evidence and review, or Build and process
    Decision: what was decided
    Why: the reason, one or two sentences
    Status: active (or: superseded by YYYY-MM-DD Short title)

To change a decision, add a new entry and mark the old one superseded; do not delete it.
Then run `python build_history.py`.

## 2026-10-27 | Company and years
Group: Scope
Decision: Old Dominion Freight Line, FY2025 vs FY2024, for the one-year bridge page.
Why: Of 7 carriers screened, the only one where both revenue (-5.5%) and operating income (-11.8%) move materially; single segment, with freight statistics.
Status: active

## 2026-10-27 | Bridge bars
Group: Method
Decision: Every line gets a bar: volume, yield, revenue remainder, then all 9 income-statement expense lines.
Why: A full bridge schedule is what analysts read at work; grouping would hide lines management does not discuss.
Status: active

## 2026-10-27 | AI step
Group: Evidence and review
Decision: A script calls a language model from the command line on plan tokens to draft commentary; James reviews; the page build reads only the approved output.
Why: Plan tokens over API dollars; nothing about this project requires an API.
Status: active

## 2026-10-27 | Stack
Group: Build and process
Decision: Python standard library only; horizontal HTML bridge, one expandable row per bar; JSON data in USD thousands.
Why: Fourteen labels do not fit under vertical bars at phone width.
Status: active

## 2026-10-27 | Citations
Group: Evidence and review
Decision: Verbatim quote plus filing page plus a link that jumps to the sentence on sec.gov; every amount carries its XBRL tag, period and accession.
Why: One tap to the highlighted sentence in the real filing is the credibility.
Status: active

## 2026-10-27 | Repo name
Group: Build and process
Decision: variance-bridge; GitHub Pages serves docs/ from main, no Actions.
Why: Bridge is the standard term in variance analysis, and the name survives extensions.
Status: superseded by 2026-10-30 Project name

## 2026-10-30 | Bar order switch on the one-year page
Group: Presentation
Decision: Default order is the 10-K's line order; a switch reorders bars by cost behavior or by size of change.
Why: Statement order ties to the filing; cost-behavior order shows which costs are volume problems.
Status: active

## 2026-10-30 | Explore five years, additively
Group: Build and process
Decision: Build the five-year view as new files next to the one-year page; roll back by archiving them if it does not work out.
Why: Exploring; the one-year page stays intact while the multi-year idea is tested.
Status: active

## 2026-10-30 | One method for any company, in dollars
Group: Scope
Decision: Build one view that runs on any S&P 500 company the same way; dollars only, no tonnage or other unit data; cross-company comparison deferred.
Why: A base-level look across all industries comes before anything company-specific.
Status: active

## 2026-10-30 | Core measure: flexed budget
Group: Method
Decision: Each line's yearly change is split into what it would have done moving in step with revenue, and the remainder beyond revenue.
Why: Shows which costs move when demand changes without hand-classifying costs as fixed or variable.
Status: active

## 2026-10-30 | Colors
Group: Presentation
Decision: Green for good, red for bad, in shades by size.
Why: Classic finance convention; signed numbers in every cell keep it readable for colorblind readers.
Status: active

## 2026-10-30 | Ratios lead
Group: Method
Decision: Costs as a share of revenue lead each company page; the dollar grid sits underneath as the drill-down.
Why: Percent of revenue is scale-free and the trend reads straight down a row.
Status: active

## 2026-10-30 | Trend at the top
Group: Presentation
Decision: Each company page opens with revenue and income by year with growth rates, plus a small chart indexed to the first year = 100.
Why: Start simple; one axis, and the gap between the lines shows leverage.
Status: superseded by 2026-11-01 Ten years at the top

## 2026-10-30 | Anchor on pre-tax income
Group: Method
Decision: Every company's lines must add up to pre-tax income; operating income is kept as a subtotal where the company reports one.
Why: Banks, insurers and some industrials report no operating income; pre-tax income is reported by every industry.
Status: active

## 2026-10-30 | Main menu
Group: Presentation
Decision: The horizontal menu is the main header: All and Decisioning. Companies are listed vertically on the All page, not in the menu.
Why: 500 tickers do not fit across a header.
Status: superseded by 2026-11-01 Menu: Chomper and Decisioning

## 2026-10-30 | Industry grouping
Group: Scope
Decision: The All page lists all S&P 500 companies by GICS sector, then sub-industry, from Wikipedia's list, with every SEC identifier checked against the SEC's own file.
Why: The grouping readers already know; sort out the grouping before any further analysis.
Status: active

## 2026-10-30 | Full S&P 500 run
Group: Scope
Decision: Not yet; settle the grouping and the page first.
Why: The run is about 1,000 filings of downloads; no point until the page is right.
Status: active

## 2026-10-30 | Time windows
Group: Method
Decision: A window must contain at least one revenue contraction and no undisclosed regime break. Long: 10-year headline only. Medium: 5-year line-by-line detail. Short: 1-year bridge. Acquisitions and accounting changes are marked, never used to shorten a window.
Why: Settles the recurring 10-year question: give each time frame its own window instead of forcing all three into one table.
Status: active

## 2026-10-30 | Decisioning page
Group: Presentation
Decision: A main-menu page lists every decision with its date, built from this file.
Why: To see every decision in one place and come back to change one.
Status: active

## 2026-10-30 | Decision groups
Group: Presentation
Decision: The Decisioning page groups decisions by type (Scope, Method, Presentation, Evidence and review, Build and process), then by date, newest first.
Why: One flat list was too much to piece through; the type says which question a decision answers.
Status: active

## 2026-10-30 | Project name
Group: Build and process
Decision: The project is chomper, an equity research project; the GitHub repo is JamesIsHere/chomper.
Why: The work grew from one bridge into reading any S&P 500 company's filings for what moves earnings; the name fits where it is going.
Status: active

## 2026-10-30 | One-year page approved
Group: Evidence and review
Decision: James reviewed the ODFL one-year bridge (wording, layout, the three findings) and approved it as it stands.
Why: Good in its current form; work moves on to the longer windows.
Status: active

## 2026-10-30 | Ten-year breaks
Group: Method
Decision: An acquisition is marked when its price is at least 10% of the buyer's total assets at the prior year end (SEC Regulation S-X Rule 1-02(w), the investment test), read from each 10-K's own XBRL. ASC 606 and 842 are marked in the year they became required. Every restatement is shown with the figure as first reported.
Why: Marking breaks must be correct, not a judgment call: the SEC's own significance test replaces a threshold of ours, and each deal's size comes from the filing.
Status: active

## 2026-11-01 | Menu: Chomper and Decisioning
Group: Presentation
Decision: The menu across the top has two items, Chomper (the company list) and Decisioning. The separate All item is gone; the name is capitalized.
Why: The name and All linked to the same page.
Status: superseded by 2026-11-01 Considerations page

## 2026-11-01 | Ten years at the top
Group: Presentation
Decision: Each company page opens with ten years of revenue, operating income (where the company reports it), pre-tax income and pre-tax margin, then the same ten years as the indexed chart. The five-year revenue and income table is removed; the five-year section starts at the cost grids. The list of breaks sits at the bottom of the page for now.
Why: The five-year table repeated the last five columns of the ten-year one; operating income moved up so it does not drop off the page.
Status: active

## 2026-11-01 | Ten years on one accounting basis
Group: Method
Decision: The ten-year headline promises the same accounting basis, with acquisitions marked; it does not promise the same business. Each year's change comes from the latest 10-K that shows both years, and the chart chains those changes. A change that does not match the dollar figures above it, because a later 10-K recast one of the years, is marked with an asterisk. Modified retrospective adoptions (most ASC 606, nearly all ASC 842) recast nothing and stay marked breaks until the adoption notes are read.
Why: Every 10-K shows its comparative year on its own basis, so same-filing growth handles restatements, retrospective changes, reclassifications and discontinued operations for every company without reading; same business needs the pro forma notes, company by company.
Status: active

## 2026-11-01 | Considerations page
Group: Build and process
Decision: A third menu page, Considerations, lists what the pages do not yet do right or what comes next, from considerations.md: one entry per item with a theme, the companies it touches, and the condition that makes it due. The menu is Chomper, Decisioning, Considerations.
Why: Items raised in passing (in chat, in the local notes) get lost; a due condition on each says when "done" is not done yet.
Status: active
