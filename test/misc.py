import json
from playwright.sync_api import sync_playwright

out = {}
ROOT = "https://ai4me.cfd"


def is_root_level(h):
    if h.startswith(ROOT + "/"):
        h = h[len(ROOT):]
    return h.startswith("/") and not h.startswith("//") and not (h == "/pdf" or h.startswith("/pdf/"))


with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/local/bin/google-chrome", args=["--no-sandbox"])
    pg = b.new_context().new_page()
    cons = []
    fails = []
    pg.on("console", lambda m: cons.append(m.type + ": " + m.text[:250]) if m.type in ("error", "warning") else None)
    pg.on("pageerror", lambda e: cons.append("pageerror: " + str(e)[:250]))
    pg.on("response", lambda r: fails.append(f"{r.status} {r.url}") if r.status >= 400 else None)

    r = pg.goto(ROOT + "/pdf/vi/", wait_until="load")
    pg.wait_for_timeout(3000)
    hrefs = pg.eval_on_selector_all("a[href]", "e=>e.map(a=>a.getAttribute('href'))")
    out["vi"] = {
        "status": r.status, "url": pg.url, "title": pg.title(),
        "lang": pg.eval_on_selector("html", "e=>e.lang"),
        "h1": pg.inner_text("h1")[:120],
        "console": list(cons), "fails": list(fails),
        "n_links": len(hrefs),
        "root_level_hrefs_dom": sorted({h for h in hrefs if is_root_level(h)})[:40],
    }
    cons.clear(); fails.clear()

    pg.goto(ROOT + "/pdf/", wait_until="load")
    pg.wait_for_timeout(3000)
    try:
        pg.locator("button:has-text('English')").first.click(timeout=3000)
        pg.wait_for_timeout(500)
        with pg.expect_navigation(timeout=15000):
            pg.locator("button:visible:has-text('Tiếng Việt')").first.click()
        pg.wait_for_timeout(2000)
    except Exception as e:
        out["switch_error"] = str(e)[:200]
    out["switch_result_url"] = pg.url

    out["lang_links"] = {}
    for path in ["/pdf/", "/pdf/merge-pdf", "/pdf/vi/", "/pdf/vi/merge-pdf"]:
        rr = pg.goto(ROOT + path, wait_until="load")
        pg.wait_for_timeout(2000)
        out["lang_links"][path] = {
            "status": rr.status,
            "hreflang": pg.eval_on_selector_all("link[hreflang],a[hreflang]", "e=>e.map(x=>x.getAttribute('hreflang')+' '+(x.href))"),
            "canonical": pg.eval_on_selector_all("link[rel=canonical]", "e=>e.map(x=>x.href)"),
            "root_level_links_dom": sorted({h for h in pg.eval_on_selector_all("a[href]", "e=>e.map(a=>a.getAttribute('href'))") if is_root_level(h)})[:15],
            "n_root_level_links_dom": len([h for h in pg.eval_on_selector_all("a[href]", "e=>e.map(a=>a.getAttribute('href'))") if is_root_level(h)]),
        }

    cons.clear(); fails.clear()
    pg.goto(ROOT + "/pdf/", wait_until="load")
    pg.wait_for_timeout(5000)
    out["sw"] = pg.evaluate("""async()=>{if(!('serviceWorker' in navigator))return {supported:false};
      const rs=await navigator.serviceWorker.getRegistrations();
      return {supported:true,regs:rs.map(r=>({scope:r.scope,script:(r.active||r.installing||r.waiting||{}).scriptURL,state:(r.active||r.installing||r.waiting||{}).state}))}}""")
    out["sw"]["console"] = list(cons)
    out["sw"]["fails"] = list(fails)
    b.close()

json.dump(out, open("test/misc.json", "w"), indent=1, ensure_ascii=False)
