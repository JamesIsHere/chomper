"""Drafts the hand records the ten-year reader asks for, from the filings themselves, through `claude -p`; the reader
then verifies each draft exactly as it verifies a record typed by hand, and a draft that does not verify is not kept
(James, 2026-11-03: draft at scale rather than waive the two hand-work rules).

    python draft_hand.py --model M --effort E TICKER...   draft for these companies
    python draft_hand.py --model M --effort E --stops     every company whose bulk result is one of the two hand-work stops

--model and --effort are required. Each claude -p call runs with --safe-mode --strict-mcp-config from an empty
folder (no CLAUDE.md, hooks or MCP servers), logs its usage to data/bulk/draft_calls.jsonl, and the first failed
call stops the batch.

For each company the reader is run; its stop says what is missing:
  * a pre-XBRL 10-K ("predates XBRL; read its acquisitions"): the drafter reads that filing's documents, sends the
    passages that mention acquisitions, the cash-flow acquisition line and the balance sheet's total assets to the
    model, and asks for the data/by_hand/acquisitions.json record: each deal with a verbatim quote naming its price,
    the year's acquisition spend from the cash flow statement, and total assets at the prior year end;
  * a deal whose assets acquired are not tagged ("need total assets acquired read from the 10-K"): the passages
    around the deal's name and its purchase price allocation go to the model, which returns the
    data/by_hand/deal_assets.json record: the allocation table quoted verbatim with its asset, liability and total
    rows named (or the sentences that carry them, or a note that the 10-K gives no gross figure);
  * a deal a later 10-K tags inside a hand-recorded year ("tagged in ... but the hand record ... lacks it"): the
    year's record is drafted again, told to include that deal at the tagged size.
Before a record is written the drafter checks it itself: every quote verbatim in the document it names (the same
normalisation the reader uses), each figure read out of its quote by row and column, dates inside the fiscal year;
then headline.by_hand() or headline.assets_from_record() runs on it, the reader's own gate. Only then is it merged
into the tracked file, marked "drafted" with the date, so a drafted record is always distinguishable from one a
person wrote. The loop ends when the reader passes, stops on a rule that is not hand work, or a draft fails twice.
Results go to data/bulk/drafts.json (not tracked); run bulk.py over the passes afterwards to refresh results.json.
No figure drafted here reaches a page except through the reader's checks.
"""
import html
import json
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import headline
from history import get, get_json
from pull import ROOT, user_agent

BULK = ROOT / "data" / "bulk"
RESULTS = BULK / "drafts.json"
MAX_ROUNDS = 8            # reader runs per company: two or three pre-XBRL years, then the deals, then the pass
PASSAGE_CAP = 110_000     # characters of filing text per model call
WORKERS = 4               # model calls in flight for one company's deals
TODAY = date.today().isoformat()

PRE_XBRL = re.compile(r"^(\d{4}-\d{2}-\d{2}): 10-K (\S+) predates XBRL")
NEED_ASSETS = re.compile(r"^  (\S+) \| (.*?) \| (\d{4}-\d{2}-\d{2}) \| price [\d.]+% of prior assets \| (\S+)$", re.M)
TAGGED_LATER = re.compile(r"^(\S+) (\d{4}-\d{2}-\d{2}): tagged in (\S+) at ([\d,]+) but the hand record for "
                          r"(\d{4}-\d{2}-\d{2}) (lacks it|has [\d,]+)")
MEASURES = [m for m, _ in headline.SIZE]

SYSTEM = """You are a careful reader of SEC 10-K filings recording facts for an audit trail. You are given passages
copied from a filing's documents, each passage headed by its document name. You answer only from the passages.
Every quote you return must be copied verbatim from a passage, character for character, including spacing,
commas, dollar signs and parentheses, and must be long enough to contain every figure you cite from it. Never
paraphrase inside a quote, never join two places into one quote. Amounts are in whole US dollars (a table in
millions showing 1,234 is 1234000000). If the passages do not state something, say so in the field provided
rather than guessing."""


# --- the filing's text, normalised as the reader normalises it ------------------------------------------------------

