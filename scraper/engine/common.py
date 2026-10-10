"""What every module and source shares: the run context, HTTP, text helpers, output.

Nothing in here knows about a particular city. City-specific values arrive through
`Ctx` (read from cities/<slug>/city.json and sources.json) or through a source's own
params; a constant naming a place belongs in the city files, not in this package.
"""

from __future__ import annotations

import html as html_lib
import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import requests

ROOT = Path(__file__).resolve().parents[2]
CITIES_DIR = ROOT / "cities"
DATA_DIR = ROOT / "data"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)

PL_MONTHS = {
    "stycznia": 1, "lutego": 2, "marca": 3, "kwietnia": 4, "maja": 5, "czerwca": 6,
    "lipca": 7, "sierpnia": 8, "września": 9, "wrzesnia": 9, "października": 10,
    "pazdziernika": 10, "listopada": 11, "grudnia": 12,
}


# --------------------------------------------------------------------------- #
# run context
# --------------------------------------------------------------------------- #

@dataclass
class Ctx:
    """One city, one run. Handed to every module and every source."""

    slug: str
    city: dict[str, Any]          # cities/<slug>/city.json, the same file the app reads
    sources: dict[str, Any]       # cities/<slug>/sources.json
    today: date = field(default_factory=date.today)

    @property
    def name(self) -> str:
        return self.city["name"]

    @property
    def city_dir(self) -> Path:
        return CITIES_DIR / self.slug

    @property
    def data_dir(self) -> Path:
        path = DATA_DIR / self.slug
        path.mkdir(parents=True, exist_ok=True)
        return path

    def module(self, name: str) -> Optional[dict[str, Any]]:
        """This city's settings for one module, or None when the city does not have it."""
        return self.sources.get(name)

    def input_file(self, relative: str) -> Path:
        """A hand-maintained input file of this city (manual events, waste guide…)."""
        path = (self.city_dir / relative).resolve()
        if self.city_dir.resolve() not in path.parents:
            raise ValueError(f"{relative!r} points outside cities/{self.slug}/")
        return path


SLUG_RX = re.compile(r"^[a-z][a-z0-9]*$")


def load_ctx(slug: str) -> Ctx:
    # The slug becomes a path and arrives from the command line, so "../x" must not
    # walk out of cities/. Same rule as Gradle's check on the flavour name.
    if not SLUG_RX.match(slug or ""):
        raise SystemExit(f"[error] invalid city slug {slug!r}: lowercase letters and digits only")
    city_dir = CITIES_DIR / slug
    if not city_dir.is_dir():
        raise SystemExit(f"[error] no such city: {city_dir}")
    city = json.loads((city_dir / "city.json").read_text(encoding="utf-8"))
    sources_path = city_dir / "sources.json"
    sources = json.loads(sources_path.read_text(encoding="utf-8")) if sources_path.exists() else {}
    return Ctx(slug=slug, city=city, sources=sources)


def all_slugs() -> list[str]:
    return sorted(p.name for p in CITIES_DIR.iterdir() if (p / "city.json").is_file())


# --------------------------------------------------------------------------- #
# logging
# --------------------------------------------------------------------------- #

def log(msg: str) -> None:
    print(msg, file=sys.stderr)


def utf8_streams() -> None:
    """Windows consoles default to cp1250 and choke on the first 'ż'."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001 — older/redirected streams
            pass


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #

RETRY_STATUSES = (403, 429, 500, 502, 503, 504)

# Nothing a city legitimately serves comes near this: Rybnik's GTFS is 0.6 MB and its
# 16 waste PDFs are under 1 MB each. A page that suddenly returns gigabytes is a broken
# or hostile server, and reading it whole would stall the CI runner.
MAX_BYTES = 50 * 1024 * 1024


class TooLarge(Exception):
    pass


CERTS_DIR = Path(__file__).resolve().parents[1] / "certs"
_bundles: dict[tuple[str, ...], str] = {}


def ca_bundle(*extra: str) -> str:
    """The standard CA store plus intermediates a server forgets to send.

    Some municipal servers present only their own certificate and leave out the
    intermediate, which browsers fetch on their own (AIA) and Python does not. The fix
    is to supply that intermediate, verified to chain to a root already in the store,
    from scraper/certs/; never to switch verification off.
    """
    key = tuple(sorted(extra))
    if key not in _bundles:
        import certifi
        import tempfile

        pems = [Path(certifi.where()).read_text(encoding="ascii")]
        for name in key:
            pems.append((CERTS_DIR / name).read_text(encoding="ascii"))
        f = tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False, encoding="ascii")
        f.write("\n".join(pems))
        f.close()
        _bundles[key] = f.name
    return _bundles[key]


def is_web_url(url: Optional[str]) -> bool:
    """http(s) only. Everything that reaches the app's ACTION_VIEW passes through here."""
    return bool(url) and url.strip().lower().startswith(("http://", "https://"))


