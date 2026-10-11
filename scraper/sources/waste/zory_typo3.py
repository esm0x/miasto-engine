"""Żory's waste schedules from zory.pl: one PDF for houses, a Word file per fraction for blocks.

Params:
    {"page": "https://www.zory.pl/dla-mieszkancow/gospodarka-odpadami/harmonogramy"}

Single-family: one PDF with a table per rejon, headed "Rejon N: <streets>", a row per
fraction and the months across. The street list may pin a street to some numbers
("Wodzisławska 218, 244, 252, 258" in rejon 2, while rejon 1 has the rest of
Wodzisławska). Between the rejony sit "Rejon K utrudniony" tables: houses on
hard-to-reach stretches, collected on other days. Each becomes a rejon of its own and,
being number-specific, wins over the whole-street rejon in the app.
Some tables have 13 columns, some 37 (three per month, values in any of them, a few
shifted by one), so a value belongs to the nearest month header at or before its column.

Multi-family: about ten .docx, one per fraction, each laid out differently: a column
per month with dates, "1 raz w tygodniu wtorek", a block of addresses over a row of
months, merged cells with "27.02 – Elektro 27.03 - Opony". Addresses are free text:
"Centralna 4, 17,19,21, 25-37, Giedroycia 1", glued neighbours ("…10Piastów…"),
initials that come and go ("J. Giedroycia" / "Giedroycia", "Z. Nałkowskiej" /
"Zofii Nałkowskiej"). Every file is read into buildings (street, number); a street
named without numbers means all its buildings the other files know, unless a row names
the building itself. Buildings with the same dates for every fraction form one rejon.
Weekly collections are expanded into the year's dates, so a block's rejon carries
pickups only, like everything else.

Holidays: neither the PDF nor the Word files say what happens to a weekly collection
on a public holiday. Dates written out are published as written; weekly collections
expanded here skip public holidays (see weekly_dates).
"""

from __future__ import annotations

import io
import re
import zipfile
from collections import defaultdict
from datetime import date, timedelta
from typing import Optional
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

from engine.common import UA, Ctx, fold, get, log, same_site, slug

HEADERS = {"User-Agent": UA, "Accept-Language": "pl-PL,pl;q=0.9"}
HOSTS = ("zory.pl",)

# Ceilings far above the real files (PDF 1 MB / 23 pages, each .docx under 60 KB with
# document.xml under 1 MB, at most ~40 numbers in one address cell, ~400 blocks). Past
# them the file is broken or hostile: a 1 KB .docx can expand to gigabytes of XML, or
# ask for a cell spanning fifty million columns, and the CI job would hang for hours.
MAX_PDF_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 120
MAX_DOCX_BYTES = 5 * 1024 * 1024
MAX_XML_BYTES = 10 * 1024 * 1024
MAX_SPAN = 64
MAX_RULES_PER_STREET = 300
MAX_BUILDINGS = 5000
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

MONTHS = ["styczeń", "luty", "marzec", "kwiecień", "maj", "czerwiec", "lipiec",
          "sierpień", "wrzesień", "październik", "listopad", "grudzień"]
WEEKDAYS = {"poniedziałek": 0, "wtorek": 1, "środa": 2, "czwartek": 3, "piątek": 4, "sobota": 5}
LOWER = "a-ząćęłńóśźż"
UPPER = "A-ZĄĆĘŁŃÓŚŹŻ"

# PDF row label → contract type.
SINGLE_TYPES = {
    "zmieszane": "ZMIESZANE",
    "bioodpady kuchenne": "BIO",
    "odpady zielone": "ZIELONE",
    "popiół": "POPIOLY",
    "papier/plastik/szkło": "SEGREGOWANE",
    "elektronika": "ELEKTRO",
    "gabaryty": "GABARYTY",
    "opony": "OPONY",
    "akcja liście": "LISCIE_CHOINKI",
    "akcja choinki": "LISCIE_CHOINKI",
    "liście": "LISCIE_CHOINKI",
    "choinki": "LISCIE_CHOINKI",
}

