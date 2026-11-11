import os
from playwright.sync_api import sync_playwright
S=os.path.abspath("samples")
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/local/bin/google-chrome",args=["--no-sandbox"])
    pg=b.new_context(accept_downloads=True).new_page(); rq=[]
    pg.on("response",lambda r:rq.append((r.status,r.url)) if any(k in r.url.lower() for k in("worker","wasm","pdfjs","pdf.")) else None)
    pg.goto("https://ai4me.cfd/pdf-to-jpg",wait_until="load"); pg.wait_for_timeout(1500)
    pg.set_input_files("#file-input",S+"/sample-a.pdf"); pg.wait_for_timeout(4000)
    for r in rq: print(r)
    b.close()