def documents(cik, accession, ua):
    """{document name: normalised text} for a filing's text documents, largest first (at most six)."""
    acc = accession.replace("-", "")
    base = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}"
    items = get_json(f"{base}/index.json", f"{cik}/{acc}/index.json", ua)["directory"]["item"]
    names = [i["name"] for i in items if re.search(r"\.(htm|html|txt)$", i["name"], re.I)
             and not i["name"].startswith(accession) and not re.match(r"^R\d+\.htm$", i["name"])
             and (i.get("size") or "0").isdigit() and int(i.get("size") or 0) > 2000]
    names.sort(key=lambda n: -int(next(i["size"] for i in items if i["name"] == n)))
    out = {}
    for n in names[:6]:
        page = get(f"{base}/{n}", f"{cik}/{acc}/{n}", ua).read_text(encoding="utf-8", errors="replace")
        out[n] = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", page)))
    if not out:
        raise SystemExit(f"{accession}: no text documents in the filing index")
    return out


def windows(text, pattern, before, after, cap):
    """Passages of `text` around each match of `pattern`, merged where they overlap, up to `cap` characters."""
    spans = []
    for m in re.finditer(pattern, text, re.I):
        a, b = max(0, m.start() - before), min(len(text), m.end() + after)
        if spans and a <= spans[-1][1]:
            spans[-1][1] = max(spans[-1][1], b)
        else:
            spans.append([a, b])
    out, used = [], 0
    for a, b in spans:
        if used + (b - a) > cap:
            break
        out.append(text[a:b])
        used += b - a
    return out


def passages(docs, specs):
    """specs: [(pattern, before, after, cap)]; the passages of every document for each spec, headed by document."""
    parts = []
    for name, text in docs.items():
        for pattern, before, after, cap in specs:
            for w in windows(text, pattern, before, after, cap):
                parts.append(f"[document: {name}]\n{w}")
    body = "\n\n".join(parts)
    return body[:PASSAGE_CAP]


# --- the model ---------------------------------------------------------------------------------------------------------

DUMP = BULK / "drafts"  # every model reply, for inspection: {ticker}_{item}_{attempt}.json


CALLS = BULK / "draft_calls.jsonl"  # one line per model call: model, effort, seconds, every usage count
MODEL = EFFORT = None              # set from --model / --effort; required, no default (a default once ran the batch on Fable)
NEUTRAL = Path(tempfile.mkdtemp(prefix="draft_hand_cwd_"))  # no CLAUDE.md above it is read with --safe-mode anyway


class ModelFailure(Exception):
    """A claude -p call that failed (usage limit, auth, outage): the batch stops at the first one."""


def ask(schema, prompt, tag, reuse=False):
    saved = DUMP / f"{tag}.json"
    if reuse and saved.exists():  # a first-attempt reply on disk is reused (the checks are the gate); a retry is always fresh
        with CALLS.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"tag": tag, "reused": True}) + "\n")
        return json.loads(saved.read_text(encoding="utf-8"))
    cmd =["claude", "-p", "--output-format", "json", "--no-session-persistence", "--tools", "",
           "--model", MODEL, "--effort", EFFORT, "--safe-mode", "--strict-mcp-config",
           "--system-prompt", SYSTEM, "--json-schema", json.dumps(schema)]
    t = time.time()
    run = subprocess.run(cmd, input=prompt, capture_output=True, text=True, encoding="utf-8", shell=False, cwd=NEUTRAL)
    line = {"tag": tag, "model": MODEL, "effort": EFFORT, "seconds": round(time.time() - t, 1),
            "prompt_chars": len(prompt), "returncode": run.returncode}
    try:
        reply = json.loads(run.stdout)
    except ValueError:
        reply = None
    if reply:
        u = reply.get("usage") or {}
        line |= {"input_fresh": u.get("input_tokens", 0), "cache_write": u.get("cache_creation_input_tokens", 0),
                 "cache_read": u.get("cache_read_input_tokens", 0), "output": u.get("output_tokens", 0),
                 "model_turns": reply.get("num_turns"), "models": sorted(reply.get("modelUsage", {})),
                 "list_price_usd": reply.get("total_cost_usd"), "is_error": reply.get("is_error")}
    if run.returncode != 0 or not reply or reply.get("is_error"):
        line["error"] = ((run.stderr or "") + " | " + (run.stdout or ""))[-600:]
    with CALLS.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line) + "\n")
    if "error" in line:
        raise ModelFailure(f"claude -p failed ({run.returncode}) on {tag}: {line['error']}")
    if not reply.get("structured_output"):
        raise RuntimeError(f"no structured output: {run.stdout[:300]}")
    DUMP.mkdir(parents=True, exist_ok=True)
    (DUMP / f"{tag}.json").write_text(json.dumps(reply["structured_output"], indent=1, ensure_ascii=False),
                                      encoding="utf-8")
    return reply["structured_output"]


