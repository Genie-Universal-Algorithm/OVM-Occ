"""Apply locally detected and manually reviewed face masks to the web demo."""
from pathlib import Path
from PIL import Image, ImageDraw
import json, math, subprocess
SITE=Path(__file__).resolve().parents[1]
CACHE=SITE/'tools/.media-cache/supermarket-privacy'
FF=str(SITE.parents[1]/'visualization/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1')
boxes=json.loads((CACHE/'mask-boxes.json').read_text())
# Keyframes: (frame, center_x, center_y). Coordinates refer to the 1620x454 web video.
# Include profile heads and partial faces missed by automatic detection.
def track(points,w,h):
 for (a,x1,y1),(b,x2,y2) in zip(points,points[1:]):
  for i in range(a,b+1):
   t=(i-a)/(b-a);x=x1+(x2-x1)*t;y=y1+(y2-y1)*t
   rect=[max(0,math.floor(x-w/2)),max(54,math.floor(y-h/2)),min(540,math.ceil(x+w/2)),min(448,math.ceil(y+h/2))]
   if rect[0]<rect[2] and rect[1]<rect[3]:boxes[i].append(rect)
# Seated visitor beside the mobility equipment at the entrance.
track([(0,270,62),(2,280,61),(3,299,61),(4,280,62),(5,294,61),(6,310,63),(7,310,66),(8,315,72),(9,342,79),(10,347,82),(11,373,89),(12,426,111)],48,50)
# First pass past the cafe tables.
track([(13,69,77),(14,190,74),(15,285,80),(16,310,83),(17,330,88),(18,381,91),(19,401,93),(20,403,101),(21,418,107),(22,442,118),(23,464,125),(24,530,146)],50,60)
track([(13,135,80),(14,250,76),(15,350,80),(16,382,87),(17,409,93),(18,477,103),(19,505,125),(20,532,134),(21,565,145)],52,60)
track([(13,95,97),(14,211,84),(15,310,105),(16,337,109),(17,355,119),(18,420,139),(19,448,132),(20,475,149),(21,505,174),(22,535,187)],58,70)
track([(13,5,74),(14,109,72),(15,219,76),(16,229,83),(17,256,86),(18,294,99),(19,310,105),(20,299,96),(21,310,102),(22,320,106),(23,318,111),(24,353,116),(25,449,104),(26,511,112),(27,563,118)],48,56)
track([(14,46,78),(15,166,82),(16,187,87),(17,209,100),(18,259,105),(19,265,113),(20,236,115),(21,246,121),(22,253,130),(23,253,135),(24,279,147),(25,370,167),(26,442,176),(27,505,172)],60,70)
# Seated people by the windows, including heads cut by the top edge.
track([(24,146,54),(25,223,62),(26,275,64),(27,301,57),(28,285,56),(29,289,54),(30,257,61),(31,256,60),(32,253,67),(33,252,69),(34,257,72),(35,256,74),(36,294,74),(37,391,80),(38,511,81)],48,58)
track([(24,300,54),(25,404,58),(26,470,62),(27,535,68),(28,563,74)],50,54)
# Second pass: small distant faces grow as the camera approaches.
track([(70,-5,65),(71,53,63),(72,150,67),(73,208,70),(74,230,68),(75,240,67),(76,243,70),(77,260,72),(78,290,80),(79,280,89)],34,42)
track([(81,264,76),(82,265,78),(83,266,78),(84,274,76),(85,308,83),(86,319,86),(87,320,87),(88,327,97),(89,255,100),(90,146,110),(91,-5,140)],50,64)
track([(82,352,78),(83,346,71),(84,365,80),(85,405,84),(86,423,87),(87,430,84),(88,438,95),(89,384,100),(90,288,99),(91,180,105),(92,79,112),(93,-15,130)],54,66)
track([(83,383,95),(84,391,105),(85,445,108),(86,464,112),(87,484,112),(88,505,123),(89,443,122),(90,330,125),(91,244,125),(92,18,169)],60,72)
track([(81,160,84),(82,114,85),(83,108,86),(84,92,80),(85,122,98),(86,115,96),(87,112,92),(88,95,105)],48,60)
track([(85,85,101),(86,83,104),(87,86,107),(88,70,110)],52,64)
# Entrance profile seen again near the end.
track([(90,533,78),(91,407,80),(92,294,70),(93,172,70),(94,88,78),(95,79,78),(96,66,83),(97,51,88),(98,22,105)],54,62)
masked=CACHE/'masked';masked.mkdir(exist_ok=True)
for i,row in enumerate(boxes):
 im=Image.open(CACHE/f'frame-{i+1:03d}.png').convert('RGB')
 original=im.copy()
 for rect in row:
  # At most 4x4 blocks per face; expanded mask covers the full head area.
  patch=original.crop(tuple(rect))
  small=patch.resize((max(1,min(4,patch.width//12)),max(1,min(4,patch.height//12))),Image.Resampling.BOX)
  im.paste(small.resize(patch.size,Image.Resampling.NEAREST),(rect[0],rect[1]))
 im.save(masked/f'frame-{i+1:03d}.png')
# Review all output frames as contact sheets, showing the RGB panel only.
for batch in range(5):
 sheet=Image.new('RGB',(2160,1416),'#eeeeee');draw=ImageDraw.Draw(sheet)
 for slot,i in enumerate(range(batch*24,min((batch+1)*24,115))):
  im=Image.open(masked/f'frame-{i+1:03d}.png').crop((0,48,540,260))
  x=slot%4*540;y=slot//4*236
  sheet.paste(im,(x,y+24));draw.text((x+5,y+5),f'FRAME {i} / {i/5:.1f}s',fill='black')
 sheet.save(CACHE/f'masked-review-{batch}.jpg')
out=SITE/'assets/videos/supermarket-face-mosaic.mp4'
subprocess.run([FF,'-hide_banner','-v','error','-y','-framerate','5','-i',str(masked/'frame-%03d.png'),'-an','-c:v','libx264','-crf','18','-preset','fast','-threads','2','-pix_fmt','yuv420p','-movflags','+faststart',str(out)],check=True)
subprocess.run([FF,'-hide_banner','-v','error','-y','-ss','4','-i',str(out),'-frames:v','1','-q:v','2',str(SITE/'assets/images/supermarket-face-mosaic.jpg')],check=True)
subprocess.run([FF,'-hide_banner','-v','error','-i',str(out),'-f','null','-'],check=True)
(SITE/'tools/supermarket-face-mosaic-manifest.json').write_text(json.dumps({'source':'assets/videos/supermarket.mp4','output':'assets/videos/supermarket-face-mosaic.mp4','frames':115,'fps':5,'duration':23,'mask_boxes_per_frame':boxes,'full_decode':'pass'},indent=2)+'\n')
print('Masked 115 frames, generated video and poster, and passed full decode.')
