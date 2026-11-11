import json
from playwright.sync_api import sync_playwright

out = {}
with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/local/bin/google-chrome", args=["--no-sandbox"])
    for name, url in [("home", "https://ai4me.cfd/pdf/"), ("merge", "https://ai4me.cfd/pdf/merge-pdf"), ("vi", "https://ai4me.cfd/pdf/vi/")]:
        pg = b.new_context().new_page()
        cons, fails = [], []
        pg.on("console", lambda m: cons.append(m.type + ": " + m.text[:300]) if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: cons.append("pageerror: " + str(e)[:300]))
        pg.on("response", lambda r: fails.append(f"{r.status} {r.url}") if r.status >= 400 else None)
        pg.goto(url, wait_until="load")
        pg.wait_for_timeout(5000)
        regs = pg.evaluate("""async()=>{const rs=await navigator.serviceWorker.getRegistrations();return rs.map(r=>({scope:r.scope,script:(r.active||r.installing||r.waiting||{}).scriptURL,state:(r.active||r.installing||r.waiting||{}).state}))}""")
        out[name] = {"final_url": pg.url, "regs": regs, "console": cons, "fails": fails}
    # switcher on a fresh context, multiple pages
    for path in ["/pdf/", "/pdf/merge-pdf"]:
        pg = b.new_context().new_page()
        pg.goto("https://ai4me.cfd" + path, wait_until="load")
        pg.wait_for_timeout(2000)
        try:
            pg.locator("button:has-text('English')").first.click(timeout=3000)
            pg.wait_for_timeout(500)
            with pg.expect_navigation(timeout=15000):
                pg.locator("button:visible:has-text('Tiếng Việt')").first.click()
            pg.wait_for_timeout(1500)
        except Exception as e:
            out.setdefault("switch_err", {})[path] = str(e)[:150]
        out.setdefault("switch", {})[path] = pg.url
    b.close()
json.dump(out, open("test/sw_switch.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
