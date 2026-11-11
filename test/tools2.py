import json,sys,os,time
from playwright.sync_api import sync_playwright
S=os.path.abspath("samples"); O=os.path.abspath("outputs2")
A,Bp,J=f"{S}/sample-a.pdf",f"{S}/sample-b.pdf",f"{S}/sample.jpg"
def run(name,path,files,pre=None,out=None):
    res={"tool":name,"url":"https://ai4me.cfd/"+path,"console":[],"failed":[],"saved":[]}
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path="/usr/local/bin/google-chrome",args=["--no-sandbox"])
        ctx=b.new_context(accept_downloads=True); pg=ctx.new_page()
        pg.on("console",lambda m:res["console"].append(m.type+": "+m.text[:250]) if m.type=="error" else None)
        pg.on("pageerror",lambda e:res["console"].append("pageerror: "+str(e)[:250]))
        pg.on("response",lambda r:res["failed"].append(f"{r.status} {r.url}") if r.status>=400 else None)
        pg.on("requestfailed",lambda r:res["failed"].append(f"FAILED {r.url}"))
        dls=[]; pg.on("download",lambda d:dls.append(d))
        try:
            pg.goto(res["url"],wait_until="load"); pg.wait_for_timeout(1500)
            pg.set_input_files("#file-input",files); pg.wait_for_timeout(2500)
            if pre: pre(pg)
            pg.click("#process-btn",timeout=15000)
            for _ in range(60):
                if dls: break
                pg.wait_for_timeout(1000)
            # some tools show a download button after processing
            if not dls:
                res["note"]="no auto download; visible buttons: "+str(pg.eval_on_selector_all("button:visible,a:visible","e=>e.map(x=>(x.id||'')+':'+x.textContent.trim().slice(0,30)).filter(s=>/download|save/i.test(s))"))
                for sel in ["#download-btn","button:has-text('Download')","a:has-text('Download')"]:
                    try:
                        with pg.expect_download(timeout=15000) as di: pg.click(sel,timeout=3000)
                        dls.append(di.value); break
                    except Exception: pass
            for i,d in enumerate(dls):
                f=f"{O}/{out or name}-{i}-{d.suggested_filename}"; d.save_as(f); res["saved"].append(f)
            res["body"]=pg.inner_text("body")[:0]
            res["alert"]=pg.evaluate("(()=>{const m=document.querySelector('#alert-modal,#alert-message,#alert-title');return m?m.innerText:''})()")
            pg.screenshot(path=f"{O}/{name}.png")
        except Exception as e:
            res["error"]=str(e)[:300]; pg.screenshot(path=f"{O}/{name}.png")
        b.close()
    json.dump(res,open(f"{O}/{name}.json","w"),indent=1); print(name,res.get("error"),res["saved"],res.get("note"),res["alert"][:100] if res.get("alert") else "")
    return res
which=sys.argv[1:]
T={
 "merge":lambda:run("merge","merge-pdf",[A,Bp]),
 "split":lambda:run("split","split-pdf",A,pre=lambda pg:pg.fill("#page-range","1-2")),
 "compress":lambda:run("compress","compress-pdf",A),
 "rotate":lambda:run("rotate","rotate-pdf",A,pre=lambda pg:pg.click("#rotate-all-right")),
 "pdf2jpg":lambda:run("pdf2jpg","pdf-to-jpg",A),
 "jpg2pdf":lambda:run("jpg2pdf","jpg-to-pdf",J),
  "unlock":lambda:run("unlock","unlock-pdf",f"{S}/sample-a-locked.pdf",pre=lambda pg:pg.fill("#password-input","secret123")),
 "protect":lambda:run("protect","protect-pdf",A,pre=lambda pg:(pg.fill("#user-password-input","secret123"),pg.fill("#owner-password-input","secret123"))),
}
for k in (which or T): T[k]()
