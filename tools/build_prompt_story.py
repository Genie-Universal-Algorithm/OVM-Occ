"""Recompose the recorded prompt demo as an annotated RGB/occupancy comparison."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess, json, numpy as np
SITE=Path(__file__).resolve().parents[1];ROOT=SITE.parents[1]
FF=str(ROOT/'visualization/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1')
SOURCE=ROOT/'AI Day/最终MOV汇总/开集.webm'
CACHE=SITE/'tools/.media-cache/prompt-story';CACHE.mkdir(exist_ok=True)
OUT=SITE/'assets/videos/open-vocabulary-prompt-story.mp4'
W,H=1920,960;PW,PH=872,548;FPS=30
INK='#172b2d';MUTED='#657577';LINE='#dce4e3';TEAL='#087e74';SOFT='#f4f6f6'
COLORS={'Object':'#df6348','Laptop':'#dcc846','Plant':'#cc1cce','Trash can':'#7d8580'}
FONT='/System/Library/Fonts/Supplemental/Arial.ttf';BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
def font(size,bold=False):return ImageFont.truetype(BOLD if bold else FONT,size)
F={size:font(size) for size in [20,22,24,26,28,30,34]};B={size:font(size,True) for size in [22,24,26,28,30,34]}

def make_base(stage):
 im=Image.new('RGB',(W,H),'white');d=ImageDraw.Draw(im)
 d.text((64,28),'OVM-Occ',font=B[30],fill=TEAL)
 d.text((258,30),'Open-vocabulary Occupancy',font=F[28],fill=INK)
 text='Text prompts → 3D semantic labels';d.text((1856-d.textlength(text,font=F[22]),34),text,font=F[22],fill=MUTED)
 labels=['Generic “Object” category','Add text prompts','Recognize new categories']
 for j,label in enumerate(labels):
  x=64+j*604;active=j==stage
  d.rounded_rectangle((x,90,x+584,152),radius=12,fill='#eaf5f2' if active else SOFT,outline=TEAL if active else LINE,width=2 if active else 1)
  d.text((x+24,106),label,font=B[28],fill=TEAL if active else MUTED)
 for x,label in [(64,'RGB Input'),(984,'Semantic Occupancy')]:
  d.text((x,174),label,font=B[28],fill=INK)
  d.rounded_rectangle((x-1,215,x+PW+1,216+PH+1),radius=8,outline=LINE,width=1)
 d.rounded_rectangle((64,788,1856,886),radius=12,fill=SOFT,outline=LINE)
 d.text((88,824),'TEXT PROMPTS',font=B[22],fill=MUTED)
 return im
BASES=[make_base(i) for i in range(3)]
# Positions are normalized to the reference video's 800x500 panel crops.
RGB_BOXES=[(262,229,130,114),(307,310,156,145),(509,387,112,111)]
OCC_BOXES=[(280,230,124,111),(292,310,156,139),(513,389,112,110)]
NAMES=['Plant','Laptop','Trash can']
LABELS=[(1090,416),(1060,642),(1630,614)]

def box_at(box,x):
 a,b,w,h=box
 return (int(x+a*PW/800),int(216+b*PH/500),int(x+(a+w)*PW/800),min(763,int(216+(b+h)*PH/500)))

def annotate(im,t,updated):
 d=ImageDraw.Draw(im)
 for j,name in enumerate(NAMES):
  color=COLORS[name] if updated else COLORS['Object']
  rgb=box_at(RGB_BOXES[j],64);occ=box_at(OCC_BOXES[j],984)
  for rect in [rgb,occ]:
   d.rounded_rectangle(rect,radius=5,outline='white',width=6)
   d.rounded_rectangle(rect,radius=5,outline=color,width=3)
  label=name if updated else 'Object';lx,ly=LABELS[j]
  lw=int(d.textlength(label,font=B[24]))+48;lh=42
  endpoint=(occ[0],(occ[1]+occ[3])//2) if j<2 else (occ[2],(occ[1]+occ[3])//2)
  start=(lx+lw,ly+lh//2) if j<2 else (lx,ly+lh//2)
  d.line((start,endpoint),fill='white',width=6);d.line((start,endpoint),fill=color,width=3)
  d.rounded_rectangle((lx,ly,lx+lw,ly+lh),radius=6,fill='white',outline=color,width=2)
  d.rectangle((lx+10,ly+15,lx+21,ly+26),fill=color)
  d.text((lx+29,ly+7),label,font=B[24],fill=INK)
 if t<6:
  d.text((304,822),'Laptop, plant and trash can share the generic “Object” label.',font=F[28],fill=MUTED)
 else:
  entries=[('Laptop','laptop',304,220,6),('Plant','plant',548,202,9),('Trash can','trash can',774,260,12)]
  for name,label,x,width,appear in entries:
   if t<appear:continue
   color=COLORS[name]
   d.rounded_rectangle((x,806,x+width,868),radius=9,fill='white',outline=color,width=2)
   d.rounded_rectangle((x+18,826,x+34,842),radius=3,fill=color)
   d.text((x+48,820),'“'+label+'”',font=B[28],fill=INK)
  status='New categories recognized' if updated else 'Adding to the vocabulary…'
  d.text((1830-d.textlength(status,font=F[24]),826),status,font=F[24],fill=TEAL if updated else MUTED)
 caption='Same scene · Updated text vocabulary · New semantic labels' if updated else 'Text prompts specify which semantic categories to recognize.'
 d.text(((W-d.textlength(caption,font=F[24]))/2,914),caption,font=F[24],fill=MUTED)
 return im

filters=f'[0:v]fps={FPS},split[a][b];[a]crop=914:574:72:255,scale={PW}:{PH}[rgb];[b]crop=914:574:988:255,scale={PW}:{PH}[occ];[rgb][occ]hstack=inputs=2[v]'
with (CACHE/'decode.log').open('wb') as de, (CACHE/'encode.log').open('wb') as en:
 decoder=subprocess.Popen([FF,'-hide_banner','-v','error','-i',str(SOURCE),'-filter_complex_threads','2','-filter_complex',filters,'-map','[v]','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE,stderr=de)
 encoder=subprocess.Popen([FF,'-hide_banner','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-an','-c:v','libx264','-crf','18','-preset','fast','-threads','2','-pix_fmt','yuv420p','-movflags','+faststart',str(OUT)],stdin=subprocess.PIPE,stderr=en)
 size=PW*2*PH*3;count=0;first_update=None
 try:
  while True:
   raw=decoder.stdout.read(size)
   if not raw:break
   assert len(raw)==size
   pair=Image.frombytes('RGB',(PW*2,PH),raw)
   occ=np.asarray(pair)[:,PW:,:]
   purple=int(((occ[:,:,0]>120)&(occ[:,:,1]<100)&(occ[:,:,2]>110)).sum())
   updated=purple>3000
   if updated and first_update is None:first_update=count/FPS
   t=count/FPS;stage=2 if updated else (1 if t>=6 else 0)
   canvas=BASES[stage].copy();canvas.paste(pair.crop((0,0,PW,PH)),(64,216));canvas.paste(pair.crop((PW,0,PW*2,PH)),(984,216))
   canvas=annotate(canvas,t,updated)
   encoder.stdin.write(canvas.tobytes())
   if count in [0,240,420,600,720]:canvas.save(CACHE/f'preview-{count//FPS}.png')
   count+=1
 finally:
  decoder.stdout.close();encoder.stdin.close()
 assert decoder.wait()==0 and encoder.wait()==0
subprocess.run([FF,'-hide_banner','-v','error','-y','-ss','20','-i',str(OUT),'-frames:v','1','-q:v','2',str(SITE/'assets/images/open-vocabulary-prompt-story.jpg')],check=True)
subprocess.run([FF,'-hide_banner','-v','error','-i',str(OUT),'-f','null','-'],check=True)
report={'source':str(SOURCE.relative_to(ROOT)),'reference':'AI Day/GenieOcc.mp4','output':str(OUT.relative_to(SITE)),'frames':count,'fps':FPS,'duration':count/FPS,'first_updated_semantics_seconds':first_update,'processing':'Original RGB and semantic occupancy panels with synchronized explanatory boxes and text prompts. Source semantic predictions are unchanged. UI chrome and global scene memory omitted. White layout.','full_decode':'pass'}
(SITE/'tools/prompt-story-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
