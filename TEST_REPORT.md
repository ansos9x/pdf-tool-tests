# Functional test report: https://ai4me.cfd/pdf/

Date: 2026-11-11. Browser: Chrome for Testing 157 (headless, Playwright). Scripts are in `test/`, raw data in `test/*.json`, `test/*.tsv` and `test/link_status.txt`. Downloaded outputs and screenshots are in `outputs/`.

**Summary:** Compress, PDF to JPG, JPG to PDF and Unlock PASS. Merge, Split, Rotate and Protect FAIL. The failures share two root causes: assets requested at the domain root (`/workers/...`, `/qpdf.wasm`, `/config.json`, `/sw.js`, `/assets/...`) instead of `/pdf/...`, and rewritten language and tool links that point at the root (`/vi/pdf/`, `/xxx.html`). The service worker never registers.

## Results

| # | Item | Result | Evidence |
|---|------|--------|----------|
| 1a | Homepage loads | PASS | `/pdf/` returns 200. |
| 1b | Homepage tool links (rendered DOM) | **FAIL** | Raw HTML uses `/pdf/compress-pdf`, but after JS runs the DOM has 130 links of the form `/compress-pdf.html`. These resolve to `https://ai4me.cfd/compress-pdf.html`, which returns 404 (118 of 118 root `.html` URLs tested). |
| 1c | Tool pages at `/pdf/<tool>` | PASS | 118 tool pages plus `/pdf/vi/` return 200 (119 pages crawled, none non-200). |
| 1d | Asset requests inside `/pdf` | PASS (346 OK) | 346 unique asset URLs under `/pdf/` returned 200. |
| 1e | Assets outside `/pdf` or 404 | **FAIL** | 43 URLs, see defects D3-D5 and `test/asset_defects.tsv`. |
| 2 | Samples generated | PASS | `samples/sample-a.pdf` (3 pages), `sample-b.pdf` (2 pages), `sample.jpg` (400x300), plus `sample-a-locked.pdf` (RC4-128, password `secret123`, made with pypdf for the Unlock test). |
| 3a | Merge PDF (a+b, expect 5 pages) | **FAIL** | No output. `404 https://ai4me.cfd/workers/merge.worker.js`. No download appeared within 60 s of clicking Merge. |
| 3b | Split PDF (range 1-2) | **FAIL** | Page shows "Initialization Error: Could not load the PDF engine". `404 https://ai4me.cfd/qpdf.wasm`. The Split button never became clickable (two runs, same result). |
| 3c | Compress PDF | PASS | Downloaded `compress-0-sample-a.pdf`: 1316 B (input 2265 B, UI says saved 41.9%), 3 pages, PDF 1.5, not encrypted (`pdfinfo`). |
| 3d | Rotate PDF (all right) | **FAIL** | Same "Initialization Error" as Split. `404 https://ai4me.cfd/qpdf.wasm`. The rotate controls were not clickable (two runs, same result). |
| 3e | PDF to JPG | PASS | `sample-a_jpgs.zip` holds 3 JPEGs (`file`: JFIF baseline, 1190x1683, about 15 KB each), one per page. |
| 3f | JPG to PDF | PASS | `from_jpgs.pdf`: 3015 B, 1 page, 300x225 pt, PDF 1.7. |
| 3g | Protect PDF | **FAIL** | UI alert "Encryption Failed: Aborted(both async and sync fetching of the wasm failed)". `404 https://ai4me.cfd/qpdf.wasm`. No file produced. |
| 3h | Unlock PDF (locked sample, correct password) | PASS | Output `unlock-0-sample-a-locked.pdf`: 1585 B, 3 pages, `Encrypted: no`. The input reported "Incorrect password" in `pdfinfo` without the password, so it was genuinely encrypted. |
| 4a | `/pdf/vi/` loads | PASS with defect | Status 200, title is Vietnamese, but `<html lang="en">` and the H1 is English ("The PDF Toolkit built for privacy."). The page is not localized (D8). |
| 4b | Language switcher gives no root-level links | **FAIL** | Selecting "Tiếng Việt" on `/pdf/` navigates to `https://ai4me.cfd/vi/pdf/`. On `/pdf/merge-pdf` it goes to `https://ai4me.cfd/vi/pdf/merge-pdf`. Both are outside `/pdf/` (the correct target is `/pdf/vi/`). `/pdf/vi/` itself has 130 root-level `/xxx.html` tool links. |
| 4c | Service worker registers without console errors | **FAIL** | `Failed to register a ServiceWorker for scope ('https://ai4me.cfd/') with script ('https://ai4me.cfd/sw.js'): A bad HTTP response code (404)`. `getRegistrations()` returns `[]` on `/pdf/`, `/pdf/merge-pdf` and `/pdf/vi/` (`test/sw_switch.json`). `/pdf/sw.js` exists (200); only the registration URL is wrong. |

