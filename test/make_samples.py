from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw
for n,pages in (("a",3),("b",2)):
    c=canvas.Canvas(f"samples/sample-{n}.pdf")
    for i in range(pages):
        c.drawString(100,750,f"Sample {n.upper()} page {i+1}"); c.showPage()
    c.save()
im=Image.new("RGB",(400,300),(200,60,60)); ImageDraw.Draw(im).text((20,20),"sample jpg",fill="white"); im.save("samples/sample.jpg",quality=85)
