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
Status: amended 2026-11-02 (Long window from fiscal 2007)

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
Status: superseded by 2026-11-01 Ten years at the top, charted in log dollars

## 2026-11-01 | Ten years on one accounting basis
Group: Method
Decision: The ten-year headline promises the same accounting basis, with acquisitions marked; it does not promise the same business. Each year's change comes from the latest 10-K that shows both years, and the chart chains those changes. A change that does not match the dollar figures above it, because a later 10-K recast one of the years, is marked with an asterisk. Modified retrospective adoptions (most ASC 606, nearly all ASC 842) recast nothing and stay marked breaks until the adoption notes are read.
Why: Every 10-K shows its comparative year on its own basis, so same-filing growth handles restatements, retrospective changes, reclassifications and discontinued operations for every company without reading; same business needs the pro forma notes, company by company.
Status: superseded by 2026-11-01 Ten years on one accounting basis, chart in dollars

## 2026-11-01 | Considerations page
Group: Build and process
Decision: A third menu page, Considerations, lists what the pages do not yet do right or what comes next, from considerations.md: one entry per item with a theme, the companies it touches, and the condition that makes it due. The menu is Chomper, Decisioning, Considerations.
Why: Items raised in passing (in chat, in the local notes) get lost; a due condition on each says when "done" is not done yet.
Status: active

