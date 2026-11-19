"""Reduce internal whitespace around occupancy renders without clipping geometry."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import subprocess,json,math
SITE=Path(__file__).resolve().parents[1];ROOT=SITE.parents[1]
CACHE=SITE/'tools/.media-cache/tight-occupancy';CACHE.mkdir(exist_ok=True)
FF=str(ROOT/'visualization/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1')
BOUNDS=json.loads((SITE/'tools/.media-cache/occupancy-tight-bounds.json').read_text())
def run(args):subprocess.run([FF,'-hide_banner','-v','error','-y',*args],check=True)
def union(boxes):
 boxes=[b for b in boxes if b]
 return [min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]
def crop(im,b):
 w,h=im.size
 # Padding and rounding preserve every occupied pixel, including alpha edges.
 left=max(0,math.floor((b[0]-7)/720*w));top=max(0,math.floor((b[1]-7)/540*h))
 right=min(w,math.ceil((b[2]+7)/720*w));bottom=min(h,math.ceil((b[3]+7)/540*h))
 return im.crop((left,top,right,bottom))
reports=[]
for key,folder,names,labels,cw,ch,title,font_size in [
 ('scannet','卧室 ScanNet_scene0000_00',['input.mp4','ground_truth.mov','Baseline.mov','Ours.mov'],['RGB input','Ground truth','Previous SOTA','OVM-Occ (ours)'],640,500,54,27),
 ('living','客厅 scene0024_02',['input.mp4','local.mov','global.mov'],['RGB input','Local occupancy','Global map'],540,520,48,24)]:
 scene=CACHE/key;scene.mkdir(exist_ok=True)
 for j,name in enumerate(names):
  d=scene/f'source-{j}';d.mkdir(exist_ok=True)
  run(['-threads','2','-i',str(ROOT/'AI Day/高清剪辑素材'/folder/name),'-vf','scale=1440:-1,format=rgba',str(d/'%03d.png')])
  assert len(list(d.glob('*.png')))==30
 crops=[]
 for i in range(30):
  if key=='scannet':
   # All methods share one crop at each timestep; include neighbouring frames
   # so movement at the boundary remains visible.
   b=union([BOUNDS[key][name][k] for name in names[1:] for k in range(max(0,i-1),min(30,i+2))])
   crops.append([None,b,b,b])
  else:
   crops.append([None,*[union(BOUNDS[key][name]) for name in names[1:]]])
 font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',font_size)
 frames=scene/'output';frames.mkdir(exist_ok=True)
 for i in range(30):
  canvas=Image.new('RGB',(cw*len(names),ch+title),'white');draw=ImageDraw.Draw(canvas)
  for j,label in enumerate(labels):
   draw.text((j*cw+23,13),label,font=font,fill='#087e74' if 'ours' in label else '#46575c')
   if j:draw.line((j*cw,0,j*cw,ch+title),fill='#e1e7e4',width=2)
   im=Image.open(scene/f'source-{j}/{i+1:03d}.png').convert('RGBA')
   if crops[i][j]:im=crop(im,crops[i][j])
   limit_h=(480 if key=='scannet' else 406) if j==0 else ch
   im=ImageOps.contain(im,(cw-4 if j else cw,limit_h),Image.Resampling.LANCZOS)
   canvas.paste(im,(j*cw+(cw-im.width)//2,title+(ch-im.height)//2),im)
  canvas.save(frames/f'{i+1:03d}.png')
 basename='comparison-scannet-tight' if key=='scannet' else 'living-room-tight'
 out=SITE/f'assets/videos/{basename}.mp4'
 run(['-framerate','2','-i',str(frames/'%03d.png'),'-an','-c:v','libx264','-crf','18','-preset','fast','-threads','2','-pix_fmt','yuv420p','-movflags','+faststart',str(out)])
 run(['-ss','4','-i',str(out),'-frames:v','1','-q:v','2',str(SITE/f'assets/images/{basename}.jpg')])
 run(['-i',str(out),'-f','null','-'])
 reports.append({'scene':key,'output':str(out.relative_to(SITE)),'duration':15,'fps':2,'frames':30,'normalized_crops_per_frame':crops,'full_decode':'pass'})
 print(f'{key}: 30 frames, 15s, 2fps, full decode passed.',flush=True)
(SITE/'tools/tight-occupancy-manifest.json').write_text(json.dumps(reports,indent=2)+'\n')
