"""S&P 500 constituents with GICS sector and sub-industry, checked against the SEC's own ticker file.

Source: the constituents table on Wikipedia's "List of S&P 500 companies" (GICS is S&P/MSCI's
taxonomy; this is a secondhand copy). Every row's CIK is matched against SEC company_tickers.json;
a mismatch is recorded with both values, never silently accepted. Writes data/sp500.json.

Usage: python universe.py
"""
import json
import urllib.request
from datetime import date
from html.parser import HTMLParser

from pull import ROOT, RAW, user_agent

URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
CACHE = RAW / "sp500" / "list_of_sp500_companies.html"
OUT = ROOT / "data" / "sp500.json"
COLUMNS = ["Symbol", "Security", "GICS Sector", "GICS Sub-Industry", "Headquarters Location", "Date added", "CIK",
           "Founded"]


class Constituents(HTMLParser):
    """Rows of the table with id="constituents", as lists of cell text."""

    def __init__(self):
        super().__init__()
        self.depth, self.rows, self.row, self.cell = 0, [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == "table" and (self.depth or dict(attrs).get("id") == "constituents"):
            self.depth += 1
        elif self.depth == 1 and tag == "tr":
            self.row = []
        elif self.depth == 1 and tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_endtag(self, tag):
        if tag == "table" and self.depth:
            self.depth -= 1
        elif self.depth == 1 and tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif self.depth == 1 and tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def main():
    ua = user_agent()
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    if not CACHE.exists():
        req = urllib.request.Request(URL, headers={"User-Agent": ua})
        with urllib.request.urlopen(req) as r:
            CACHE.write_bytes(r.read())
    parser = Constituents()
    parser.feed(CACHE.read_text(encoding="utf-8"))
    header, *rows = parser.rows
    if header != COLUMNS:
        raise SystemExit(f"constituents table columns changed: {header}")
    if not 495 <= len(rows) <= 510:
        raise SystemExit(f"expected about 500 constituents, found {len(rows)}")

    sec = json.loads((RAW / "company_tickers.json").read_text(encoding="utf-8"))
    sec_by_ticker = {r["ticker"]: r for r in sec.values()}
    companies, mismatches = [], []
    for row in rows:
        rec = dict(zip(COLUMNS, row))
        ticker = rec["Symbol"].replace(".", "-")  # Wikipedia BRK.B -> SEC BRK-B
        cik = int(rec["CIK"])
        s = sec_by_ticker.get(ticker)
        if s is None or s["cik_str"] != cik:
            mismatches.append({"ticker": ticker, "wikipedia_cik": cik, "sec_cik": s["cik_str"] if s else None,
                               "sec_title": s["title"] if s else None})
        companies.append({"ticker": ticker, "name": rec["Security"], "sector": rec["GICS Sector"],
                          "sub_industry": rec["GICS Sub-Industry"], "cik": cik})
    out = {"source": URL, "retrieved": date.fromtimestamp(CACHE.stat().st_mtime).isoformat(),
           "sec_crosscheck": "company_tickers.json", "cik_mismatches": mismatches, "companies": companies}
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sectors = sorted({c["sector"] for c in companies})
    print(f"data/sp500.json: {len(companies)} companies, {len(sectors)} sectors, "
          f"{len({c['sub_industry'] for c in companies})} sub-industries, {len(mismatches)} CIK mismatch(es)")
    for mm in mismatches:
        print(f"  {mm}")


if __name__ == "__main__":
    main()
