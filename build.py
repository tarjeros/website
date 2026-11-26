#!/usr/bin/env python3
"""Build tarjeros.no.

Reads src/page.html (the page body, also used for the private preview) and
data/papers.json, and writes the finished site to public/:

  public/index.html            the home page, with search-engine metadata
  public/papers/<slug>.html    one page per article that has an abstract or a PDF,
                               carrying Google Scholar citation_* tags
  public/papers/<slug>.pdf     copied from files/ when present
  public/portrait.jpg, sitemap.xml, robots.txt

Run:  python build.py            (site)
      python build.py --preview  (also writes preview/ for the claude.ai draft page)
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SITE = "https://tarjeros.no"
NAME = "Tarjei Ellingsen Røsvoll"
ORCID = "https://orcid.org/0009-0000-1437-7042"

SRC = (ROOT / "src" / "page.html").read_text(encoding="utf-8")
PAPERS = json.loads((ROOT / "data" / "papers.json").read_text(encoding="utf-8"))["papers"]
FILES = ROOT / "files"

e = html.escape


def split_page(src):
    head, sep, body = src.partition('<div class="wrap">')
    if not sep:
        sys.exit("src/page.html: could not find <div class=\"wrap\">")
    head = re.sub(r"<title>.*?</title>\s*", "", head, flags=re.S)
    head = re.sub(r'<meta name="claude:[^>]*>\s*', "", head)
    head = re.sub(r'<meta name="description"[^>]*>\s*', "", head)
    return head.strip(), sep + body


HEAD_ASSETS, BODY = split_page(SRC)
DESCRIPTION = re.search(r'<meta name="description" content="([^"]*)"', SRC).group(1)


def doc(lang, title, head_extra, body):
    return (
        "<!doctype html>\n"
        f'<html lang="{lang}">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        f"<title>{e(title)}</title>\n"
        f"{head_extra}\n{HEAD_ASSETS}\n</head>\n<body>\n{body}\n</body>\n</html>\n"
    )


def has_page(p):
    return bool(p.get("abstract_no") or p.get("abstract_en") or pdf_exists(p))


def pdf_exists(p):
    return bool(p.get("pdf")) and (FILES / p["pdf"]).is_file()


def display_author(a):
    last, _, first = a.partition(", ")
    return f"{first} {last}".strip()


def apa_initials(a):
    last, _, first = a.partition(", ")
    initials = " ".join(f"{n[0]}." for n in first.split())
    return f"{last}, {initials}"


def paper_page(p, preview=False):
    url = f"{SITE}/papers/{p['slug']}.html"
    year = p["date"][:4]
    meta = [
        ("citation_title", p["title"]),
        *[("citation_author", a) for a in p["authors"]],
        ("citation_publication_date", p["date"]),
        ("citation_journal_title", p["journal"]),
        ("citation_publisher", p.get("publisher", "")),
        ("citation_issn", p.get("issn", "")),
        ("citation_volume", p.get("volume", "")),
        ("citation_issue", p.get("issue", "")),
        ("citation_firstpage", p.get("firstpage", "")),
        ("citation_lastpage", p.get("lastpage", "")),
        ("citation_doi", p.get("doi", "")),
        ("citation_language", p.get("language", "")),
        ("citation_abstract_html_url", url),
    ]
    if pdf_exists(p):
        meta.append(("citation_pdf_url", f"{SITE}/papers/{p['pdf']}"))
    head = "\n".join(f'<meta name="{k}" content="{e(v)}">' for k, v in meta if v)
    abstract = p.get("abstract_en") or p.get("abstract_no") or ""
    head += f'\n<meta name="description" content="{e(abstract[:280])}">'
    head += f'\n<link rel="canonical" href="{url}">'

    authors = " and ".join(display_author(a) for a in p["authors"])
    vol = p.get("volume", "")
    iss = f"({p['issue'].replace('-', '–')})" if p.get("issue") else ""
    pages = f", {p['firstpage']}–{p['lastpage']}" if p.get("firstpage") else ""
    cite_authors = ", & ".join(apa_initials(a) for a in p["authors"])
    cite = (f"{e(cite_authors)} ({year}). {e(p['title'])}. <i>{e(p['journal'])}</i>, "
            f"<i>{e(vol)}</i>{e(iss)}{e(pages)}. https://doi.org/{e(p['doi'])}")

    blocks = []
    if p.get("abstract_en"):
        blocks.append(f'<h2>Abstract</h2>\n<div class="abstract"><p>{e(p["abstract_en"])}</p></div>')
    if p.get("abstract_no"):
        label = "Sammendrag (Norwegian)" if p.get("abstract_en") else "Abstract (in Norwegian)"
        blocks.append(f'<h2>{label}</h2>\n<div class="abstract" lang="no"><p>{e(p["abstract_no"])}</p></div>')

    tags = [f'<a class="tag" href="https://doi.org/{e(p["doi"])}">doi:{e(p["doi"])}</a>']
    if pdf_exists(p):
        label = f"Full text (PDF, {p['license']})" if p.get("license") else "Accepted manuscript (PDF)"
        tags.append(f'<a class="tag" href="{e(p["pdf"])}">{e(label)}</a>')
    elif p.get("nva"):
        tags.append(f'<a class="tag" href="{e(p["nva"])}">NVA record</a>')

    if p.get("license"):
        rights = f'<p class="note">Published open access under {e(p["license"])}.</p>'
    elif pdf_exists(p):
        rights = '<p class="note">The PDF is the author’s accepted manuscript. Please cite the published version.</p>'
    else:
        rights = ""

    home = "../"
    body = f"""<div class="wrap">
  <header>
    <p class="crumb"><a href="{home}">← {e(NAME)}</a></p>
    <span class="kicker note">Article · {e(p['journal'])} · {e(year)}</span>
    <h1 class="paper-title" lang="no">{e(p['title'])}</h1>
    <span class="gl">{e(p.get('gloss', ''))}</span>
    <p class="role">{e(authors)} <span>· <i>{e(p['journal'])}</i> {e(vol)}{e(iss)}{e(pages)}</span></p>
  </header>
  <section>
    {chr(10).join(blocks)}
  </section>
  <section>
    <h2>Cite</h2>
    <p class="cite">{cite}</p>
    <div class="tags">{''.join(tags)}</div>
    {rights}
  </section>
  <footer><a href="{home}">{e(NAME)}</a> · Associate Professor of Law, University of Inland Norway</footer>
