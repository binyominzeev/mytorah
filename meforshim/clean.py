#!/usr/bin/env python3
"""1. lépés: Sefaria /api/links?with_text=1 válasz -> tisztított, forrásonkénti szöveg.

Nem használ modellt. Kidobja a HTML-t, a lábjegyzeteket és (alapból) a nikudot,
forrásonként csak egy nyelvet tart meg. Ettől az input a töredékére esik vissza.
"""
import argparse
import html
import json
import re
from collections import OrderedDict

NIKUD = re.compile(r"[\u0591-\u05C7]")  # nikud + taamim
SUP_MARKER = re.compile(r'<sup class="footnote-marker">.*?</sup>', re.S)
TAG = re.compile(r"<[^>]+>")
SPACES = re.compile(r"[ \t\r\f\v]+")
FOOTNOTE_OPEN = '<i class="footnote">'

BAVLI_TRACTATES = frozenset({
    "arakhin", "avodah zarah", "baba batra", "baba kamma", "baba metzia", "bekhorot",
    "beitzah", "berakhot", "bava batra", "bava kamma", "bava metzia", "chagigah", "chullin",
    "eruvin", "horayot", "keritot", "ketubot", "kiddushin", "maakkot",
    "makkot", "makkos", "megillah",
    "meilah", "menachot", "moed katan", "niddah", "nazir", "nedarim",
    "pesachim", "rosh hashanah", "sanhedrin", "shabbat", "shekalim", "shevuot", "sotah",
    "sukkah", "taanit", "tamid", "temurah", "yevamot", "yoma", "zevachim",
})
YERUSHALMI_TRACTATES = frozenset({
    "avodah zarah", "baba batra", "baba kamma", "baba metzia", "bava batra", "bava kamma",
    "bava metzia", "berakhot", "beitzah", "bikkurim", "chagigah", "challah", "demai",
    "eruvin", "gittin", "horayot", "kilayim", "ketubot", "kiddushin", "maaser sheni",
    "maaserot", "megillah", "moed katan", "nazir", "nedarim", "niddah", "orlah", "peah",
    "pesachim", "rosh hashanah", "sanhedrin", "shabbat", "shekalim", "shevuot", "sotah",
    "sukkah", "taanit", "terumot", "yevamot", "yoma",
})


def supported_source(entry: dict) -> bool:
    category = entry.get("category")
    title = re.sub(r"[^a-z0-9]+", " ", (entry.get("index_title") or "").casefold()).strip()
    if category == "Commentary":
        return True
    if category == "Kabbalah":
        return title.startswith("zohar")
    if category != "Talmud":
        return False
    for prefix in ("jerusalem talmud ", "talmud yerushalmi ", "yerushalmi "):
        if title.startswith(prefix):
            return title[len(prefix):] in YERUSHALMI_TRACTATES
    for prefix in ("babylonian talmud ", "talmud bavli ", "bavli "):
        if title.startswith(prefix):
            title = title[len(prefix):]
            break
    return title in BAVLI_TRACTATES


def anchor_matches(entry: dict, anchor: str) -> bool:
    if entry.get("anchorRef") == anchor:
        return True
    expanded = entry.get("anchorRefExpanded") or []
    if anchor in expanded:
        return True
    match = re.fullmatch(r"(.+?)\s+(\d+):(\d+)-(\d+)", entry.get("anchorRef", ""))
    target = re.fullmatch(r"(.+?)\s+(\d+):(\d+)", anchor)
    return bool(match and target and match.group(1) == target.group(1)
                and match.group(2) == target.group(2)
                and int(match.group(3)) <= int(target.group(3)) <= int(match.group(4)))


def strip_footnotes(s: str) -> str:
    """Törli a lábjegyzet-jelölőket és a (beágyazott <i>-t is tartalmazó) lábjegyzeteket."""
    s = SUP_MARKER.sub("", s)
    out, i = [], 0
    while True:
        j = s.find(FOOTNOTE_OPEN, i)
        if j < 0:
            out.append(s[i:])
            break
        out.append(s[i:j])
        depth, k = 1, j + len(FOOTNOTE_OPEN)
        while depth and k < len(s):
            o = s.find("<i", k)
            c = s.find("</i>", k)
            if c < 0:
                k = len(s)
                break
            if 0 <= o < c:
                depth += 1
                k = o + 2
            else:
                depth -= 1
                k = c + 4
        i = k
    return "".join(out)


def flatten(x) -> str:
    if isinstance(x, str):
        return x
    if isinstance(x, list):
        return "\n".join(p for p in (flatten(e) for e in x) if p.strip())
    return ""


def clean_text(raw: str, keep_nikud: bool = False) -> str:
    s = strip_footnotes(raw)
    s = s.replace("<br>", "\n").replace("<br/>", "\n")
    s = s.replace("<b>", "«").replace("</b>", "»")  # dibur hámátchil jelölése
    s = TAG.sub("", s)
    s = html.unescape(s)
    s = s.replace("\u05BE", "-")  # makkef ne olvadjon össze a szavakkal
    if not keep_nikud:
        s = NIKUD.sub("", s)
    lines = [SPACES.sub(" ", ln).strip() for ln in s.split("\n")]
    return "\n".join(ln for ln in lines if ln)


def pick(entry: dict, lang: str):
    he, en = flatten(entry.get("he")), flatten(entry.get("text"))
    order = [("he", he), ("en", en)] if lang in ("auto", "he") else [("en", en), ("he", he)]
    for code, txt in order:
        if txt.strip():
            return code, txt
    return None, ""


def clean_links(data, lang="auto", keep_nikud=False, anchor=None, category=None):
    """`data`: Sefaria /api/links lista. `anchor`: ezt a verset lefedő horgonyok; alapból a kommentárok,
    Zohár, Bavli és Yerushalmi forrásai maradnak meg."""
    groups = OrderedDict()
    for e in data:
        if category and e.get("category") != category:
            continue
        if not category and not supported_source(e):
            continue
        if anchor and not anchor_matches(e, anchor):
            continue
        code, raw = pick(e, lang)
        txt = clean_text(raw, keep_nikud)
        if not txt:
            continue
        name = (e.get("collectiveTitle") or {}).get("en") or e.get("index_title") or "?"
        g = groups.setdefault(name, {"name": name, "entries": []})
        g["entries"].append((e.get("commentaryNum", 0), e.get("sourceRef", ""), code, txt))
    result = []
    for name, g in groups.items():
        g["entries"].sort(key=lambda t: t[0])
        langs = sorted({t[2] for t in g["entries"]})
        body = "\n".join(f"[{ref}]\n{txt}" for _, ref, _, txt in g["entries"])
        result.append({"name": name, "lang": "+".join(langs), "text": body, "chars": len(body),
                       "entries": [{"ref": ref, "text": txt} for _, ref, _, txt in g["entries"]]})
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("links_json")
    ap.add_argument("--lang", default="auto", choices=["auto", "he", "en"])
    ap.add_argument("--keep-nikud", action="store_true")
    ap.add_argument("--out", default="cleaned.json")
    ap.add_argument("--anchor", help='csak az erre a versre horgonyzott bejegyzések, pl. "Genesis 17:17"')
    a = ap.parse_args()
    with open(a.links_json, encoding="utf-8") as f:
        res = clean_links(json.load(f), a.lang, a.keep_nikud, a.anchor)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    total = sum(r["chars"] for r in res)
    print(f"{len(res)} forrás, {total} karakter (~{total // 3} token durván) -> {a.out}")
