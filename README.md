# tarjeros.no

Personal academic website of Tarjei Ellingsen Røsvoll, built with a small Python script and hosted free on GitHub Pages.

## What is where

| Path | What it is |
|---|---|
| `src/page.html` | The home page text and design. Edit this to change the site. |
| `data/papers.json` | Articles that get their own page with Google Scholar metadata. A page is built when the entry has an abstract or its PDF is in `files/`. |
| `data/nva_known.json` | NVA records already reviewed for the site. |
| `files/` | Portrait and article PDFs (accepted manuscripts), named as in `papers.json`. |
| `build.py` | Builds the finished site into `public/`. |
| `scripts/check_nva.py` | Weekly check for new NVA records. |
| `.github/workflows/` | Deploys the site on every push; runs the NVA check every Monday. |

## Updating

- **New publication:** the Monday check opens a GitHub issue (you get an email) listing new NVA records. Add the ones you want to `src/page.html`, and add all listed ids to `data/nva_known.json`.
- **Add a PDF:** put the accepted manuscript in `files/` under the file name given in `papers.json`. The article page and its Scholar metadata pick it up on the next build.
- **Add an English abstract:** fill `abstract_en` in `papers.json`. Articles without any abstract (Teologisk tidsskrift 2023, Kritisk juss 2021) get a page once an abstract is added.

Build locally with `python build.py` and open `public/index.html`.

## One-time setup

1. Create a public GitHub repository and upload these files (including the hidden `.github` folder).
2. In the repository: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. Register `tarjeros.no` (needs a Norwegian national ID number) and add these DNS records at the registrar:
   - `A` records for `tarjeros.no`: `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   - `AAAA` records for `tarjeros.no`: `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153`, `2606:50c0:8003::153`
   - `CNAME` record for `www`: `<your-github-username>.github.io`
4. **Settings → Pages → Custom domain:** `tarjeros.no`, then tick **Enforce HTTPS** once it is offered.
5. Recommended: verify the domain under your GitHub account **Settings → Pages**, so nobody else can claim it.
6. Add the site to Google Search Console and submit `https://tarjeros.no/sitemap.xml`. Google Scholar has no submission form; it finds the article pages through the sitemap and links.
