# Round 2 test report: https://ai4me.cfd/ (pristine BentoPDF v2.8.11 at the domain root)

Date: 2026-11-11. Browser: Chrome for Testing 157 (headless, Playwright). Scripts: `test/tools2.py` (tools, adapted from `test/tools.py` with root URLs), `test/round2.py`, `test/sw2.py`, `test/worker2.py`. Raw data: `test/round2.json`, `test/sw2.json`. Tool outputs and screenshots: `outputs2/`. Same samples as round 1 (`samples/`).

**Summary:** All 8 core tools PASS. Every round-1 defect (D1-D9) is FIXED. No BLOCKED items. Two minor observations, no functional new defects.

## Results

| # | Item | Result | Evidence |
|---|------|--------|----------|
| 1a | Homepage `/` loads | PASS | 200, no failed requests, no console errors. |
| 1b | Homepage tool links | PASS | 181 anchors in the rendered DOM, 132 unique internal URLs. 131 return 200, 1 returns 301 (`/blog`). 130 tool links are `/<tool>.html` (e.g. `/merge-pdf.html`). They all return 200, which is how this dist is built, not a JS rewrite. |
| 1c | Crawl of all 132 internal URLs in a browser | PASS | 132/132 load with 200 and 0 console errors. Two `requestfailed` entries (`elk-*.js`, `ghostscript-dynamic-loader-*.js`) are loads aborted by navigating away. Both URLs return 200 when fetched directly. |
| 2a | Merge PDF (3 + 2 pages) | PASS | `merged.pdf`, 2796 B, 5 pages, A4, not encrypted. |
| 2b | Split PDF (range 1-2) | PASS | `split-document.pdf`, 1193 B, 2 pages. |
| 2c | Compress PDF | PASS | 1316 B (input 2265 B), 3 pages. |
| 2d | Rotate PDF (all right) | PASS | 1273 B, 3 pages, `/Rotate` = 90 on all 3 pages. |
| 2e | PDF to JPG | PASS | ZIP of 3 JPEGs (JFIF, 1190x1683, about 15 KB each). |
| 2f | JPG to PDF | PASS | 3015 B, 1 page, 300x225 pt. |
| 2g | Protect PDF | PASS | 3265 B, 3 pages, `Encrypted: yes`, AES-256. `pdfinfo` without a password fails with "Incorrect password". It opens with `secret123`. |
| 2h | Unlock PDF | PASS | 1585 B, 3 pages, not encrypted. |
| 3a | Per-tool chunks load | PASS | No 404 across the 132-page crawl or the 8 tool runs. `/workers/merge.worker.js`, `/config.json`, `/qpdf.wasm` and `/sw.js` all return 200. |
| 3b | flexsearch error gone | PASS | No console errors on `/`, `/merge-pdf` or the 132-page crawl. Typing "merge" in the homepage search shows 4 visible Merge matches with no errors. |
| 3c | PDF worker loads | PASS | `GET /assets/pdf.worker-Cm5pRtDN.js` returns 200 when a PDF is loaded in PDF to JPG. |
| 3d | Service worker | PASS (homepage) | On `/` and `/vi/`: scope `https://ai4me.cfd/`, script `/sw.js`, state `activated`, the page is controlled (also after reload), and there is no scope error. See observation O1. |
| 3e | `/vi/` in Vietnamese | PASS | 200, `<html lang="vi">`, H1 "Bộ công cụ PDF an toàn và riêng tư.", 134 internal links (e.g. `/vi/about`, `/vi/merge-pdf`), all 200. |
| 3f | Language switcher | PASS | `/` to `/vi/` (lang `vi`, 200). `/merge-pdf` to `/vi/merge-pdf` (H1 "Gộp PDF", 200). `/vi/` to `/` (lang `en`, 200). |
| 4 | Old URL `/pdf/merge-pdf` | PASS | `301` to `https://ai4me.cfd/merge-pdf`, which returns 200 with title "Merge PDF Files Free Online..." and a working `#file-input`. |

## Defects D1-D9

The first-round IDs and the labels in the retest request differ. The verdicts below follow the round-1 report; the request's labels are in brackets.

| ID | Defect (round 1) | Verdict | Evidence |
|----|------------------|---------|----------|
| D1 | Tool links rewritten to broken root `.html` URLs | **FIXED** | The `.html` links remain, but they now resolve: 131 of 132 internal links return 200, and the only exception is a 301 for `/blog`. |
| D2 | `/qpdf.wasm` 404 (Split, Rotate, Protect) | **FIXED** | Split, Rotate and Protect all produce valid output. `/qpdf.wasm` returns 200 (1.3 MB). |
| D3 | `/workers/*.worker.js` 404 (Merge) [request: per-tool chunks] | **FIXED** | `/workers/merge.worker.js` returns 200, and Merge outputs 5 pages. |
| D4 | `/assets/*` dynamic chunks 404 [request: per-tool chunks] | **FIXED** | No 404 for assets in the 132-page crawl. |
| D5 | `/config.json` 404 on every page [request: per-tool chunks] | **FIXED** | `/config.json` returns 200 (`{}`). |
| D6 | Language switcher gives root-level broken URLs [request: flexsearch] | **FIXED** | See 3f. The flexsearch check (3b) also shows no errors. |
| D7 | Service worker registration path wrong [request: PDF worker] | **FIXED** | See 3d. The PDF worker also loads (3c). |
| D8 | `/vi/` in English with `lang="en"` [request: service worker] | **FIXED** | See 3e. |
| D9 | Console noise, 404s, `addEventListener` of null [request: `/vi/` and switcher] | **FIXED** | 0 console errors in the 132-page crawl, and none on `/vi/` or the switcher paths. |

## New defects

None blocking.

Observations (low severity, probably upstream behavior):
- **O1:** The service worker registers only from the homepage bundle (`main-BWtDN6vv.js`, used by `/` and `/vi/`). Direct visits to `/merge-pdf` and `/compress-pdf` load a different main bundle with no registration code (0 registrations, no controller). The worker registers once the homepage is visited.
- **O2:** Protect PDF logs `error: this.program: -accessibility=n is ignored for modern encryption formats` and Unlock PDF logs `decryptPdf: Pdf.PDFError("Bad or missing /P entry")`. Both are console errors only, and both tools succeed. The `/P` message comes from the pypdf-made RC4 sample, which falls back to the owner-decrypt path.

Notes: `/blog` redirects with a 301 and I did not follow it. The tool runs used a fresh browser context each, and no tool needed a retry.