def S(**props):
    """A JSON schema object with every property required (claude -p's structured output wants that)."""
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


STR, INT = {"type": "string"}, {"type": "integer"}
STRS = {"type": "array", "items": STR}

YEAR_SCHEMA = S(
    deals={"type": "array", "items": S(
        name=STR, member=STR, date=STR, size=INT, measure={"type": "string", "enum": MEASURES},
        document=STR, quote=STR)},
    spend=INT, spend_label=STR, spend_unit={"type": "integer", "enum": [1000, 1000000]},
    spend_columns=STRS, spend_column=INT, spend_document=STR, spend_quote=STR,
    prior_total_assets=INT, assets_label=STR, assets_unit={"type": "integer", "enum": [1000, 1000000]},
    assets_columns=STRS, assets_column=INT, assets_document=STR, assets_quote=STR,
    note=STR)

ASSETS_SCHEMA = S(
    kind={"type": "string", "enum": ["table", "prose", "not_determinable", "unreadable"]},
    document=STR, quote=STR, unit={"type": "integer", "enum": [0, 1000, 1000000]},
    columns=INT, column=INT, assets=STRS, liabilities=STRS, total=STRS, note=STR)


# --- a pre-XBRL year -----------------------------------------------------------------------------------------------------

def year_prompt(ticker, company, end, prior_end, docs, required, failure):
    body = passages(docs, [(r"Total assets", 900, 500, 15_000),
                           (r"investing activities", 400, 2200, 20_000),
                           (r"acqui", 1000, 1400, PASSAGE_CAP)])
    req = ""
    if required:
        req = ("\nA later filing tags these deals inside this fiscal year; each must appear in `deals` with exactly "
               "this member key and this size, quoted from the passages:\n" +
               "\n".join(f"  member {m}, dated {d}, size {v:,} dollars" for m, d, v in required) + "\n")
    retry = f"\nA previous draft failed this check: {failure}\nFix that in this draft.\n" if failure else ""
    return f"""Company: {company} ({ticker}). Fiscal year: {prior_end} (exclusive) to {end} (inclusive). The filing is
the 10-K for that year, filed before XBRL. Record, from the passages below:

1. `deals`: every business acquisition the company completed in this fiscal year (not announced-only deals, not
   investments in securities, not deals of earlier or later years). For each: `name` as the filing names the target;
   `member` as "by_hand:" plus the name in CamelCase with no spaces (unless a member key is required below);
   `date` as YYYY-MM-DD, the month's last day when the filing gives only a month; `size` in whole dollars, the
   measure the filing states (`measure`: consideration if the total purchase price is given, else cash paid or
   cash paid net of cash acquired, else net assets acquired); `document` and `quote`: the verbatim passage text
   that states the size. If the filing states no acquisitions this year, `deals` is empty.
2. `spend`: the cash flow statement's line for acquisitions of businesses (net of cash acquired where that is the
   line) for this fiscal year, in whole dollars, as a positive number (0 if the line shows a dash or nothing).
   `spend_label` is the row's label exactly as printed, `spend_unit` the statement's unit, `spend_columns` the year
   headings in the order the row's numbers appear (for example ["2007", "2006", "2005"]), `spend_column` the
   0-based index of this fiscal year's column, `spend_document` and `spend_quote` the verbatim row text (label
   followed by its numbers), with the unit heading included where it is near. A dash cell is 0. If the cash flow
   statement has no line for acquisitions of businesses at all, `spend` is 0, `spend_quote` is the investing
   activities section quoted verbatim from its heading through its net total, and `spend_label` is that net
   total's label (so the record shows the section had no such line).
3. `prior_total_assets`: total assets on the balance sheet at the prior fiscal year end ({prior_end}), in whole
   dollars, with `assets_label`, `assets_unit`, `assets_columns` (the year headings in the order the row's numbers
   appear), `assets_column` (the 0-based index of the prior year end's column), `assets_document` and
   `assets_quote` (the verbatim row text, label followed by its numbers).
4. `note`: anything a reader should know (a deal whose price is given only approximately, a line label that
   differs, a figure you could not find).
{req}{retry}
Passages:

{body}"""