# Word file name fragment → contract type.
MULTI_FILES = [
    ("zmieszanych", "ZMIESZANE"),
    ("bio_kuchenne", "BIO"),
    ("odpady_zielone", "ZIELONE"),
    ("popiol", "POPIOLY"),
    ("papier_plastik", "PAPIER_PLASTIK"),
    ("szklo", "SZKLO"),
    ("segregacja_workowa", "SEGREGOWANE"),
    ("wielkogabaryty", "GABARYTY"),
    ("elektronika", "ELEKTRO"),
    ("choinki_liscie", "LISCIE_CHOINKI"),
]
# "27.02 – Elektro": a label inside a cell overrides the file's type.
CELL_LABELS = {"elektro": "ELEKTRO", "opony": "OPONY", "gabaryty": "GABARYTY"}


# --------------------------------------------------------------------------- numbers
def number_rules(spec: str) -> list[dict]:
    """'72, 72B, 114-120, do nr 20, od nr 22 do nr 32, 5A-B' → contract rules. Letters
    drop to the number: the contract keeps house numbers as integers ("128B" → 128)."""
    spec = spec.replace("–", "-").replace("\xa0", " ").strip(" .,")
    if not spec:
        return []
    m = re.match(r"^(?:od\s+nr\.?\s*(\d+)\s*)?do\s+nr\.?\s*(\d+)$", spec, re.IGNORECASE)
    if m:
        return [{"from": int(m.group(1)) if m.group(1) else None, "to": int(m.group(2)), "parity": None}]
    # "32 34" with the comma missing, and "1 i 3".
    spec = re.sub(r"(\d)\s+(?=\d)", r"\1, ", spec)
    rules: list[tuple[int, int]] = []
    for part in re.split(r"\s*(?:,|\bi\b)\s*", spec):
        part = part.strip()
        # A letter range on one number: "5A-B", "45 C - I", "28 A-D".
        m = re.match(rf"^(\d+)\s*[{LOWER}]?\s*-\s*[{LOWER}]$", part, re.IGNORECASE)
        if m:
            rules.append((int(m.group(1)), int(m.group(1))))
            continue
        # A number range: "25-37", "4-27", "3-3A".
        m = re.match(rf"^(\d+)\s*[{LOWER}]?\s*-\s*(\d+)\s*[{LOWER}]?$", part, re.IGNORECASE)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            rules.append((min(a, b), max(a, b)))
            continue
        m = re.match(r"^(\d+)", part)
        if m:
            rules.append((int(m.group(1)), int(m.group(1))))
    # The same number twice ("116", "116A") is one rule.
    return [{"from": a, "to": b, "parity": None} for a, b in dict.fromkeys(rules)]


OS_700 = "Siedemsetlecia"          # "oś. 700-lecia" must not read as "oś." + number 700
# "3 Maja", "11 Listopada": a street whose name starts with a number. While splitting,
# the number is spelled in letters ("3" → "Nrd") so it reads as part of the name.
DATE_STREET = re.compile(r"\b(\d{1,2})\s+(?=(?:stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|"
                         r"września|października|listopada|grudnia)\b)", re.IGNORECASE)


