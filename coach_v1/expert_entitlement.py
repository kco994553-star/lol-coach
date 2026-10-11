"""Fail-closed public-document entitlement; never project billing or API access."""
from __future__ import annotations

import datetime as dt
import hashlib
from html.parser import HTMLParser
import re
import urllib.request


MODEL = "gemini-3.8-flash"
SOURCE_URLS = tuple("https://ai.google.dev/gemini-api/docs/" + path
                    for path in ("pricing", "video-understanding", "models"))
MAX_BYTES = 2 * 1024 * 1024
TIMEOUT = 10
_VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())
_NOTICE = ("Preview: The YouTube URL feature is in preview and is available at no charge. "
           "Pricing and rate limits are likely to change.")
_LIMIT = "For the free tier, you can't upload more than 8 hours of YouTube video per day."
_PUBLIC = "You can only upload public videos (not private or unlisted videos)."


class _Node:
    def __init__(self, tag, attrs=(), parent=None):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []

    def has_class(self, name):
        return name in self.attrs.get("class", "").split()

    def nodes(self):
        yield self
        for child in self.children:
            if isinstance(child, _Node):
                yield from child.nodes()

    def text(self, *, omit_new=False):
        if self.tag in ("script", "style") or (omit_new and self.has_class("gemini-api-new")):
            return ""
        return " ".join(" ".join(child.text(omit_new=omit_new) if isinstance(child, _Node)
                                else child for child in self.children).split())


