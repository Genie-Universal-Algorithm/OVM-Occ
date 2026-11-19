"""Four-column comparisons with one fixed foreground crop shared by GT/baseline/ours."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,re,json,math
from PIL import Image,ImageDraw,ImageFont
SITE=Path(__file__).resolve().parents[1];ROOT=SITE.parents[1]
FF=str(ROOT/'visualization/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1')
CACHE=SITE/'tools/.media-cache';CACHE.mkdir(exist_ok=True)
FONT=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',27)

def run(args):
 r=subprocess.run([FF,'-hide_banner','-v','error','-y',*args],capture_output=True)
 if r.returncode:raise RuntimeError(r.stderr.decode())
 return r.stdout

def build(scene):
 key,folder,duration=scene
 directory=ROOT/'AI Day/高清剪辑素材'/folder
 files=[directory/n for n in ['input.mp4','ground_truth.mov','Baseline.mov','Ours.mov']]
 # Scan all original frames. Use the same crop for every method and every timestep.
 union=[720,540,0,0];counts=[];dimensions=[]
 for p in files[1:]:
  meta=subprocess.run([FF,'-hide_banner','-i',str(p)],capture_output=True,text=True).stderr
  dimensions.append(tuple(map(int,re.search(r'\b(\d{3,5})x(\d{3,5})\b',meta).groups())))
  raw=run(['-threads','2','-i',str(p),'-vf','scale=720:540,format=rgba,alphaextract','-f','rawvideo','-pix_fmt','gray','pipe:1'])
  size=720*540;assert len(raw)%size==0
  counts.append(len(raw)//size)
  for start in range(0,len(raw),size):
   bbox=Image.frombytes('L',(720,540),raw[start:start+size]).getbbox()
   if bbox:
    union=[min(union[0],bbox[0]),min(union[1],bbox[1]),max(union[2],bbox[2]),max(union[3],bbox[3])]
 assert len(set(dimensions))==1,dimensions
 assert all(n==duration*2 for n in counts),counts
 ow,oh=dimensions[0];pad=10
 left=max(0,math.floor((union[0]-pad)/720*ow/2)*2)
 top=max(0,math.floor((union[1]-pad)/540*oh/2)*2)
 right=min(ow,math.ceil((union[2]+pad)/720*ow/2)*2)
 bottom=min(oh,math.ceil((union[3]+pad)/540*oh/2)*2)
 crop=[right-left,bottom-top,left,top]
 cw,ch,th=640,480,54
 plate=Image.new('RGB',(cw*4,ch+th),'white');d=ImageDraw.Draw(plate)
 for i,label in enumerate(['RGB input','Ground truth','Previous SOTA','OVM-Occ (ours)']):
  d.text((i*cw+23,13),label,font=FONT,fill='#087e74' if i==3 else '#46575c')
  if i:d.line((i*cw,0,i*cw,ch+th),fill='#e1e7e4',width=2)
 platefile=CACHE/f'{key}-row-plate.png';plate.save(platefile)
 out=SITE/'assets/videos'/f'{key}-row-sota.mp4'
 args=['-loop','1','-framerate','2','-i',str(platefile)]
 for p in files:args+=['-threads','2','-i',str(p)]
 filters=[];prev='0:v'
 for i in range(4):
  cropping='' if i==0 else 'crop='+':'.join(map(str,crop))+','
  filters.append(f'[{i+1}:v]setpts=PTS-STARTPTS,{cropping}scale={cw}:{ch}:force_original_aspect_ratio=decrease,setsar=1,format=rgba[v{i}]')
  filters.append(f'[{prev}][v{i}]overlay=x={i*cw}+({cw}-overlay_w)/2:y={th}+({ch}-overlay_h)/2:shortest=1[o{i}]')
  prev=f'o{i}'
 args+=['-filter_complex_threads','2','-filter_complex',';'.join(filters),'-map',f'[{prev}]','-t',str(duration),'-an','-c:v','libx264','-crf','18','-preset','fast','-threads','2','-pix_fmt','yuv420p','-r','2','-movflags','+faststart',str(out)]
 run(args)
 run(['-ss','4','-i',str(out),'-frames:v','1','-q:v','2',str(SITE/'assets/images'/f'{key}-row-sota.jpg')])
 run(['-i',str(out),'-f','null','-'])
 result={'id':key+'-row-sota','source_dimensions':dimensions[0],'shared_crop_xywh':[left,top,right-left,bottom-top],'alpha_bounds_at_720x540':union,'source_frames_per_method':counts,'duration':duration,'fps':2,'width':cw*4,'height':ch+th,'bytes':out.stat().st_size,'all_frames_decode':'pass','crop_policy':'One fixed common crop for GT, LegoOcc and OVM-Occ from alpha bounds of all frames, with safety margin; original RGB unchanged. No interpolation or per-frame recentering.'}
 print(json.dumps(result),flush=True)
 return result
with ThreadPoolExecutor(max_workers=2) as pool:
 report=list(pool.map(build,[('comparison-scannet','卧室 ScanNet_scene0000_00',15),('comparison-replica','卧室 Replica_room1',26)]))
(SITE/'tools/comparison-row-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
