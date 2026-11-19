"""Pair two real-world scenes, each with RGB and occupancy prediction only."""
from pathlib import Path
import subprocess,json
from PIL import Image,ImageDraw,ImageFont
SITE=Path(__file__).resolve().parents[1];ROOT=SITE.parents[1]
FF=str(ROOT/'visualization/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1')
SRC=ROOT/'AI Day/高清剪辑素材'
files=[SRC/'茶水间 3367531/input.mov',SRC/'茶水间 3367531/local.mov',SRC/'电梯厅 3338370/input.mov',SRC/'电梯厅 3338370/local.mov']
font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',24)
bold=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',27)
cw,ch,th=640,480,84
plate=Image.new('RGB',(cw*4,ch+th),'white');d=ImageDraw.Draw(plate)
for x,text in [(640,'Tearoom Scene'),(1920,'Elevator Lobby Scene')]:
 d.text((x,12),text,font=bold,anchor='mt',fill='#243e43')
for i in range(4):
 d.text((i*cw+24,49),'RGB input' if i%2==0 else 'Occupancy Prediction',font=font,fill='#46575c' if i%2==0 else '#087e74')
 if i:d.line((i*cw,40 if i%2 else 0,i*cw,ch+th),fill='#dfe7e5',width=2)
cache=SITE/'tools/.media-cache';cache.mkdir(exist_ok=True)
platefile=cache/'fewshot-paired-plate.png';plate.save(platefile)
args=['-loop','1','-framerate','2','-i',str(platefile)]
for p in files:args+=['-threads','2','-i',str(p)]
filters=[];prev='0:v'
for i in range(4):
 filters.append(f'[{i+1}:v]setpts=PTS-STARTPTS,scale={cw}:{ch}:force_original_aspect_ratio=decrease,setsar=1,format=rgba[v{i}]')
 filters.append(f'[{prev}][v{i}]overlay=x={i*cw}+({cw}-overlay_w)/2:y={th}+({ch}-overlay_h)/2:shortest=1[o{i}]')
 prev=f'o{i}'
out=SITE/'assets/videos/fewshot-tearoom-elevator.mp4'
args+=['-filter_complex_threads','2','-filter_complex',';'.join(filters),'-map',f'[{prev}]','-t','15','-an','-c:v','libx264','-crf','18','-preset','fast','-threads','2','-pix_fmt','yuv420p','-r','2','-movflags','+faststart',str(out)]
def run(a):
 r=subprocess.run([FF,'-hide_banner','-v','error','-y',*a],capture_output=True,text=True)
 assert r.returncode==0,r.stderr
run(args)
run(['-ss','4','-i',str(out),'-frames:v','1','-q:v','2',str(SITE/'assets/images/fewshot-tearoom-elevator.jpg')])
run(['-i',str(out),'-f','null','-'])
(SITE/'tools/fewshot-row-manifest.json').write_text(json.dumps({'sources':[str(p.relative_to(ROOT)) for p in files],'output':str(out.relative_to(SITE)),'duration':15,'fps':2,'layout':'Tearoom RGB / Tearoom Occupancy Prediction / Elevator RGB / Elevator Occupancy Prediction','global_map_panels':False,'processing':'Full source frames, equal panel sizes, original playback speed; transparent pixels composited onto white.','all_frames_decode':'pass'},ensure_ascii=False,indent=2)+'\n')
print('Created and decoded four-column RGB / Occupancy Prediction video, 15 seconds.',flush=True)
