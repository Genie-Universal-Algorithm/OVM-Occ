"""Compose the original PDF pipelines without rasterizing their vector text and lines."""
from pathlib import Path
from io import BytesIO
from pypdf import PdfReader, PdfWriter, Transformation
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
SITE=Path(__file__).resolve().parents[1]
pages=[PdfReader(SITE.parent/'材料'/n).pages[0] for n in ['TeacherConstuct.pdf','StudentModel.pdf']]
panel_h=560
widths=[float(p.mediabox.width)/float(p.mediabox.height)*panel_h for p in pages]
margin=40;gap=240;bottom=96;top=30
W=sum(widths)+2*margin+gap;H=bottom+panel_h+top
font_path=Path('/System/Library/Fonts/Supplemental/Arial Bold.ttf')
pdfmetrics.registerFont(TTFont('OverviewBold',str(font_path)))
pdfmetrics.registerFont(TTFont('OverviewRegular','/System/Library/Fonts/Supplemental/Arial.ttf'))
buffer=BytesIO();c=canvas.Canvas(buffer,pagesize=(W,H))
c.setTitle('OVM-Occ Teacher Construction and Student Model')
c.setFillColorRGB(1,1,1);c.rect(0,0,W,H,stroke=0,fill=1)
centers=[margin+widths[0]/2,margin+widths[0]+gap+widths[1]/2]
c.setFillColorRGB(.08,.13,.15);c.setFont('OverviewBold',34)
for x,t in zip(centers,['(a) Teacher Construction','(b) Student Model']):c.drawCentredString(x,39,t)
x1=margin+widths[0]+12;x2=x1+gap-24;y=bottom+panel_h/2
c.setFont('OverviewBold',29);c.drawCentredString((x1+x2)/2,y+24,'Distillation')
c.setStrokeColorRGB(.20,.61,.82);c.setLineWidth(5);c.line(x1,y,x2-9,y)
path=c.beginPath();path.moveTo(x2-21,y+11);path.lineTo(x2,y);path.lineTo(x2-21,y-11)
c.drawPath(path,stroke=1)
c.save()
combined=PdfReader(buffer).pages[0]
for p,x in zip(pages,[margin,margin+widths[0]+gap]):
 scale=panel_h/float(p.mediabox.height)
 combined.merge_transformed_page(p,Transformation().scale(scale).translate(x,bottom))
writer=PdfWriter();writer.add_page(combined)
writer.add_metadata({'/Title':'OVM-Occ Teacher Construction and Student Model'})
with (SITE/'assets/images/teacher-student-overview-hq.pdf').open('wb') as f:writer.write(f)
print(f'Composed vector PDF: {W:.1f} × {H:.1f} pt')