def split_streets(text: str) -> list[tuple[str, str]]:
    """'Brodecka 11, 11A, Wodzisławska 72, 72B' → [('Brodecka', '11, 11A'), ('Wodzisławska', '72, 72B')]."""
    t = " ".join(text.replace("\xa0", " ").split()).replace("–", "-")
    t = re.sub(r"700\s*-?\s*lecia", OS_700, t, flags=re.IGNORECASE)
    t = DATE_STREET.sub(lambda m: "Nr" + "".join("abcdefghij"[int(c)] for c in m.group(1)) + "Q", t)
    t = t.replace(" / ", ", ")                            # paragraphs inside one Word cell
    # Neighbours glued together: "10Piastów", "16A-BAstrów", "43 Chlebowa", "27 al. Zjednoczonej".
    t = re.sub(rf"(\d[{UPPER}{LOWER}]?(?:-[{UPPER}])?)\s*(?=[{UPPER}][{LOWER}]{{2,}})", r"\1, ", t)
    t = re.sub(r"(\d[A-Za-z]?)\s+(?=(?:al|Al|oś|os)\.?\s)", r"\1, ", t)
    out: list[tuple[str, list[str]]] = []
    for tok in (x.strip() for x in t.split(",")):
        if not tok:
            continue
        m = re.match(rf"^(?P<name>[^\d]*?[{UPPER}{LOWER}]{{3,}}[^\d]*?)\s*(?P<rest>(?:od |do |\d).*)?$", tok)
        if m and not re.match(r"^(do|od|nr)\b", tok, re.IGNORECASE):
            out.append((m.group("name"), [m.group("rest") or ""]))
        elif out:
            out[-1][1].append(tok)
    unspell = lambda n: re.sub(r"Nr([a-j]+)Q", lambda m: "".join(str("abcdefghij".index(c)) for c in m.group(1)) + " ", n)  # noqa: E731
    return [(unspell(n.replace(OS_700, "700-lecia")), ", ".join(x for x in parts if x)) for n, parts in out]


# --------------------------------------------------------------------------- names
def canon(name: str) -> str:
    """One spelling per street: "al."/"Al."/"Aleja" → "Aleja", "oś"/"Osiedle" → "oś."."""
    n = " ".join(name.replace("–", "-").replace("\xa0", " ").split()).strip(" .,")
    n = re.sub(r"\s+-\s+", " ", n)                       # "Alojzego – Frysza"
    n = re.sub(r"\s*-\s*", "-", n)                       # "Herrlinga- Grudzińskiego"
    n = re.sub(r"^(al\.?|aleja)\s+", "Aleja ", n, flags=re.IGNORECASE)
    n = re.sub(r"^(oś\.?|os\.|osiedle)\s*", "oś. ", n, flags=re.IGNORECASE)
    return n


def key(name: str) -> str:
    """Matching key: folded, no initials or titles ("J. Giedroycia" = "Giedroycia")."""
    n = fold(canon(name))
    n = re.sub(r"\b[a-z]{1,3}\.\s*", "", n)              # "j.", "ks.", "gen.", "św.", "oś."
    return re.sub(r"[^a-z0-9]+", "", n)