def check_row(quote, label, columns, column, unit, value, year, what):
    """The value read out of the quote by its row label and column, in the stated unit, must be the value given,
    and the chosen column heading must name the year asked for."""
    if not (0 <= column < len(columns)):
        raise ValueError(f"{what}: column {column} outside {columns}")
    if not any(str(y) in columns[column] for y in year):
        raise ValueError(f"{what}: column {column} is headed {columns[column]!r}, not {' or '.join(map(str, year))}")
    vals = headline.quoted_row(quote, label, len(columns), unit, what)
    if abs(vals[column]) != abs(value):
        raise ValueError(f"{what}: the quote's column {column} reads {vals[column]:,}, the draft says {value:,}")


def heading_years(end):
    """The years a column for the fiscal year ending `end` may be headed by: the end's calendar year, and the year
    before when a 52/53-week year ends in the first week of January (CDNS's year ending 2010-01-02 is fiscal 2009)."""
    d = date.fromisoformat(end)
    return (d.year, d.year - 1) if d.month == 1 and d.day <= 7 else (d.year,)


def prior_year_end(end):
    """The same date one year earlier (Feb 29 -> Feb 28). Not end - 365 days: that lands on 1 January in a leap year
    and demanded a '2008' column for the balance sheet at 31 December 2007 (20 drafts rejected, 2026-11-03)."""
    d = date.fromisoformat(end)
    return (d.replace(year=d.year - 1) if not (d.month == 2 and d.day == 29) else d.replace(year=d.year - 1, day=28)).isoformat()


def year_record(ticker, cik, end, accession, docs, draft, prior_end):
    """The acquisitions.json record from a draft, after the drafter's own checks (ValueError names the failure)."""
    def verbatim(document, quote, what):
        if document not in docs:
            raise ValueError(f"{what}: document {document!r} is not one of {list(docs)}")
        if len(quote) < 20 or quote not in docs[document]:
            raise ValueError(f"{what}: quote not found verbatim in {document}: {quote[:80]!r}")
    deals = []
    for d in draft["deals"]:
        verbatim(d["document"], d["quote"], f"deal {d['name']}")
        if not (prior_end < d["date"] <= end):
            raise ValueError(f"deal {d['name']}: date {d['date']} is outside {prior_end} to {end}")
        forms = headline.deal_forms(d["size"])
        if not any(f in d["quote"] for f in forms):
            raise ValueError(f"deal {d['name']}: size {d['size']:,} does not appear in its quote as {forms}")
        deals.append({"name": d["name"], "member": d["member"], "date": d["date"], "size": d["size"],
                      "measure": d["measure"]})
    verbatim(draft["assets_document"], draft["assets_quote"], "total assets")
    check_row(draft["assets_quote"], draft["assets_label"], draft["assets_columns"], draft["assets_column"],
              draft["assets_unit"], draft["prior_total_assets"], heading_years(prior_end), "total assets")
    verbatim(draft["spend_document"], draft["spend_quote"], "spend")
    if draft["spend"]:
        check_row(draft["spend_quote"], draft["spend_label"], draft["spend_columns"], draft["spend_column"],
                  draft["spend_unit"], draft["spend"], heading_years(end), "spend")
    elif draft["spend_label"] not in draft["spend_quote"]:
        raise ValueError("spend 0: the label is not in the quote")
    elif "investing" not in draft["spend_quote"].lower() and "acqui" not in draft["spend_quote"].lower():
        raise ValueError("spend 0: the quote shows neither an acquisitions line nor the investing section")
    sources = []
    for doc, q in [(d["document"], d["quote"]) for d in draft["deals"]] + [
            (draft["spend_document"], draft["spend_quote"]), (draft["assets_document"], draft["assets_quote"])]:
        if {"document": doc, "quote": q} not in [{k: s[k] for k in ("document", "quote")} for s in sources]:
            sources.append({"accession": accession, "document": doc, "quote": q})
    rec = {"deals": deals, "spend": draft["spend"], "prior_total_assets": draft["prior_total_assets"],
           "sources": sources, "note": draft["note"], "drafted": f"claude -p {TODAY}, verified by headline.py"}
    if not draft["spend"]:
        rec["spend_line"] = draft["spend_label"]
    return rec


