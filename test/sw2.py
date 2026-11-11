import json
from playwright.sync_api import sync_playwright
B="https://ai4me.cfd"; out={}
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/local/bin/google-chrome",args=["--no-sandbox"])
    for path in ["/","/vi/","/merge-pdf","/compress-pdf"]:
        pg=b.new_context().new_page(); logs=[]
        pg.on("console",lambda m:logs.append(m.type+": "+m.text[:200]) if ("SW" in m.text or m.type=="error") else None)
        pg.on("pageerror",lambda e:logs.append("pageerror "+str(e)[:200]))
        pg.goto(B+path,wait_until="load"); pg.wait_for_timeout(8000)
        regs=pg.evaluate("""async()=>{const rs=await navigator.serviceWorker.getRegistrations();return rs.map(r=>({scope:r.scope,script:(r.active||r.installing||r.waiting||{}).scriptURL,state:(r.active||r.installing||r.waiting||{}).state}))}""")
        c1=pg.evaluate("!!navigator.serviceWorker.controller")
        pg.reload(wait_until="load"); pg.wait_for_timeout(4000)
        c2=pg.evaluate("!!navigator.serviceWorker.controller")
        scripts=pg.eval_on_selector_all("script[src]","e=>e.map(s=>s.src.split('/').pop())")
        out[path]={"regs":regs,"controller_first":c1,"controller_after_reload":c2,"logs":logs,"scripts":scripts}
    b.close()
json.dump(out,open("test/sw2.json","w"),indent=1)
print(json.dumps(out,indent=1))
