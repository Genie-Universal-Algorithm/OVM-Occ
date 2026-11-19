"""Create web copies of the user-supplied media without changing source files."""
from pathlib import Path
import concurrent.futures, json, os, re, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont
SITE = Path(__file__).resolve().parents[1]
ROOT = SITE.parents[1]
SRC = ROOT / 'AI Day/高清剪辑素材'
FF = os.environ.get('FFMPEG') or shutil.which('ffmpeg') or str(ROOT/'visualization/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1')
TMP = SITE/'tools/.media-cache'
TMP.mkdir(exist_ok=True)
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'
font = ImageFont.truetype(FONT, 24)
scenes = [
 ('comparison-scannet','卧室 ScanNet_scene0000_00',['input.mp4','ground_truth.mov','Baseline.mov','Ours.mov'],['RGB input','Ground truth','LegoOcc','OVM-Occ (ours)'],2),
 ('comparison-replica','卧室 Replica_room1',['input.mp4','ground_truth.mov','Baseline.mov','Ours.mov'],['RGB input','Ground truth','LegoOcc','OVM-Occ (ours)'],2),
 ('tearoom','茶水间 3367531',['input.mov','local.mov','global.mov'],['RGB input','Local occupancy','Global map'],3),
 ('elevator','电梯厅 3338370',['input.mov','local.mov','global.mov'],['RGB input','Local occupancy','Global map'],3),
 ('office-e2','办公室E2',['input.mov','local.mov','global.mov'],['RGB input','Local occupancy','Global map'],3),
 ('living-room','客厅 scene0024_02',['input.mp4','local.mov','global.mov'],['RGB input','Local occupancy','Global map'],3),
 ('supermarket','超市 supermarket',['input.mp4','local.mov','global.mov'],['RGB input','Local occupancy','Global map'],3),
 ('office-e1','办公室E1',['input.mov','local.mov','global.mov'],['RGB input','Local occupancy','Global map'],3),
]
def run(args):
 p=subprocess.run([FF,'-hide_banner','-loglevel','error','-y',*args],capture_output=True,text=True)
 if p.returncode: raise RuntimeError(p.stderr)
def meta(path):
 s=subprocess.run([FF,'-hide_banner','-i',str(path)],capture_output=True,text=True).stderr
 h,m,sec=map(float,re.search(r'Duration: (\d+):(\d+):([\d.]+)',s).groups())
 fps=float(re.search(r'([\d.]+) fps',s).group(1))
 return h*3600+m*60+sec,fps

def encode(scene):
 key,folder,names,labels,cols=scene
 files=[SRC/folder/n for n in names]
 info=[meta(p) for p in files]; duration=min(i[0] for i in info); fps=info[0][1]
 cw,ch=(640,480) if cols==2 else (540,406)
 title_h=48;rows=(len(files)+cols-1)//cols;w=cols*cw;h=rows*(ch+title_h)
 plate=Image.new('RGB',(w,h),'white');d=ImageDraw.Draw(plate)
 for i,label in enumerate(labels):
  x=i%cols*cw;y=i//cols*(ch+title_h)
  d.text((x+24,y+13),label,font=font,fill='#087e74' if 'ours' in label else '#46575c')
  if i%cols: d.line((x,y,x,y+ch+title_h),fill='#e8eeee',width=2)
 plate_path=TMP/f'{key}-plate.png';plate.save(plate_path)
 out=SITE/'assets/videos'/f'{key}.mp4'
 if not out.exists():
  args=['-loop','1','-framerate',str(fps),'-i',str(plate_path)]
  for p in files: args+=['-threads','2','-i',str(p)]
  filters=[];prev='0:v'
  for i in range(len(files)):
   filters.append(f'[{i+1}:v]setpts=PTS-STARTPTS,scale={cw}:{ch}:force_original_aspect_ratio=decrease,setsar=1,format=rgba[v{i}]')
   x=i%cols*cw;y=i//cols*(ch+title_h)+title_h
   filters.append(f'[{prev}][v{i}]overlay=x={x}+({cw}-overlay_w)/2:y={y}+({ch}-overlay_h)/2:shortest=1[o{i}]')
   prev=f'o{i}'
  args+=['-filter_complex_threads','2','-filter_complex',';'.join(filters),'-map',f'[{prev}]','-t',str(duration),'-an','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-r',str(fps),'-threads','2','-movflags','+faststart',str(out)]
  run(args)
 poster=SITE/'assets/images'/f'{key}.jpg'
 run(['-ss',str(min(4,duration/3)),'-i',str(out),'-frames:v','1','-q:v','2',str(poster)])
 print(f'Prepared {key}: {duration:g}s, {out.stat().st_size/1e6:.1f} MB',flush=True)
 return {'id':key,'sources':[str(p.relative_to(ROOT)) for p in files],'duration':duration,'fps':fps,'width':w,'height':h,'bytes':out.stat().st_size,'processing':'Full source frames fitted without cropping; alpha composited on white; original playback rate; H.264 web copy.'}

with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
 report=list(pool.map(encode,scenes))
# Navigation already includes all eight labelled panels. Preserve its layout and text.
p=SRC/'具身导航 scene0420_01/composite.mov';out=SITE/'assets/videos/navigation.mp4'
duration,fps=meta(p)
if not out.exists():
 run(['-threads','2','-i',str(p),'-vf','scale=1920:-2','-an','-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-threads','2','-movflags','+faststart',str(out)])
run(['-ss','10','-i',str(out),'-frames:v','1','-q:v','2',str(SITE/'assets/images/navigation.jpg')])
report.append({'id':'navigation','sources':[str(p.relative_to(ROOT))],'duration':duration,'fps':fps,'bytes':out.stat().st_size,'processing':'Complete labelled composite, fitted to 1920px width; original playback rate; H.264.'})
# Hero uses corresponding RGB / prediction panels from a single observed frame.
run(['-ss','5','-i',str(SITE/'assets/videos/comparison-scannet.mp4'),'-frames:v','1',str(TMP/'hero-frame.png')])
im=Image.open(TMP/'hero-frame.png').convert('RGB')
hero=Image.new('RGB',(1280,480),'white')
hero.paste(im.crop((0,48,640,528)),(0,0));hero.paste(im.crop((640,576,1280,1056)),(640,0))
hero.save(SITE/'assets/images/hero.jpg',quality=94)
(SITE/'tools/media-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('Media complete',flush=True)
