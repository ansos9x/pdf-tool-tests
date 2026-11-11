import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/local/bin/google-chrome",args=["--no-sandbox"])
    pg=b.new_context().new_page()
    for t in sys.argv[1:]:
        pg.goto("https://ai4me.cfd/pdf/"+t,wait_until="load"); pg.wait_for_timeout(2000)
        print("==",t,pg.title())
        print(pg.eval_on_selector_all("input,button,select","e=>e.map(x=>x.tagName+'#'+x.id+'['+(x.type||'')+']'+(x.textContent||'').trim().slice(0,25)).filter(s=>!/^BUTTON#\\[/.test(s)||true)").__str__()[:1500])
    b.close()
