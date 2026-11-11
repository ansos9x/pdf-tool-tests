from pypdf import PdfReader,PdfWriter
w=PdfWriter(); [w.add_page(p) for p in PdfReader("samples/sample-a.pdf").pages]
try: w.encrypt("secret123",algorithm="RC4-128")
except Exception as e: print(e)
w.write("samples/sample-a-locked.pdf")