def verify_year(ticker, end, cik, accession, rec, ua):
    """headline.by_hand() on the draft alone, in a temporary record file: the reader's own gate."""
    real = headline.HAND
    with tempfile.TemporaryDirectory() as tmp:
        headline.HAND = Path(tmp) / "acquisitions.json"
        headline.HAND.write_text(json.dumps({ticker: {end: rec}}), encoding="utf-8")
        try:
            headline.by_hand(ticker, end, cik, {"accession": accession}, ua)
        finally:
            headline.HAND = real


def draft_year(ticker, company, cik, end, accession, ua, required=()):
    prior_end = prior_year_end(end)
    docs = documents(cik, accession, ua)
    failure = None
    for attempt in range(2):
        draft = ask(YEAR_SCHEMA, year_prompt(ticker, company, end, prior_end, docs, required, failure),
                    f"{ticker}_{end}_{attempt}", reuse=attempt == 0)
        try:
            rec = year_record(ticker, cik, end, accession, docs, draft, prior_end)
            for m, d, v in required:
                hit = next((x for x in rec["deals"] if x["member"] == m), None)
                if hit is None or not headline.same(hit["size"], v):
                    raise ValueError(f"required deal {m} ({v:,}) missing or at another size")
            verify_year(ticker, end, cik, accession, rec, ua)
            return rec, None
        except (ValueError, SystemExit) as e:
            failure = str(e)
    return None, failure


# --- a deal's assets acquired --------------------------------------------------------------------------------------------

def assets_prompt(ticker, company, member, name, when, docs, failure):
    words = [w for w in re.findall(r"[A-Za-z][a-z]+", re.sub(r"Member$", "", member.split(":")[-1]))
             if len(w) >= 4] + [w for w in re.findall(r"[A-Za-z]{4,}", name) if w.lower() not in
                                {"corporation", "company", "incorporated", "limited", "holdings", "acquisition",
                                 "business", "member", "group"}]
    pats = [(r"|".join(re.escape(w) for w in sorted(set(words))), 1200, 2500, 60_000)] if words else []
    pats += [(r"purchase price|allocat|assets acquired|liabilities assumed|net assets", 900, 1800, PASSAGE_CAP)]
    body = passages(docs, pats)
    retry = f"\nA previous draft failed this check: {failure}\nFix that in this draft.\n" if failure else ""
    return f"""Company: {company} ({ticker}). The deal: {name} (XBRL member {member}), dated {when}. The filing is
the 10-K whose XBRL tags this deal. Find the total assets acquired in this deal, goodwill included, as the filing
states them, and return one of three kinds:

* `kind` "table": the purchase price allocation table. `quote` is the table copied verbatim from the passages,
  from its unit heading ("(In millions" or "(In thousands", which must be inside the quote) through its last row.
  `unit` is 1000 or 1000000. `columns` is how many numbers follow each row label (a table for two deals side by
  side has 2; a dash cell counts as a number), `column` the 0-based index of this deal's column. `assets` lists the row labels, exactly as printed, that
  together are the gross assets acquired (either every asset row, or the single "Total assets acquired" row when the
  table prints one); `liabilities` the row labels for liabilities assumed (or the single total liabilities row, or
  empty when the table has none); `total` is one row label, the table's net total (net assets acquired, total
  purchase price, total consideration). The assets less the liabilities must equal that total.
* `kind` "prose": the allocation is written as sentences. `quote` is the verbatim passage. `assets`,
  `liabilities` and `total` each list verbatim phrases from the quote, each containing one amount written as
  "$X million" or "$X billion", such that the asset amounts less the liability amounts equal the total amounts.
  `unit`, `columns`, `column` are 0.
* `kind` "not_determinable": the filing gives no gross assets acquired (only net assets, only goodwill and
  intangibles, or no allocation at all). `quote` is the verbatim passage that shows what the filing does state
  about this deal's purchase price allocation; other fields are empty or 0. Use this only when the passages truly
  carry no gross figure.
* `kind` "unreadable": the filing does state the allocation, but the table cannot be read row by row from the
  text (footnote markers such as "(1)" sit between its numbers, rows are split across lines, or the columns are
  not whole numbers), so a person must read it. `quote` is the verbatim passage; `note` says why.

`document` is the document the quote comes from. `note` explains your choice in one or two sentences.
{retry}
Passages:

{body}"""


