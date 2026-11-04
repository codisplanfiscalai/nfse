from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

BASE=Path(__file__).resolve().parent
S=1024
img=Image.new('RGBA',(S,S),(0,0,0,0))
d=ImageDraw.Draw(img)
# Soft gradient, independent identity from the Escritura teal brand.
mask=Image.new('L',(S,S),0);md=ImageDraw.Draw(mask);md.rounded_rectangle((30,30,S-30,S-30),radius=220,fill=255)
background=Image.new('RGBA',(S,S));pix=background.load()
for y in range(S):
 for x in range(S):
  t=(x+y)/(2*(S-1));pix[x,y]=(int(36+(105-36)*t),int(41+(87-41)*t),int(104+(246-104)*t),255)
img.paste(background,(0,0),mask)
d=ImageDraw.Draw(img)
# Clear invoice-inspired N with an independent rising turquoise path.
for points,color,width in [([(250,738),(250,294),(519,580),(519,294),(776,294),(776,738)],(253,254,255),96),
                           ([(250,738),(519,449),(776,738)],(55,215,195),68)]:
 d.line(points,fill=color,width=width,joint='curve')
 for x,y in [points[0],points[-1]]:d.ellipse((x-width//2,y-width//2,x+width//2,y+width//2),fill=color)
d.ellipse((683,198,867,382),fill=(255,180,107,255))
d.ellipse((713,228,837,352),fill=(255,190,124,255))
img.save(BASE/'app.png',optimize=True)
img.save(BASE/'app.ico',format='ICO',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
# Standalone lockup works on login screen without legacy logo.
W,H=900,225
canvas=Image.new('RGBA',(W,H),(0,0,0,0));mark=img.resize((165,165),Image.Resampling.LANCZOS);canvas.alpha_composite(mark,(17,29))
d=ImageDraw.Draw(canvas)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
normal='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
d.text((211,32),'NFS-e',fill=(34,37,78),font=ImageFont.truetype(font,97))
d.text((217,146),'CODISPLAN  /  GESTÃO FISCAL',fill=(93,94,145),font=ImageFont.truetype(normal,26))
canvas.save(BASE/'brand-lockup.png',optimize=True)