BLOCKED: none. Every tool could be driven in the headless browser. Where a tool failed, the failure came from the app, with the evidence shown above.

## Defects

| ID | Severity | Defect | Exact URL / error |
|----|----------|--------|-------------------|
| D1 | High | Tool links rewritten to root `.html` URLs at runtime (404). The raw HTML is correct. | `https://ai4me.cfd/compress-pdf.html` and 117 others (`test/link_status.txt`), e.g. `/merge-pdf.html`, `/pdf-to-jpg.html`. |
| D2 | High | qpdf WASM requested from the root. Breaks Split, Rotate and Protect. | `https://ai4me.cfd/qpdf.wasm` (404). Console: `wasm streaming compile failed ... HTTP status code is not ok`. |
| D3 | High | Worker scripts requested from the root. Breaks Merge. | `https://ai4me.cfd/workers/merge.worker.js` (404). Also `add-attachments`, `edit-attachments`, `extract-attachments`, `json-to-pdf`, `pdf-to-json` and `table-of-contents` `.worker.js` (all 404, one page each, with console `Worker error: Event`). |
| D4 | Medium | Dynamic-import chunks requested from `/assets/` at the root (404 or aborted). | `/assets/mermaid.core-CFQwT28n.js`, `/assets/katex-*.js`, `/assets/chunk-*.js` and about 30 more (on `/pdf/markdown-to-pdf`). `/assets/flowDiagram-IUGLLWBU-DbPL_92y.js` and `/pdf/assets/flowDiagram-IUGLLWBU-DbPL_92y.js` (both aborted) on `/pdf/merge-pdf`. Full list: `test/asset_defects.tsv`. |
| D5 | Medium | App config requested from the root, on every page (119 of 119). | `https://ai4me.cfd/config.json` (404). |
| D6 | High | Language switcher produces root-level URLs. | `https://ai4me.cfd/vi/pdf/`, `https://ai4me.cfd/vi/pdf/merge-pdf` (404 on WordPress). |
| D7 | Medium | Service worker registration path is wrong. | `https://ai4me.cfd/sw.js` (404), scope `/`. The real file is `https://ai4me.cfd/pdf/sw.js`, so the scope should be `/pdf/`. |
| D8 | Low | `/pdf/vi/` shows English content with `lang="en"`. Canonical and hreflang point to `https://www.bentopdf.com/...`, not this site. | `https://ai4me.cfd/pdf/vi/` |
| D9 | Low | Console noise: 146 "Failed to load resource ... 404" errors across the crawl, plus a pageerror `Cannot read properties of null (reading 'addEventListener')` seen after the redirect to `/vi/pdf/`. | crawl of 119 pages (`test/crawl2.json`) |

## Notes
- The only third-party request is `https://api.github.com/repos/alam00000/bentopdf` (200).
- `/pdf/` never reaches `networkidle`, so the crawl used `load` plus a short wait.
- `qpdf.wasm` and the PDF.js workers load only when a tool runs, so `qpdf.wasm` shows up from the tool runs rather than the crawl. Other lazily loaded assets on tool pages I did not run may also be affected.
- Each tool ran in a fresh browser context. Split and Rotate were attempted twice with the same result.
- Compress, PDF to JPG, JPG to PDF and Unlock do not depend on qpdf or the root-level workers, and they work.