# --------------------------------------------------------------------------- dates
def days_in(year: int, month: int) -> int:
    return (date(year + month // 12, month % 12 + 1, 1) - timedelta(days=1)).day


def parse_days(cell: str, year: int, month: int) -> list[str]:
    out = []
    for d in re.findall(r"\d{1,2}", cell or ""):
        if 1 <= int(d) <= days_in(year, month):
            out.append(date(year, month, int(d)).isoformat())
    return out


def holidays(year: int) -> set[date]:
    """Polish public holidays (ustawa o dniach wolnych od pracy)."""
    a, b, c = year % 19, year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741
    m = (a + 11 * h + 22 * l) // 451
    easter = date(year, (h + l - 7 * m + 114) // 31, (h + l - 7 * m + 114) % 31 + 1)
    fixed = [(1, 1), (1, 6), (5, 1), (5, 3), (8, 15), (11, 1), (11, 11), (12, 25), (12, 26)]
    if year >= 2025:
        fixed.append((12, 24))                          # Wigilia, wolna od 2025
    return {date(year, mo, dy) for mo, dy in fixed} | {
        easter, easter + timedelta(days=1), easter + timedelta(days=49), easter + timedelta(days=60)}


def weekly_dates(text: str, year: int, months: list[int]) -> Optional[list[str]]:
    """'1 raz w tygodniu wtorek', '3 razy w tygodniu poniedziałek-środa-piątek' → dates.
    Public holidays are left out: the schedules do not say where a holiday collection
    moves, and a reminder for 1 January is surely wrong, while a missing one is only
    a missing reminder."""
    t = text.lower()
    if "tygodni" not in t:
        return None
    days = {d for w, d in WEEKDAYS.items() if w in t}
    off = holidays(year)
    return [date(year, m, d).isoformat() for m in months for d in range(1, days_in(year, m) + 1)
            if date(year, m, d).weekday() in days and date(year, m, d) not in off]


def month_index(label: str) -> Optional[int]:
    lab = (label or "").strip().lower()
    if len(lab) < 3:
        return None
    for i, m in enumerate(MONTHS, 1):
        if lab == m or lab.startswith(m[:5]) and len(lab) <= len(m) + 1:
            return i
    return None


def month_columns(row: list[str]) -> Optional[dict[int, int]]:
    """Column → month for a header row, or None if the row is not one."""
    cols = {i: m for i, c in enumerate(row) if (m := month_index(c))}
    return cols if len(cols) >= 2 else None


def month_of(col: int, cols: dict[int, int]) -> Optional[int]:
    """A value's month: the nearest month header at or before its column."""
    before = [c for c in cols if c <= col]
    return cols[max(before)] if before else None


# --------------------------------------------------------------------------- source files
def find_files(page_url: str, year: int) -> tuple[Optional[str], list[str]]:
    from bs4 import BeautifulSoup

    from modules.waste import NotPublished

    html = get(page_url, headers=HEADERS, retries=2, allowed_hosts=HOSTS).text
    pdf, docx = None, []
    for a in BeautifulSoup(html, "html.parser").select("a[href]"):
        url = urljoin(page_url, a["href"])
        low = url.lower()
        if not same_site(url, "zory.pl") or f"{year}" not in low:
            continue
        if low.endswith(".pdf") and "wielorodzin" not in low and pdf is None:
            pdf = url
        elif low.endswith(".docx") and "wielorodzin" in low and url not in docx:
            docx.append(url)
    if not pdf and not docx:
        raise NotPublished(f"no {year} schedules linked on {page_url}")
    return pdf, docx


# --------------------------------------------------------------------------- single-family
def parse_single(data: bytes, year: int) -> tuple[list[dict], list[str]]:
    import pdfplumber

    rejony: list[dict] = []
    problems: list[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        if len(pdf.pages) > MAX_PDF_PAGES:
            raise ValueError(f"PDF has {len(pdf.pages)} pages, expected under {MAX_PDF_PAGES}")
        for page_no, page in enumerate(pdf.pages, 1):
            for table_no, table in enumerate(page.extract_tables(), 1):
                head = " ".join((table[0][0] or "").split()) if table and table[0] else ""
                m = re.match(r"^Rejon\s+(\d+)(\s+utrudniony)?\s*:\s*(.+)$", head, re.IGNORECASE)
                if not m:
                    continue
                cols = next((c for r in table if (c := month_columns([x or "" for x in r]))), None)
                if not cols:
                    problems.append(f"str. {page_no}: brak nagłówka miesięcy pod {head[:40]}")
                    continue
                pickups: dict[str, set[str]] = defaultdict(set)
                for row in table:
                    label = " ".join((row[0] or "").split()).lower()
                    wtype = SINGLE_TYPES.get(label)
                    if not wtype:
                        if label and not month_index(label) and not label.startswith(("rodzaj", "rejon")):
                            problems.append(f"str. {page_no}: nieznany wiersz {label!r}")
                        continue
                    for col, cell in enumerate(row[1:], start=1):
                        if cell and (month := month_of(col, cols)):
                            pickups[wtype].update(parse_days(cell, year, month))
                streets = [{"name": canon(n), "rules": number_rules(nums)} for n, nums in split_streets(m.group(3))]
                n = int(m.group(1))
                if m.group(2):
                    rid = f"rejon-{n}-utrudniony-{page_no}-{table_no}"
                    name = f"Rejon {n} utrudniony ({streets[0]['name'] if streets else page_no})"
                else:
                    rid, name = f"rejon-{n}", f"Rejon {n}"
                rejony.append({
                    "id": rid, "name": name, "district": "Żory", "houseType": "SINGLE_FAMILY",
                    "streets": streets,
                    "pickups": [{"type": t, "dates": sorted(d)} for t, d in sorted(pickups.items()) if d],
                    "weekdayRules": [],
                })
    return rejony, problems


# --------------------------------------------------------------------------- multi-family
def docx_tables(data: bytes) -> list[list[list[str]]]:
    """Tables as grid rows: a merged cell's text sits in its first grid column."""
    zf = zipfile.ZipFile(io.BytesIO(data))
    if zf.getinfo("word/document.xml").file_size > MAX_XML_BYTES:
        raise ValueError("word/document.xml over the size limit")
    x = ET.fromstring(zf.read("word/document.xml"))
    tables = []
    for t in x.iter(W + "tbl"):
        rows = []
        for r in t.findall(W + "tr"):
            cells: list[str] = []
            for c in r.findall(W + "tc"):
                paras = ["".join(n.text or "" for n in p.iter(W + "t")) for p in c.findall(W + "p")]
                span = c.find(f"{W}tcPr/{W}gridSpan")
                cells.append(" / ".join(p.strip() for p in paras if p.strip()))
                try:
                    width = int(span.get(W + "val")) if span is not None else 1
                except (TypeError, ValueError):
                    width = 1
                cells.extend([""] * (min(max(width, 1), MAX_SPAN) - 1))
            rows.append(cells)
        tables.append(rows)
    return tables


def has_words(s: str) -> bool:
    return bool(re.search(rf"[{UPPER}{LOWER}]{{3,}}", s or ""))


def cell_dates(cell: str, month: Optional[int], year: int, wtype: str) -> dict[str, list[str]]:
    """Dates in one cell, by type: weekly text, "27.02 – Elektro" pairs, or days of `month`."""
    pairs = re.findall(rf"(\d{{1,2}})\.(\d{{1,2}})\s*[-–]?\s*([{UPPER}{LOWER}]+)?", cell)
    if pairs:
        out: dict[str, list[str]] = defaultdict(list)
        for d, m, label in pairs:
            t = CELL_LABELS.get(fold(label or ""), wtype)
            try:
                out[t].append(date(year, int(m), int(d)).isoformat())
            except ValueError:
                pass
        return out
    weekly = weekly_dates(cell, year, [month] if month else list(range(1, 13)))
    if weekly is not None:
        return {wtype: weekly}
    return {wtype: parse_days(cell, year, month)} if month else {}


def schedule_rows(tables: list[list[list[str]]], year: int, wtype: str) -> list[tuple[str, dict[str, list[str]]]]:
    """(address text, {type: dates}) for every address block in one Word file."""
    out: list[tuple[str, dict[str, list[str]]]] = []
    for rows in tables:
        cols: Optional[dict[int, int]] = None
        pending: Optional[str] = None
        for row in rows:
            cells = [c.strip() for c in row]
            filled = [c for c in cells if c]
            if not filled:
                continue
            if (c := month_columns(cells)):
                cols = c
                continue
            if fold(cells[0]) in ("ulica", "adres") or not has_words(cells[0]) and not cols:
                continue
            # "Ulica | Nr | Harmonogram" (mixed waste) and "ADRES | Harmonogram" (bio).
            if not cols and re.search("tygodni", cells[-1], re.IGNORECASE):
                address = " ".join(cells[:-1])
                out.append((address, cell_dates(cells[-1], None, year, wtype)))
                continue
            # An address alone in a row, its months and dates in the rows below.
            if len(filled) == 1 and has_words(filled[0]) and not month_index(filled[0]):
                pending = filled[0]
                continue
            if not cols:
                continue
            if has_words(cells[0]):
                address, start = cells[0], 1
            elif pending:
                address, start = pending, 0
            else:
                continue                                 # a sub-header ("| CHOINKI | LIŚCIE")
            dates: dict[str, list[str]] = defaultdict(list)
            for col in range(start, len(cells)):
                if cells[col]:
                    for t, d in cell_dates(cells[col], month_of(col, cols), year, wtype).items():
                        dates[t].extend(d)
            out.append((address, dates))
            if address is pending:
                pending = None
    return out


def parse_multi(files: list[tuple[str, bytes]], year: int) -> tuple[list[dict], list[str]]:
    problems: list[str] = []
    names: dict[str, str] = {}
    # street key → [(lo, hi, type, dates)]; lo/hi None for a street named without numbers.
    rules_by_street: dict[str, list[tuple[Optional[int], Optional[int], str, frozenset]]] = defaultdict(list)
    seen_types: set[str] = set()
    file_types: set[str] = set()

    for url, data in files:
        low = url.lower()
        wtype = next((t for frag, t in MULTI_FILES if frag in low), None)
        if not wtype:
            problems.append(f"nieznany plik {url.rsplit('/', 1)[-1]}")
            continue
        # The page once linked last half-year's file next to the new one; two schedules
        # for one fraction would merge into dates from both. The page lists the newest first.
        if wtype in file_types:
            problems.append(f"drugi plik dla {wtype}, pominięty: {url.rsplit('/', 1)[-1]}")
            continue
        file_types.add(wtype)
        for address, by_type in schedule_rows(docx_tables(data), year, wtype):
            if not any(by_type.values()):
                problems.append(f"{wtype}: brak dat dla {address[:60]!r}")
                continue
            for name, nums in split_streets(address):
                k = key(name)
                if not k:
                    continue
                if k not in names or len(canon(name)) > len(names[k]):
                    names[k] = canon(name)               # the longest spelling: "oś. Powstańców Śląskich"
                rules = number_rules(nums)
                if len(rules) > MAX_RULES_PER_STREET:
                    raise ValueError(f"{wtype}: {len(rules)} numbers for {name[:40]!r}")
                spans = [(r["from"] if r["from"] is not None else 1, r["to"]) for r in rules] or [(None, None)]
                for t, d in by_type.items():
                    if d:
                        seen_types.add(t)
                        rules_by_street[k].extend((lo, hi, t, frozenset(d)) for lo, hi in spans)

    # One street, two spellings: "nalkowskiej" / "zofiinalkowskiej", "powstancow" /
    # "powstancowslaskich". Fold the shorter key into the longer when exactly one fits.
    alias = {}
    for k in names:
        longer = [o for o in names if o != k and (o.endswith(k) or o.startswith(k))]
        if len(longer) == 1:
            alias[k] = longer[0]
    if alias:
        problems.append("ujednolicone nazwy: " + ", ".join(f"{names[a]} → {names[b]}" for a, b in sorted(alias.items())))
    merged: dict[str, list] = defaultdict(list)
    for k, rs in rules_by_street.items():
        merged[alias.get(k, k)].extend(rs)

    # Buildings: each number some row names on its own. A range ("Wojska Polskiego 4-27")
    # gives its dates to the buildings inside it and creates none, or the blocks would
    # get every number in between; only a range with no named building inside stays
    # a unit of its own. A street named without numbers covers what no row names directly.
    if sum(len(rs) for rs in merged.values()) > MAX_BUILDINGS * 20:
        raise ValueError("far more address entries than Żory has blocks")
    groups: dict[tuple, list[tuple[str, Optional[int], Optional[int]]]] = defaultdict(list)
    no_mixed: list[str] = []
    for k, rs in sorted(merged.items()):
        singles = sorted({lo for lo, hi, _, _ in rs if lo is not None and lo == hi})
        units = [(n, n) for n in singles]
        # Units times entries is the cost below; both are a few dozen per street in reality.
        if len(singles) > MAX_RULES_PER_STREET or len(rs) > 20 * MAX_RULES_PER_STREET:
            raise ValueError(f"{names[k]}: {len(singles)} numbers in {len(rs)} entries")
        units += sorted({(lo, hi) for lo, hi, _, _ in rs if lo is not None and lo != hi
                         and not any(lo <= n <= hi for n in singles)})
        # A street some row names whole ("oś. Powstańców Śląskich") keeps a whole-street
        # unit for the buildings no row names, next to any it does name ("… 2"); the app
        # matches a named building first.
        if not units or any(lo is None for lo, _, _, _ in rs):
            units.append((None, None))
        for lo, hi in units:
            types: dict[str, set[str]] = defaultdict(set)
            for t in seen_types:
                own = [d for a, b, tt, d in rs if tt == t and a is not None and lo is not None and a <= lo and hi <= b]
                fallback = [d for a, _, tt, d in rs if tt == t and a is None]
                for d in own or fallback:
                    types[t] |= d
            sig = tuple(sorted((t, tuple(sorted(d))) for t, d in types.items() if d))
            groups[sig].append((k, lo, hi))
            if not types.get("ZMIESZANE"):
                no_mixed.append(f"{names[k]} {lo if lo == hi else f'{lo}-{hi}'}" if lo is not None else names[k])
    if no_mixed:
        problems.append(f"{len(no_mixed)} adresów bez odpadów zmieszanych w plikach dla bloków: " + ", ".join(no_mixed))

    rejony = []
    for sig, members in sorted(groups.items(), key=lambda kv: (kv[1][0][0], kv[1][0][1] or 0)):
        streets: dict[str, list] = defaultdict(list)
        for k, lo, hi in members:
            streets[names[k]].append({"from": lo, "to": hi, "parity": None} if lo is not None else None)
        k0, n0, _ = members[0]
        rejony.append({
            "id": f"bloki-{slug(names[k0])}-{n0 or 0}",
            "name": f"Bloki: {names[k0]}" + (f" {n0}" if n0 else "") + (" i inne" if len(members) > 1 else ""),
            "district": "Żory", "houseType": "MULTI_FAMILY",
            "streets": [{"name": nm, "rules": [] if None in rules else rules} for nm, rules in sorted(streets.items())],
            "pickups": [{"type": t, "dates": list(d)} for t, d in sig],
            "weekdayRules": [],
        })
    return rejony, problems


def fetch(params: dict, ctx: Ctx, failures: list[dict], year: int) -> list[dict]:
    pdf_url, docx_urls = find_files(params["page"], year)
    rejony: list[dict] = []
    if pdf_url:
        pdf = get(pdf_url, headers=HEADERS, timeout=60, retries=2, max_bytes=MAX_PDF_BYTES, allowed_hosts=HOSTS).content
        single, problems = parse_single(pdf, year)
        log(f"[info] domy: {len(single)} rejonów z {pdf_url.rsplit('/', 1)[-1]}")
        for p in problems:
            log(f"[warn] {p}")
        rejony.extend(single)
    else:
        failures.append({"source": params["page"], "error": f"brak PDF zabudowy jednorodzinnej na {year}"})
    if docx_urls:
        if len(docx_urls) > 20:
            raise ValueError(f"{len(docx_urls)} Word files linked, expected about ten")
        files = [(u, get(u, headers=HEADERS, timeout=60, retries=2, max_bytes=MAX_DOCX_BYTES,
                         allowed_hosts=HOSTS).content) for u in docx_urls]
        multi, problems = parse_multi(files, year)
        log(f"[info] bloki: {len(multi)} grup z {len(files)} plików")
        for p in problems:
            log(f"[warn] {p}")
        rejony.extend(multi)
    else:
        failures.append({"source": params["page"], "error": f"brak plików zabudowy wielorodzinnej na {year}"})
    return rejony