def assets_record(docs, draft, accession):
    kind = draft["kind"]
    if kind == "unreadable":
        raise ValueError(f"unreadable by the model: {draft['note'][:200]}")
    if draft["document"] not in docs:
        raise ValueError(f"document {draft['document']!r} is not one of {list(docs)}")
    if len(draft["quote"]) < 20 or draft["quote"] not in docs[draft["document"]]:
        raise ValueError(f"quote not found verbatim in {draft['document']}: {draft['quote'][:80]!r}")
    base = {"accession": accession, "document": draft["document"], "quote": draft["quote"], "note": draft["note"],
            "drafted": f"claude -p {TODAY}, verified by headline.py"}
    if kind == "not_determinable":
        return {"not_determinable": True, "sources": [{k: base[k] for k in ("accession", "document", "quote")}],
                "note": draft["note"], "drafted": base["drafted"]}
    if kind == "prose":
        if len(draft["total"]) < 1 or not draft["assets"]:
            raise ValueError("prose: assets and total phrases are needed")
        return base | {"prose": True, "assets": draft["assets"], "liabilities": draft["liabilities"],
                       "total": draft["total"]}
    if draft["unit"] not in (1000, 1_000_000) or len(draft["total"]) != 1 or not draft["assets"]:
        raise ValueError("table: unit, one total row and asset rows are needed")
    return base | {"unit": draft["unit"], "columns": draft["columns"], "column": draft["column"],
                   "assets": draft["assets"], "liabilities": draft["liabilities"], "total": draft["total"][0]}


def draft_assets(ticker, company, cik, member, name, when, accession, ua):
    docs = documents(cik, accession, ua)
    failure = None
    for attempt in range(2):
        draft = ask(ASSETS_SCHEMA, assets_prompt(ticker, company, member, name, when, docs, failure),
                    f"{ticker}_{re.sub(r'[^A-Za-z0-9]+', '_', member)}_{attempt}", reuse=attempt == 0)
        try:
            rec = assets_record(docs, draft, accession)
            headline.assets_from_record(ticker, member, rec, cik, ua)  # the reader's gate; None is a valid outcome
            return rec, None
        except (ValueError, SystemExit) as e:
            failure = str(e)
    return None, failure


# --- the loop ------------------------------------------------------------------------------------------------------------