class _DOM(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.root = _Node("root")
        self.stack, self.count = [self.root], 0
        self.feed(source)
        self.close()

    def handle_starttag(self, tag, attrs):
        self.count += 1
        # Official navigation repeats analytics attributes. Only selector/table
        # attributes participate in our proof, and duplicate ones are ambiguous.
        scoped_attrs = [name for name, _ in attrs if name in ("id", "class", "href", "colspan", "rowspan")]
        if self.count > 100_000 or len(self.stack) >= 128 or len(set(scoped_attrs)) != len(scoped_attrs):
            raise ValueError("HTML bound or duplicate attribute")
        node = _Node(tag, attrs, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in _VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if self.stack[-1].tag not in ("script", "style"):
            self.stack[-1].children.append(data)


def _one(nodes):
    values = list(nodes)
    if len(values) != 1:
        raise ValueError("Nonunique selector")
    return values[0]


def _pricing(root):
    nodes = list(root.nodes())
    heading = _one(n for n in nodes if n.tag == "h2" and n.attrs.get("id") == MODEL)
    start = nodes.index(heading)
    end = next((i for i in range(start + 1, len(nodes)) if nodes[i].tag == "h2"), len(nodes))
    scope = nodes[start:end]
    link = _one(n for n in scope if n.tag == "a" and
                n.attrs.get("href") == "/gemini-api/docs/models/" + MODEL)
    if _one(n for n in link.nodes() if n.tag == "code").text() != MODEL:
        raise ValueError("Model code mismatch")
    section = _one(n for n in scope if n.tag == "section" and
                   any(h.tag == "h3" and h.text() == "Standard" for h in n.nodes()))
    _one(n for n in section.nodes() if n.tag == "h3" and n.text() == "Standard")
    table = _one(n for n in section.nodes() if n.tag == "table" and n.has_class("pricing-table"))
    for cell in table.nodes():
        if cell.tag in ("td", "th") and any(cell.attrs.get(a, "1") != "1" for a in ("colspan", "rowspan")):
            raise ValueError("Spanning table cells")
    thead = _one(n for n in table.nodes() if n.tag == "thead")
    header_row = _one(n for n in thead.children if isinstance(n, _Node) and n.tag == "tr")
    headers = [n.text() for n in header_row.children if isinstance(n, _Node) and n.tag == "th"]
    if headers.count("Free Tier") != 1:
        raise ValueError("Free Tier column mismatch")
    column = headers.index("Free Tier")
    tbody = _one(n for n in table.nodes() if n.tag == "tbody")
    rows = [[n.text() for n in row.children if isinstance(n, _Node) and n.tag == "td"]
            for row in tbody.children if isinstance(row, _Node) and row.tag == "tr"]
    prices = []
    for name in ("Input price", "Output price (including thinking tokens)"):
        row = _one(row for row in rows if row and row[0] == name)
        if len(row) != len(headers):
            raise ValueError("Pricing columns mismatch")
        value = row[column]
        if value == "Free of charge":
            prices.append("FREE")
        elif re.fullmatch(r"\$(?:0|[1-9][0-9]*)(?:\.[0-9]{1,6})?(?: per 1M tokens)?", value):
            # A recognized zero dollar cell is still unsupported: do not infer free.
            amount = value.split()[0][1:]
            prices.append("PAID" if any(ch in "123456789" for ch in amount) else "UNKNOWN")
        else:
            prices.append("UNKNOWN")
    if "UNKNOWN" in prices:
        raise ValueError("Unsupported Free Tier price")
    return "PAID_REQUIRED" if "PAID" in prices else "VERIFIED_FREE"


def _youtube(root):
    heading = _one(n for n in root.nodes() if n.tag == "h3" and n.attrs.get("id") == "youtube")
    siblings = heading.parent.children
    scope = []
    for sibling in siblings[siblings.index(heading) + 1:]:
        if isinstance(sibling, _Node):
            if sibling.tag in ("h2", "h3"):
                break
            scope.extend(sibling.nodes())
    notice = _one(n for n in scope if n.tag == "aside" and n.has_class("preview"))
    if notice.text() != _NOTICE:
        raise ValueError("YouTube preview notice changed")
    for required in (_LIMIT, _PUBLIC):
        _one(n for n in scope if n.tag == "li" and n.text() == required)


def _stable(root):
    card = _one(n for n in root.nodes() if n.tag == "a" and n.has_class("gemini-card-centered")
                and n.attrs.get("href") == "/gemini-api/docs/models/" + MODEL)
    _one(n for n in card.nodes() if n.tag == "h3" and n.attrs.get("id") == MODEL)
    status = _one(n for n in card.nodes() if n.tag == "p" and n.has_class("status-subtext"))
    labels = [n for n in status.nodes() if n.has_class("gemini-api-new")]
    if any(n.tag != "span" or n.text() != "New" for n in labels):
        raise ValueError("Unsupported model status label")
    if status.text(omit_new=True) != "Stable":
        raise ValueError("Model is not stable")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _transport(url, *, timeout, max_bytes):
    # Fixed allowlist is enforced before creating a request. No cookies or auth.
    if url not in SOURCE_URLS:
        raise ValueError("Source URL not allowed")
    request = urllib.request.Request(url, headers={"Accept": "text/html"})
    with urllib.request.build_opener(_NoRedirect()).open(request, timeout=timeout) as response:
        return {"status": response.status, "body": response.read(max_bytes + 1),
                "url": response.url, "content_type": response.headers.get("Content-Type", "")}


def verify_free_entitlement(*, transport=None, clock=None):
    """Return safe current UTC proof of documentation, without billing inference.

    transport(url, *, timeout, max_bytes) returns status/body(bytes)/url/content_type.
    clock() returns an aware datetime; injection is intended for offline tests.
    Network, selectors and parsing failures always become UNKNOWN with safe codes.
    """
    now = (clock or (lambda: dt.datetime.now(dt.timezone.utc)))()
    if not isinstance(now, dt.datetime) or now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("clock must return a timezone-aware datetime")
    result = {"status": "UNKNOWN", "checked_at": now.astimezone(dt.timezone.utc).date().isoformat(),
              "model": MODEL, "sources": [], "reasons": []}
    roots, failures = [], []
    for index, url in enumerate(SOURCE_URLS):
        try:
            response = (transport or _transport)(url, timeout=TIMEOUT, max_bytes=MAX_BYTES)
            body = response["body"]
            content_type = response["content_type"].lower().split(";")
            if (response["status"] != 200 or response["url"] != url or
                    not isinstance(body, bytes) or len(body) > MAX_BYTES or
                    content_type[0].strip() != "text/html" or
                    any(part.strip().startswith("charset=") and
                        part.strip()[8:].strip('"') not in ("utf-8", "utf8") for part in content_type[1:])):
                raise ValueError("Invalid source response")
            result["sources"].append({"url": url, "sha256": hashlib.sha256(body).hexdigest()})
            roots.append(_DOM(body.decode("utf-8", errors="strict")).root)
        except Exception:
            roots.append(None)
            failures.append(("PRICING", "YOUTUBE", "MODEL")[index] + "_SOURCE_UNAVAILABLE")
    checks = (_pricing, _youtube, _stable)
    price_status = None
    for index, (root, check) in enumerate(zip(roots, checks)):
        if root is None:
            continue
        try:
            checked = check(root)
            if index == 0:
                price_status = checked
        except Exception:
            failures.append(("PRICING", "YOUTUBE", "MODEL")[index] + "_SCOPE_UNVERIFIED")
    if failures:
        result["reasons"] = failures
    else:
        result["status"] = price_status
        result["reasons"] = ["FREE_TIER_POSITIVE_PRICE" if price_status == "PAID_REQUIRED"
                             else "DOCUMENTED_FREE_ENTITLEMENT"]
    return result