</div>"""
    return doc("en", f"{p['title']} – {NAME}", head, body)


def person_jsonld():
    data = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": NAME,
        "url": SITE + "/",
        "image": SITE + "/portrait.jpg",
        "jobTitle": "Associate Professor of Law",
        "email": "mailto:tarjei.rosvoll@inn.no",
        "affiliation": {"@type": "CollegeOrUniversity", "name": "University of Inland Norway",
                        "url": "https://www.inn.no/"},
        "alumniOf": {"@type": "CollegeOrUniversity", "name": "University of Bergen"},
        "knowsAbout": ["Administrative law", "Constitutional law", "Delegation", "Agencification",
                       "Legal theory", "Legal history", "Public administration"],
        "sameAs": [ORCID, "https://scholar.google.com/citations?user=wThmioMAAAAJ",
                   "https://nva.sikt.no/research-profile/1103479",
                   "https://www.inn.no/english/find-an-employee/tarjei-rosvoll.html",
                   "https://www.youtube.com/@tarjeros"],
    }
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + "</script>"


def index_page():
    body = re.sub(r'\s*<p class="draft">.*?</p>\n', "\n", BODY, count=1, flags=re.S)
    head = "\n".join([
        f'<meta name="description" content="{e(DESCRIPTION)}">',
        f'<link rel="canonical" href="{SITE}/">',
        f'<meta property="og:type" content="profile">',
        f'<meta property="og:title" content="{e(NAME)}">',
        f'<meta property="og:description" content="{e(DESCRIPTION)}">',
        f'<meta property="og:url" content="{SITE}/">',
        f'<meta property="og:image" content="{SITE}/portrait.jpg">',
        f'<link rel="me" href="{ORCID}">',
        person_jsonld(),
    ])
    return doc("en", NAME, head, body)


def check_links(built):
    linked = set(re.findall(r'href="papers/([a-z0-9-]+)\.html"', SRC))
    problems = []
    for slug in linked - built:
        problems.append(f"ERROR: the home page links to papers/{slug}.html, but that page is not built "
                        f"(no abstract or PDF in data/papers.json / files/).")
    for slug in built - linked:
        problems.append(f"WARNING: papers/{slug}.html is built but the home page does not link to it.")
    return problems


def main():
    preview = "--preview" in sys.argv
    out = ROOT / "public"
    if out.exists():
        shutil.rmtree(out)
    (out / "papers").mkdir(parents=True)

    built = set()
    for p in PAPERS:
        if not has_page(p):
            continue
        (out / "papers" / f"{p['slug']}.html").write_text(paper_page(p), encoding="utf-8")
        if pdf_exists(p):
            shutil.copy2(FILES / p["pdf"], out / "papers" / p["pdf"])
        built.add(p["slug"])

    (out / "index.html").write_text(index_page(), encoding="utf-8")
    shutil.copy2(FILES / "portrait.jpg", out / "portrait.jpg")
    if (FILES / "docs").is_dir():
        shutil.copytree(FILES / "docs", out / "docs")

    urls = [SITE + "/"] + [f"{SITE}/papers/{s}.html" for s in sorted(built)]
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
        + "</urlset>\n", encoding="utf-8")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8")

    if preview:
        prev = ROOT / "preview"
        if prev.exists():
            shutil.rmtree(prev)
        shutil.copytree(out / "papers", prev / "papers")
        shutil.copy2(ROOT / "src" / "page.html", prev / "index.html")
        shutil.copy2(FILES / "portrait.jpg", prev / "portrait.jpg")
        if (out / "docs").is_dir():
            shutil.copytree(out / "docs", prev / "docs")

    problems = check_links(built)
    for msg in problems:
        print(msg)
    print(f"Built home page and {len(built)} paper page(s): {', '.join(sorted(built)) or 'none'}")
    if any(m.startswith("ERROR") for m in problems):
        sys.exit(1)


if __name__ == "__main__":
    main()