def merge(path, ticker, key, rec):
    records = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    records.setdefault(ticker, {})[key] = rec
    records[ticker] = dict(sorted(records[ticker].items()))
    path.write_text(json.dumps(records, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def run_reader(ticker, out_dir):
    headline.OUT = out_dir
    sys.argv = ["headline.py", ticker]
    try:
        headline.main()
        return None
    except SystemExit as stop:
        return str(stop)


def one(ticker, ua, out_dir, log):
    h = json.loads((headline.HISTORY / f"{ticker}.json").read_text(encoding="utf-8"))
    cik, company = h["cik"], h["company"]
    drafted = []
    for round_ in range(MAX_ROUNDS):
        stop = run_reader(ticker, out_dir)
        if stop is None:
            return {"status": "pass", "rounds": round_ + 1, "records": drafted}
        if m := PRE_XBRL.match(stop):
            end, acc = m.groups()
            log(f"{ticker}: drafting {end} from {acc}")
            rec, why = draft_year(ticker, company, cik, end, acc, ua)
            if rec is None:
                return {"status": "draft failed", "rounds": round_ + 1, "records": drafted, "item": f"{end} {acc}",
                        "message": why}
            merge(headline.HAND, ticker, end, rec)
            drafted.append(f"acquisitions {end}")
            continue
        if m := TAGGED_LATER.match(stop):
            member, when, acc, v, year, _ = m.groups()
            records = json.loads(headline.HAND.read_text(encoding="utf-8"))
            if "drafted" not in records.get(ticker, {}).get(year, {}):
                return {"status": "stop", "rounds": round_ + 1, "records": drafted, "message": stop}  # a person's record
            filing = next(s["accession"] for s in records[ticker][year]["sources"])
            required = [(d["member"], d["date"], d["size"]) for d in records[ticker][year]["deals"]
                        if not d["member"].startswith("by_hand:")] + [(member, when, int(v.replace(",", "")))]
            log(f"{ticker}: redrafting {year} with {member} at {v}")
            rec, why = draft_year(ticker, company, cik, year, filing, ua, required)
            if rec is None:
                return {"status": "draft failed", "rounds": round_ + 1, "records": drafted,
                        "item": f"{year} {member}", "message": why}
            merge(headline.HAND, ticker, year, rec)
            drafted.append(f"acquisitions {year} (redrafted for {member})")
            continue
        needs = NEED_ASSETS.findall(stop)
        if needs:
            log(f"{ticker}: drafting assets for {len(needs)} deal(s)")
            with ThreadPoolExecutor(WORKERS) as pool:
                futures = {pool.submit(draft_assets, ticker, company, cik, mem, name, when, acc, ua): (mem, name)
                           for mem, name, when, acc in needs}
                failed = []
                for f, (mem, name) in futures.items():
                    rec, why = f.result()
                    if rec is None:
                        failed.append((mem, why))
                    else:
                        merge(headline.DEAL_ASSETS, ticker, mem, rec)
                        drafted.append(f"deal assets {mem}" + (" (not determinable)" if rec.get("not_determinable") else ""))
            if failed:
                return {"status": "draft failed", "rounds": round_ + 1, "records": drafted,
                        "item": failed[0][0], "message": failed[0][1], "failed": len(failed)}
            continue
        return {"status": "stop", "rounds": round_ + 1, "records": drafted, "message": stop[:400]}
    return {"status": "stop", "rounds": MAX_ROUNDS, "records": drafted, "message": f"no pass after {MAX_ROUNDS} rounds"}


def main():
    global MODEL, EFFORT
    args = sys.argv[1:]
    for flag in ("--model", "--effort"):
        if flag not in args or args.index(flag) + 1 >= len(args):
            raise SystemExit(f"{flag} is required (no default).\n{__doc__}")
        i = args.index(flag)
        if flag == "--model":
            MODEL = args[i + 1]
        else:
            EFFORT = args[i + 1]
        del args[i:i + 2]
    if not args:
        raise SystemExit(__doc__)
    headline.HISTORY = BULK / "history"
    if args == ["--stops"]:
        res = json.loads((BULK / "results.json").read_text(encoding="utf-8"))
        tickers = sorted(t for t, r in res.items() if r["status"] == "stop" and
                         ("predates XBRL" in r["message"] or "need total assets acquired" in r["message"]))
    else:
        tickers = [t.upper() for t in args]
    ua = user_agent()
    results = json.loads(RESULTS.read_text(encoding="utf-8")) if RESULTS.is_file() else {}
    out_dir = Path(tempfile.mkdtemp(prefix="draft_hand_"))
    t0 = time.time()
    log = lambda s: print(f"  {s}", flush=True)
    for i, t in enumerate(tickers, 1):
        t1 = time.time()
        try:
            rec = one(t, ua, out_dir, log)
        except ModelFailure as err:  # the model is unavailable: every later company would fail the same way
            print(f"{i}/{len(tickers)} {t} STOPPED, model call failed: {err}", flush=True)
            raise SystemExit(f"stopped at {t}; {CALLS} has the failing call. Nothing recorded for {t}.")
        except Exception as err:  # a crash is a bug in this script or a network failure, recorded, not fatal
            rec = {"status": "crash", "message": f"{type(err).__name__}: {err}"[:400], "records": []}
        rec["seconds"] = round(time.time() - t1)
        results[t] = rec
        RESULTS.write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
        print(f"{i}/{len(tickers)} {t} {rec['status']} ({len(rec['records'])} record(s), {rec['seconds']}s; "
              f"{(time.time() - t0) / 60:.0f} min so far)", flush=True)
    done = [t for t in tickers if results[t]["status"] == "pass"]
    print(f"{len(done)} of {len(tickers)} pass with drafted records; now: python bulk.py {' '.join(done)}")


if __name__ == "__main__":
    main()