def same_site(url: str, *allowed_hosts: str) -> bool:
    """Whether a link found on a page stays on hosts we chose to read.

    Parsers follow links they find in third-party HTML. Without this, a defaced or
    compromised page could point the scraper anywhere, internal addresses of the CI
    runner included.
    """
    from urllib.parse import urlsplit

    host = (urlsplit(url).hostname or "").lower()
    if urlsplit(url).scheme not in ("http", "https"):
        return False
    return any(host == h or host.endswith("." + h) for h in (a.lower().removeprefix("www.") for a in allowed_hosts))


def get(
    url: str,
    *,
    session: Optional[requests.Session] = None,
    headers: Optional[dict[str, str]] = None,
    retries: int = 0,
    encoding: Optional[str] = None,
    timeout: int = 30,
    fix_latin1: bool = False,
    params: Optional[dict[str, Any]] = None,
    max_bytes: int = MAX_BYTES,
    verify: Any = True,
) -> requests.Response:
    """GET with optional retry, forced encoding and the latin-1 rescue.

    `retries` is for sources that throttle or block datacentre ranges: rybnik.com.pl
    answers 403 to GitHub Actions runners while serving the same URL to a home
    connection, and a retry helps only when the refusal is rate limiting.

    `fix_latin1`: some servers omit the charset, requests then assumes latin-1 and
    mangles every Polish letter. If the body decodes as UTF-8, it is UTF-8.
    """
    getter = session.get if session else requests.get
    hdrs = headers or {"User-Agent": UA}
    last: Exception | None = None
    for attempt in range(retries + 1):
        try:
            r = getter(url, headers=hdrs, timeout=timeout, params=params, stream=True, verify=verify)
            r.raise_for_status()
            declared = int(r.headers.get("content-length") or 0)
            if declared > max_bytes:
                r.close()
                raise TooLarge(f"{url}: {declared} bytes declared, limit {max_bytes}")
            body = bytearray()
            for chunk in r.iter_content(64 * 1024):
                body.extend(chunk)
                if len(body) > max_bytes:
                    r.close()
                    raise TooLarge(f"{url}: over {max_bytes} bytes")
            r._content = bytes(body)  # what r.content and r.text read from
            if encoding:
                r.encoding = encoding
            elif fix_latin1 and (r.encoding or "").lower() in ("iso-8859-1", "latin-1", "latin_1"):
                try:
                    r.content.decode("utf-8")
                    r.encoding = "utf-8"
                except UnicodeDecodeError:
                    pass
            return r
        except requests.HTTPError as e:
            last = e
            status = e.response.status_code if e.response is not None else 0
            if status not in RETRY_STATUSES:
                raise
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
        except requests.RequestException as e:
            last = e
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
    raise last if last else RuntimeError(f"nie udało się pobrać {url}")


# --------------------------------------------------------------------------- #
# text
# --------------------------------------------------------------------------- #

def fold(text: str) -> str:
    """lowercase + strip Polish diacritics, so keyword stems stay ASCII."""
    lowered = text.lower().replace("ł", "l")
    decomposed = unicodedata.normalize("NFKD", lowered)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def strip_accents(s: str) -> str:
    s = s.replace("ł", "l").replace("Ł", "L")
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def clean_text(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    s = " ".join(s.split())
    return s or None


def strip_html(raw: Optional[str]) -> str:
    from bs4 import BeautifulSoup

    if not raw:
        return ""
    text = BeautifulSoup(html_lib.unescape(raw), "html.parser").get_text(" ", strip=True)
    return " ".join(text.split())


def truncate(text: str, limit: int = 300) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit]
    space = cut.rfind(" ")
    if space > limit * 0.6:
        cut = cut[:space]
    return cut.rstrip(" .,;:–-") + "…"


def slug(text: str) -> str:
    """'Stal Brzeg' → 'stal-brzeg'. Used inside ids, so it must stay stable."""
    lowered = text.lower().replace("ł", "l")
    folded = "".join(c for c in unicodedata.normalize("NFKD", lowered) if not unicodedata.combining(c))
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", folded)).strip("-")


# --------------------------------------------------------------------------- #
# output
# --------------------------------------------------------------------------- #

def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> Optional[dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_source(module: str, kind: str):
    """sources/<module>/<kind>.py — the parser named by a `type` in sources.json."""
    import importlib

    if not re.fullmatch(r"[a-z0-9_]+", kind):
        raise ValueError(f"invalid source type {kind!r}")
    return importlib.import_module(f"sources.{module}.{kind}")