## 2026-11-01 | Ten years at the top, charted in log dollars
Group: Presentation
Decision: Each company page opens with ten years of revenue, operating income (where the company reports it), pre-tax income and pre-tax margin, then a chart of revenue and pre-tax income in dollars on a log scale. Each year with a significant acquisition or a newly required accounting standard gets a numbered marker on the chart, explained in a numbered key under it. Under the lines, a band of bars shows each year's cost gap: pre-tax income at the prior year's pre-tax margin minus actual pre-tax income, both years from the same 10-K; red when costs grew faster than revenue, green when revenue grew faster. Figures a later 10-K changed are listed at the bottom as Note 1 - Recast Figures, and a starred change in the table reads "See Note 1". The chart and the five-year grids carry no explanatory notes. The five-year revenue and income table stays removed.
Why: A chart in multiples of the first year depends on that year (CAT's small 2016 pre-tax income made it read 83x); a log scale keeps one axis, and equal slopes still mean equal growth, without a base year. The bars put a dollar size on costs outrunning revenue. The numbered markers were chosen from four trial displays (markers, shaded bands, labels, swim lanes).
Status: active

## 2026-11-01 | Ten years on one accounting basis, chart in dollars
Group: Method
Decision: The ten-year headline promises the same accounting basis, with acquisitions marked; it does not promise the same business. Each year's change comes from the latest 10-K that shows both years. The dollar figures and the chart's lines are the latest reported; the cost-gap bars take both years from that same 10-K. A change that does not match the dollar figures above it, because a later 10-K recast one of the years, is starred and points to Note 1. Modified retrospective adoptions (most ASC 606, nearly all ASC 842) recast nothing and stay marked breaks until the adoption notes are read.
Why: Every 10-K shows its comparative year on its own basis, so same-filing growth handles restatements, retrospective changes, reclassifications and discontinued operations for every company without reading; same business needs the pro forma notes, company by company. The chart moved to dollars on a log scale, so it no longer chains the changes.
Status: active

## 2026-11-02 | Standards marked in the year adopted
Group: Method
Decision: ASC 606 and ASC 842 are marked on the ten-year chart in the year each company adopted them, as read from its own 10-K into data/adoptions.json (year, whether earlier years were recast, accession, verbatim quote). A standard adopted with earlier years recast gets no marker, since the series has no break there. Where no adoption note was found, the marker stays on the year the standard became required; where the 10-K does not state the method, the key says only "adopted".
Why: The required year was wrong for early adopters (MSFT, UNH), and a fully retrospective adoption (AAPL, JPM and MSFT 606, MSFT 842) is not a break; the company's own adoption note is the only source that says which.
Status: active

## 2026-11-02 | Company names: one source, one rule
Group: Presentation
Decision: Every company name on the site comes from the S&P 500 list (data/sp500.json) through one function, display_name: a trailing legal suffix is dropped ("Apple Inc." becomes Apple), except a bare "Company" that would leave one word ("Southern Company" stays); words that are part of the name stay (Group, Holdings, Trust, Bancorp); "Home Depot (The)" becomes The Home Depot. Company pages and the Chomper list use the same function.
Why: SEC filer names mix capitals and suffixes ("HOME DEPOT, INC.", "PROGRESSIVE CORP/OH/"), and the list's own names are not uniform; one rule over one source can be checked against a single cell per company.
Status: active

## 2026-11-02 | Fiscal year labels
Group: Presentation
Decision: A fiscal year is labeled from its end date read a week early: a year ending in December shows as the year (2020), any other as month and year (Sep 2020, Jan 2025). The week keeps 52/53-week years on one month: JNJ's year ended 2021-01-03 is 2020, and HD's years all read Jan. Labels name the month a year ends in, not the company's own fiscal-year name (James, 2026-11-02): HD's "Jan 2025" is the year HD calls fiscal 2024.
Why: Labeled by the raw end date, JNJ's years jumped between "Jan 2021" and "2020" and HD's between Jan and Feb, so fiscal years looked missing or doubled.
Status: active

## 2026-11-02 | Rounding is not a disagreement
Group: Method
Decision: When two filings give the same figure at different precision, and the coarser one equals the finer one rounded to its unit (PGR: $62,109M against $62,108.5M), the difference is not listed as a disagreement; the footer says the filings agree apart from rounding. Any other difference is listed with both values.
Why: Listing rounding as disagreement printed pairs like "$62.11B vs $62.11B", which reads as an error; recording real disagreements with both values still holds.
Status: active

## 2026-11-02 | Recast, not restated
Group: Presentation
Decision: A figure that a later 10-K changed is called recast ("Note 1 - Recast Figures", "as later recast"), never restated.
Why: In accounting a restatement corrects an error (ASC 250); most of these changes are new standards, presentation changes or discontinued operations, and calling them restatements claims an error the company never made.
Status: active

## 2026-11-02 | Deal names from the buyer's 10-K
Group: Presentation
Decision: The chart key names each significant acquisition as the buyer's own 10-K prose names the acquired company, with a trailing legal suffix dropped (HD Supply, SRS, Liberty Property Trust, Duke Realty), read by hand into data/deal_names.json with a verbatim quote and the accession. A significant deal with no record stops the build.
Why: The XBRL member label is not the company's name: HD tags HD Supply as "HD Holdings Inc", and PLD's labels came out lowercase and doubled ("Liberty property trust and liberty property limited partnership").
Status: active

## 2026-11-02 | Loss years break the income line
Group: Presentation
Decision: The ten-year chart stays on a log scale for every company. A year with zero or negative pre-tax income breaks the pre-tax income line and sits on a strip labeled Loss under the plot, with its amount; the line runs only through consecutive profitable years. The axis is set from the profitable years. A year with zero or negative revenue stops the build.
Why: A log scale cannot show zero or a negative, and growth is not defined across a change of sign, so the break marks exactly where slope stops meaning growth. Chosen over a symlog axis (slopes near zero would not mean growth), a linear axis for loss companies only (two chart grammars and the first-year problem back), and a margin axis (repeats the table). Checked on test data, Caterpillar's revenue with invented losses in five patterns.
Status: active

## 2026-11-02 | No marker where the standard does not reach the business
Group: Method
Decision: A standard gets no marker on the ten-year chart when the company's own 10-K says it falls outside the standard's scope and no adoption note follows (data/adoptions.json, out_of_scope, with that statement quoted). PGR's FY2016 10-K says insurance contracts are outside ASC 606; its FY2018 adoption section lists no revenue standard; PGR shows no 2018 marker.
Why: Every marker cites the company's own words. A "required this year" marker on PGR asserted a break the filing never claims, while the FY2016 sentence says why there is none (James, 2026-11-02).
Status: active

## 2026-11-02 | Footing allows the filing's own rounding
Group: Method
Decision: A year foots when the reported lines miss pre-tax income (or operating income) by no more than half a rounding unit for each figure summed, the subtotal included, with each unit read from the fact's own XBRL decimals. Any gap allowed this way becomes its own row, "Rounding in the filing" (a second row, "within operating income", when the operating subtotal is the one off), so the five-year grid and every later check still add exactly; history.py also records each gap with both values in footing_gaps, and the page footer names each one (year, subtotal, lines against reported, in millions). Rounding rows are not costs, so they do not scale with revenue: their whole change counts as beyond revenue, and pre-tax income's in-step change is taken from the figures that foot. A gap beyond the allowance still stops the build.
Why: Carnival's lines miss by $1M in years where every figure is rounded to the million; an exact rule stopped a real company over the filing's own rounding, while a flat dollar or percent tolerance would be arbitrary across company sizes. Boeing's $70B gap stays a hard stop (James, 2026-11-02).
Status: active

## 2026-11-02 | No cost-gap bar after a loss year
Group: Presentation
Decision: The ten-year chart draws no cost-gap bar for a year whose prior year had zero or negative pre-tax income (prior year as shown in the 10-K that reports both). The Loss strip above already marks those years.
Why: The bar is the pre-tax income at last year's margin minus what was earned; after a loss, last year's margin is negative and scaling it by revenue is not a cost gap. Carnival's Nov 2022 bar read $54.6B "revenue ran ahead of costs" from a -499% margin on 6.4x revenue, against an actual pre-tax change of +$3.44B (James, 2026-11-02).
Status: active

## 2026-11-02 | No ratio or growth on a loss base
Group: Method
Decision: Nothing on a company page divides or scales by a base at or below zero. The ten-year table leaves the percent change blank when the prior year is zero or negative (a fall from a positive year into a loss still shows, e.g. Carnival Nov 2020 -435.1%). The five-year dollar grid, in a column that starts from a loss year, leaves "if every cost moved in step with revenue" and "beyond revenue" blank and shows each line's whole change instead; a note under the grid names those columns. Together with "No cost-gap bar after a loss year", this is one rule. James will look through the loss cases for a tighter rule later.
Why: Scaling a loss by revenue gave Carnival -$51.20B "in step" against a +$3.44B change in Nov 2022, and percent changes like +3188.7% across a sign flip; the chart's income line already breaks at losses (James, 2026-11-02: "If you get a loss on the base here, I think we need to do something").
Status: active

## 2026-11-02 | One line under two tags is one row
Group: Method
Decision: When a line carries the same label in the filing but a different XBRL tag in the two 10-Ks, it is shown as one row, only when every tag carries figures, the years never overlap, and the line's sign and section (above or below operating income) agree. The row keeps the latest tag; history.py records every tag with its years in `retagged`, and the page footer names each one ("tagged InterestExpense for 2021 to 2022, then InterestExpenseNonoperating for 2023 to 2025"). The year both 10-Ks show is compared across the tag change, as for any line. No matching on similar labels and no company-specific rules; anything short of the test stays two rows.
Why: Keyed by tag, the line became two rows each jumping to or from nothing: Carnival's interest expense showed -$2.07B and +$1.61B where the real change was -$457M. The census found the pattern on 158 of 322 passing companies; the rule merges every split row on 135 of them (164 rows; 97 are InterestExpense to InterestExpenseNonoperating). 23 rows on 23 companies stay split, 20 where the line changes section or sign between the filings (James, 2026-11-02).
Status: active

## 2026-11-02 | A line tagged only in parts is shown summed
Group: Method
Decision: When a line on the income statement has no tagged total in a year, and the filing tags it in parts on an axis the statement itself shows (Boeing's cost of goods and services sold, by product and by service), the line is the sum of those parts, as one row under the line's own label. The footer names the parts by the filing's labels. If the parts sit on more than one such axis the build stops; if a line is summed in some years and a single total in others, the build stops ("Member slice"), since the parts may be only a slice of the total. Footing to pre-tax income stays the check, with no new tolerance.
Why: 39 of the 55 Footing stops were one cost line tagged only by product and service; reading only totals lost the whole line (Boeing's "$70B gap" is its 2023 cost of goods and services sold, $70,070M). One summed row keeps every label a real filing label and matches how revenue, split the same way on the face, is already shown as one total; per-part rows would have carried revenue labels on cost rows (Boeing's parts are labeled "Sales of products" and "Sales of services"). Of the 55, 36 now pass, 10 stop as Member slice; the 11 built pages are unchanged (James, 2026-11-02).
Status: active


## 2026-11-02 | Pre-tax income found by position
Group: Method
Decision: When neither pre-tax income tag anchors the statement's calculation, pre-tax income is the one subtotal that income tax is subtracted from to reach net income, provided that subtotal has its own calculation; more than one such subtotal stops the build. The page footer names the line by the filing's own label. No list of further tags.
Why: 33 companies print a pre-tax line under some other tag (Costco's "INCOME BEFORE INCOME TAXES" is IncomeLossAttributableToParent; eight different tags across the 33). Of the 52 stopped here, 29 now pass, each with a subtotal labeled as pre-tax income in the filing; the rest still stop. The 11 built pages are unchanged. Made under the standing rule that XBRL plumbing inside the rails is the agent's (James, 2026-11-02).
Status: active

## 2026-11-02 | Every company says whether it can be read
Group: Presentation
Decision: The All page gives every company without a page a status in its row: "Readable" when its filings pass every check of the five-year step, or "Not readable" with the reason in one plain line (one sentence per census class: statement not identified, pre-tax income not found, revenue not one line, figures that disagree, filings not found, lines that do not add up, a line in parts against a total, or an error in the reader). The opening paragraph counts both. Status comes from data/census.json, so a census rerun updates it. The full build of pages for readable companies stays a separate decision: each page also needs ASC 606/842 adoption records read from the company's 10-Ks.
Why: The agreed tail treatment was to exclude openly with reasons rather than add a rule per small class; with 11 pages built, a reader could not otherwise tell a company that cannot be read from one not yet built (James, 2026-11-02).
Status: active

## 2026-11-02 | Revenue in parts is not summed
Group: Method
Decision: Revenue is read like any line, but when the filing tags it only in parts, or leaves a year without it, the build stops with a named Revenue reason rather than summing the parts. Unlike a cost line, which parts make up "revenue" decides how the headline number is defined, so it waits for James's ruling.
Why: Three companies crashed on revenue with no total (APA, LHX, WFC). Summing WFC's parts would have shown three fee lines (advisory, brokerage, investment banking) as Wells Fargo's revenue. All three now stop as Revenue; the 11 built pages are unchanged (agent, under the standing XBRL rule, 2026-11-02).
Status: active

## 2026-11-02 | S&P 500 page, a trial
Group: Presentation
Decision: A new page, S&P 500 in the menu, sums revenue and pre-tax income across today's S&P 500 and each GICS sector, ten calendar years (2016 to 2025), and draws each sum with the company pages' log chart and cost-gap bars, all static, with one line of annual growth (revenue, costs, the gap between them) above each chart. Values come from the SEC's frames data (calendar-aligned, most recently filed); a company counts only with revenue and pre-tax income in all ten years, so every year sums the same companies, and the rest are listed with reasons. Revenue is the largest of the total-revenue tags a company reports in a year; pre-tax income is history.py's two tags, else domestic plus foreign. Sums, not medians: the largest companies dominate, and the page says so. Financials stays in, with a note that its revenue is not comparable. No drill-down yet.
Why: James wanted to see what costs have done across the S&P 500 and its sectors before building anything interactive (James, 2026-11-02: "lay out the main graph and the industry graphs, all static ... on a single new page, like a trial page"). The sectors add to the total in every year; the 11 built companies match their ten-year data. Rollback = move aggregate.py, data/aggregate.json and docs/aggregate.html to archive and drop the menu item.
Status: amended 2026-11-02 (Years placed by the fiscal-year rule, from the filings)

## 2026-11-02 | The S&P 500 as it was
Group: Method
Decision: Membership by month, January 2016 to December 2025, comes from the version of Wikipedia's "List of S&P 500 companies" current on the first of each month (membership.py; a page drawing one row per company and a bar for its months). Companies are matched by SEC identifier; a blank one is taken from the SEC's ticker file, and a new identifier that keeps the ticker the next month is the same company. Every month must list 495 to 510 rows. The S&P 500 page adds the index as it was: each year's change measured on that year's 1 January members that report both years, each company against itself, chained; today's members are chained the same way, so the gap between the two lines is survivorship alone.
Why: Tracing today's members back selects on the outcome: a third of January 2016's members were gone by December 2025, and index entry requires positive earnings. Measured, today's members overstate revenue growth by about half a point a year and the decade's margin gain by half (3.0 points against 2.0) (James, 2026-11-02).
Status: active

## 2026-11-02 | Survivorship by sector
Group: Presentation
Decision: The S&P 500 page shows, for each sector, the pre-tax margin of the sector as it was (members on 1 January of each year) against today's members, chained the same way as the total, with the number of members counted in the first and last year under each chart. Each company sits in its last sector while a member; the old Telecommunication Services is Communication Services. The ten-year dollar charts of today's members stay below, under their own heading.
Why: Split by sector, survivorship is not a uniform haircut: it reverses the decade in Utilities (-2.1 points as it was, +2.6 for today's members) and Consumer Discretionary, and runs through named companies; PG&E was out of the index 2020 to 2022 while it recovered from its wildfire losses, and Vistra turned around two years before joining, so only today's line counts their rebounds (James, 2026-11-02).
Status: active

## 2026-11-02 | Long window from fiscal 2007
Group: Method
Decision: The long view starts at fiscal 2007, the pre-crisis peak (the fiscal year ending between 1 July 2007 and 30 June 2008), instead of the last ten years. The medium and short windows are unchanged.
Why: The question is how a company's costs respond when revenue falls, and the downturns are the evidence; ten years from 2016 hold only 2020 and 2023. From 2007 the view holds the financial crisis, the 2015-16 industrial and energy slump, 2020 and 2023, and starting at a cycle peak measures growth over full cycles instead of from an arbitrary base year (James, 2026-11-02). CAT's FY2009 10-K reports 2007 and 2008 in the SEC's data.
Status: active

## 2026-11-02 | Company pages are finished by hand
Group: Scope
Decision: Company pages are finished one at a time for a short list chosen for variety in cost structure, not run in bulk. The scripts stay the instrument (pulling, footing, flags, verbatim checks); where they cannot decide (acquisitions before deals were tagged in the SEC's data, a year the data does not reach), the filing is read and a record is written with its source, checked as the scripts check their own. Peer and economy comparisons stay automated and are labelled approximate.
Why: Every company-specific case was becoming a general rule (eleven on 2026-11-02 alone), and the batch run was setting the agenda instead of the reader's question. The project's promise is that every number is traced to the filing, which a hand record with its source keeps; the reader is served by a few deep pages, not five hundred shallow ones (James, 2026-11-02).
Status: active

## 2026-11-02 | US recessions shaded
Group: Presentation
Decision: The long view shades each fiscal year that holds a quarter or more of a US recession as the NBER dates it (December 2007 to June 2009; February to April 2020), on the table's rows and on the chart as whole year slots, with a legend entry and a note naming the dates. The chart's numbered markers also appear beside their years in the table.
Why: The question is how operating income responds when revenue falls, and the recessions are where to look (James, 2026-11-02). Whole fiscal years, not true dates, because each point is a fiscal year: a band at the true dates left CAT's 2009 trough outside the shading. A share, not a fixed three months, because the 2020 recession lasted three months and a fixed test missed HD's fiscal 2020, which starts 3 February. A slump outside the shading (CAT 2015-16) reads as the company's own, not the economy's.
Status: active

## 2026-11-02 | A tag joins to fill a gap
Group: Method
Decision: When the long series' revenue (or income) tags skip years inside the window, another tag joins if it brings the missing years and matches the series in a year both cover, the same evidence that already lets a tag extend the series further back. The series must reach fiscal 2007 with no gap, or the run stops and names the gap.
Why: CCL's Revenues tag skips 2009 to 2013; SalesRevenueServicesGross covers 2008 to 2015 and matches it in 2014 and 2015 ($15,884M, $15,714M). Plumbing within the rails: no tolerance, no company-specific rule; CAT and HD unchanged.
Status: active

## 2026-11-02 | A full restatement joins by its own table, and its break is marked
Group: Method
Decision: Where a company restated earlier years fully retrospectively under a new tag (MSFT's ASC 606 in its FY2018 10-K), the old tag joins the long series only through a hand record (data/by_hand/joins.json) whose as-first-reported and as-restated pairs appear in a verbatim quote of the 10-K's own restatement table, and match the two tags exactly. Each recast adoption records recast_from, the earliest year its 10-K reports on the new basis; a series reaching before it gets a chart marker there ("adopted in ... with this year and after recast; earlier years as first reported"), and the build stops if a recast adoption lacks recast_from where the series reaches further back. Note 1 says "earlier reported", not "first reported", and shows millions where a recast is smaller than the page's rounding.
Why: MSFT's 2016-17 revenue was restated ($85,320M to $91,154M; $89,950M to $96,571M), so no shared year can match. A recast adoption was treated as no break, true only while the series began inside the recast years; the new check found AAPL's page had carried an unmarked break at Sep 2017 (James, 2026-11-02, approved with MSFT and AAPL from 2007).
Status: active

## 2026-11-02 | A year before the SEC's data is read by hand from the latest 10-K that reports it
Group: Method
Decision: Where the SEC's XBRL data does not reach fiscal 2007 (ODFL's first XBRL 10-K is for 2010, so its data starts with 2008), the missing year's revenue, operating income and pre-tax income come from a hand record (data/by_hand/levels.json): one verbatim quote of the income statement in the latest 10-K that reports the year. The figures are read out of the quote, not typed; the quote must state its unit and columns; every footing in the record (revenue less total operating expenses is operating income; operating income less non-operating expense is pre-tax income) must hold in every column; and the filing's other columns must equal the XBRL series exactly, so the hand year sits on the same basis. The change into the next year is measured within that one 10-K. A note under the long table names the filing. Hand acquisition records may now quote amounts in thousands, as ODFL prints them.
Why: The long window starts at fiscal 2007 ("Long window from fiscal 2007"), and a company page is finished by hand where the data does not reach ("Company pages are finished by hand"). ODFL's FY2009 10-K reports 2007 alongside 2008 and 2009, which match the SEC's data to the thousand (James, 2026-11-02, approved with ODFL from 2007).
Status: active

## 2026-11-02 | Significance: price or assets
Group: Method
Decision: An acquisition is significant, and marked on the long view, when either the price paid (S-X Rule 1-02(w) investment test) or the total assets acquired, goodwill included (the rule's asset test), reach 10% of the buyer's total assets at the prior fiscal year end. The assets come from the 10-K's purchase price allocation, read by hand into data/by_hand/deal_assets.json and footed (assets less liabilities must equal the price or net assets the filing prints, whether a table or named amounts in a sentence), else from the XBRL total; XBRL identifiable assets settle the test only when they alone reach 10% (goodwill can exceed the price, so they give no upper bound). Every deal by a Financials-sector company is tested; elsewhere, a deal priced under 1% of prior total assets is screened out, since its assets could reach 10% only if the target's liabilities exceeded nine times the price. Where the 10-K gives only net figures, the record says so with the quote and the deal stays on the price test, named on the Considerations page. A marker from the asset test names the price and the assets brought ("at least" where only identifiable assets are known). The income test is not applied.
Why: JPM bought Bear Stearns and Washington Mutual's banking operations in 2008 for 0.1% of its assets each, yet they brought 18% and 17%; the price test alone left the year unmarked, an undisclosed regime break the time-window rule forbids (James, 2026-11-02, chose the asset test with a 1% screen outside Financials, and to name deals whose 10-K gives no gross assets rather than screen them). Only 9 of 58 tagged deals carry a total in XBRL, so the rest are read by hand. Result on the finished pages: JPM 2008 (Bear Stearns, Washington Mutual), MSFT fiscal 2008 (aQuantive, 11%) and fiscal 2014 (Nokia's Devices and Services business, 10.5%) now marked.
Status: active

## 2026-11-02 | A short series says so
Group: Presentation
Decision: A company page whose long view does not reach fiscal 2007 carries one sentence under its heading: the years before its first year have not yet been read for this company, and the long view starts at fiscal 2007 once they are. The recession note under the table names only the recessions the table shows. Both come from the data (the first period against the fiscal 2007 window), never from a list of companies.
Why: The ship-surface audit (audit.md, F1) found JNJ, PGR, PLD and UNH headed "2016 to 2025" beside seven pages that reach 2007, with no reason on the page, and a recession note naming 2007 to 2009 on tables that never show those years (James, 2026-11-02, approved the wording).
Status: active

## 2026-11-02 | Phone long table stays as is
Group: Presentation
Decision: On a phone the 2007-2025 table on each company page scrolls sideways inside its box, so pre-tax income and margin start off-screen. It ships that way; a phone column order is version 2.
Why: Nothing is wrong and the page itself does not scroll sideways; the ship list is frozen and a reorder is a change to what every reader sees first (James, 2026-11-02; audit.md, F3).
Status: active

## 2026-11-02 | The All page names what is built
Group: Presentation
Decision: One sentence after the All page's opening paragraph names what is built, each linked: every one-year bridge in docs/bridge/ (its company and years read from the bridge data, which must be that company's) and every company page. It is generated from the pages on disk, never a hand list.
Why: The ship-surface audit (audit.md, F5) found the ODFL bridge, the one page that argues rather than presents, two clicks down inside Industrials with nothing above the fold pointing to it; a stranger from the GitHub profile saw a directory, not the product (James, 2026-11-02, approved the wording).
Status: active

## 2026-11-02 | One deal, two tagged values: within 1%
Group: Method
Decision: When a 10-K tags the same deal measure (price paid, or assets acquired) at two values, the reader keeps the larger if they are within 1% of each other and stops otherwise. The 1% stays; it is not tightened to the facts' own rounding.
Why: The post-ship tolerance census found it the only hand constant among the checks (the rest derive from the data or a cited rule). James ruled it fine as is (2026-11-02): the two values come from one filing and the shares that depend on them are read against a 10% test.
Status: active

## 2026-11-02 | Every rebuild ends with the cross-page check
Group: Build and process
Decision: coherence.py reads every figure or fact that appears on more than one built page, or in the README, from each place and compares them (the All page's counts and rows against the pages, data and README; each company page against its row; the bridge against the All page sentence and README; both ledgers against their files; the S&P 500 page against the membership data; the menu on every page). rebuild.py runs it last and fails on any disagreement. A check that cannot find what it looks for fails rather than skips.
Why: The post-ship list's "coherence map", settled with James on 2026-11-02 as a cross-page agreement check. The pages are built by four scripts and the README by hand, so a figure can drift in one place; a planted change to the README and to one All page cell were both caught before this was committed.
Status: active

## 2026-11-02 | The population, and a Waterfall page that counts it down
Group: Scope
Decision: The population is every company the S&P 500 held in any month the membership file covers (January 2016 to December 2025, matched by SEC identifier), not today's list alone. A Waterfall page, last in the menu, counts each path down from its top: membership to today's list, today's list through the two readers to the published pages, the ten-year passes through to the fall years the cost measure would see, and today's members to what the S&P 500 page sums; every step names what fell out and why. waterfall.py takes each count from the file that defines that level and writes data/waterfall.json; the page is built from that file, and the cross-page check ties its counts to the other pages.
Why: James could not place the counts in the profit-line evidence (199 of 250: where does 250 come from?). The readers run on today's list only, so the 194 companies that left the index are not read anywhere yet; the page says so rather than letting the sample pass for the population. Membership before 2016 has not been read, so a fifteen- or twenty-year population is named as not yet existing (James, 2026-11-02).
Status: active

## 2026-11-02 | A company is read under every identifier it has filed under
Group: Method
Decision: On the S&P 500 page a company on today's list is read under its own SEC identifier and, for years that identifier lacks, under the identifiers the membership file holds for the company carrying its ticker while it was still a member in the file's last month. The earlier identifier fills only missing years, and only when the two series read as the same company: they agree at the coarser rounding in a year both hold, or, with no shared year, the earlier series ends the year before the company's own begins. Otherwise the earlier identifier is ignored and the exclusion says so. The page records which identifiers and years were used.
Why: Exxon re-registered in 2025 and all ten of its years sat under the old number, so the page summed the index without its largest energy company (2% of revenue, worth about a point of index revenue growth in 2020 and 2022); Bunge and BlackRock were out for the same reason. The same-company test keeps a reused ticker (Fox 2019, Qnity 2025) from stitching a different company's history on (James, 2026-11-02, asked for the Exxon fix).
Status: active

## 2026-11-02 | Years placed by the fiscal-year rule, from the filings
Group: Method
Decision: The S&P 500 page takes each company's revenue and pre-tax income from its own companyfacts (one-year facts from 10-K filings, the most recently filed value for each year end, the way headline.py reads a company), not from the SEC's frames. A company's year ends are chained back from its latest, each 350 to 380 days before the next; the latest is placed in the calendar year it most nearly covers (a year ending 1 July to 30 June of the next year counts as the first), and each earlier year sits one step before it. Year ends off that chain (a changed year end, a stray period) are left out and the exclusion names them. The membership file's identifiers are the population; the frames are not read at all.
Why: The frames place each fiscal year by its end date alone, so a 52/53-week year that drifts across 30 June lands in the wrong calendar year: Sysco's year ending 30 June 2018 appeared nowhere, the years ending 29 June 2019 and 27 June 2020 sat in 2018 and 2019, the year ending 3 July 2021 in 2021, and 2020 was empty; Danaher's 2020 was absent from the frames though its filings carry it. The page listed Sysco, Uber, Duke and others as missing a year they had filed. Chaining from the latest year end places every year of a company consecutively, which is what the calendar placement means. Values now match the company pages (the frames rounded to millions; Progressive's 2022 and 2023 differ from its page by the filer's own change of rounding). The placement moves for companies with non-December year ends, about a quarter of the list, so James ruled it (2026-11-02, "yes").
Status: active

## 2026-11-03 | A short series is read where the tags stop before fiscal 2007
Group: Method
Decision: When a company's tags and hand records reach back only part way to fiscal 2007 without a gap, the ten-year reader keeps the years they reach instead of stopping (the series starts at the latest first year its three lines share: Nvidia's revenue runs from fiscal 2007 and its pre-tax income from 2008, so both start in 2008). The page already says, under the long view, which years have not yet been read for the company; a gap inside the series still stops. The Waterfall's ten-year row counts every pass and says how many reach fiscal 2007.
Why: Under the fiscal-2007 rule 289 of 384 readable companies stopped at "starts after fiscal 2007" and the ten-year sample was the seven companies with hand records, so the cost measure had nothing to read; the stop protected nothing the page's own note does not disclose (James, 2026-11-03, "yes" to the short series). The long window still starts at fiscal 2007 where the data reaches; this does not amend that ruling.
Status: active

## 2026-11-03 | The cost measure's verdict comes from pre-tax income
Group: Method
Decision: The cost measure, how far a company's profit fell when its revenue fell, is the change in profit over the change in revenue in a fall year (revenue down 5% or more on the prior fiscal year), and its verdict comes from pre-tax income for every company. Where the company reports an operating income subtotal, the same ratio on operating income is shown beside it, and a fall year is flagged when the two land in different bands: below zero, zero to one, above one. The bands are the structural boundaries (profit moved against revenue; profit fell by more than revenue), not a tolerance. measure.py writes every fall year to data/measure.json from the ten-year series the bulk run passed.
Why: Pre-tax income is the subtotal every filer prints and the one every series already foots to. Operating income is each filer's own boundary: restructuring, impairments, gains on property sales and the non-service pension cost sit above it at one company and below at the next, and banks, insurers and six of the 36 companies the reader passes today print none, so a verdict from it would compare one filer's boundary against another's. On those 36: 52 fall years, 47 with both lines, the two ratios within 0.11 on 44 of them, three band differences all within 0.05 of zero (Dell 2024, Howmet 2018 and 2020), three gaps above 0.25 from items below operating income (T. Rowe Price 2022 investment losses, Carnival 2021 interest, IFF 2025). The pre-tax ratio equals the operating ratio plus the change in the items between them over the change in revenue, so the two side by side are that decomposition and nothing is lost silently; what is given up is a one-number ranking that ignores financing, and the flag says so where it matters. Operating-where-reported, pre-tax otherwise would have mixed two definitions across the companies a peer comparison sets side by side (James, 2026-11-03, "yes pretax with op margin beside it").
Status: active

## 2026-11-03 | Hand records drafted by the model, verified by the reader
Group: Method
Decision: The two hand-work stops of the ten-year reader (a 10-K before XBRL whose acquisitions must be read from the filing; a deal whose assets acquired are not tagged) are met at scale by draft_hand.py: for each, a `claude -p` call reads the filing's own passages and drafts the record in the format a person writes, and the reader verifies it exactly as it verifies a person's record (every quote verbatim in the filing's document, every figure read out of its quote by row and column, every table footed) before it is written to data/by_hand/. A draft that fails twice is not kept and the company stays stopped, named in data/bulk/drafts.json. A drafted record carries "drafted" with the date, so it is always distinguishable from one a person wrote. The model also reads which deals are business combinations and which are asset purchases, and its note records that reading; a reader of the record can see it. A table the model reports it cannot read row by row (footnote markers between the numbers) is left to a person.
Why: 267 of the 348 companies the reader stops on need these records (159 pre-XBRL years, mostly the 2007 and 2008 10-Ks; 108 companies' deal assets, some 800 tables), and an experiment with the hand work waived showed 182 of them would pass, taking the sample from 36 companies and 52 fall years to about 218 and 310. Waiving the two rules by definition would have dropped the asset test that caught JPMorgan's 2008 deals (0.1% of assets on price, 18% on assets) and the crisis years the fiscal-2007 rule exists for. Drafting keeps both rules and their gate, and spends plan tokens, not API dollars. Pilot 2026-11-03: Costco 2009 and Tesla 2010 (no acquisitions; the cash-flow investing section quoted as the record of that), Ameriprise's BMO deal (allocation table footed), AES's DPL deal left to a person (James, 2026-11-03, "A please draft at scale").
Status: active
