"""Enlarge selected occupancy panels from original media, preserving full sequences."""
from pathlib import Path
import json
import math
import re
import subprocess
from PIL import Image, ImageDraw, ImageFont

SITE = Path(__file__).resolve().parents[1]
ROOT = SITE.parents[1]
FF = str(ROOT / 'visualization/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1')


def run(args):
    result = subprocess.run([FF, '-hide_banner', '-v', 'error', '-y', *args], capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode())
    return result.stdout


def build_living_room():
    folder = ROOT / 'AI Day/高清剪辑素材/客厅 scene0024_02'
    local = folder / 'local.mov'
    ow, oh = 3600, 2624
    sw, sh = 900, 656
    raw = run(['-threads', '2', '-i', str(local), '-vf', f'scale={sw}:{sh},format=rgba,alphaextract', '-f', 'rawvideo', '-pix_fmt', 'gray', 'pipe:1'])
    size = sw * sh
    assert len(raw) == size * 30
    bounds = [sw, sh, 0, 0]
    for i in range(0, len(raw), size):
        box = Image.frombytes('L', (sw, sh), raw[i:i + size]).getbbox()
        if box:
            bounds = [min(bounds[0], box[0]), min(bounds[1], box[1]), max(bounds[2], box[2]), max(bounds[3], box[3])]
    # A single fixed crop keeps the whole sequence stable and inside the frame.
    left, top, right, bottom = [v * 4 for v in bounds]
    zoom = min(1.35, ow / (right - left + 80), oh / (bottom - top + 80))
    cw, ch = math.ceil(ow / zoom / 2) * 2, math.ceil(oh / zoom / 2) * 2
    x = int(max(0, min(ow - cw, (left + right - cw) / 2)) // 2 * 2)
    y = int(max(0, min(oh - ch, (top + bottom - ch) / 2)) // 2 * 2)
    assert x <= left and y <= top and x + cw >= right and y + ch >= bottom
    plate = SITE / 'tools/.media-cache/living-room-plate.png'
    args = ['-loop', '1', '-framerate', '2', '-i', str(plate)]
    for name in ['input.mp4', 'local.mov', 'global.mov']:
        args += ['-threads', '2', '-i', str(folder / name)]
    filters = []
    prev = '0:v'
    for i in range(3):
        crop = f'crop={cw}:{ch}:{x}:{y},' if i == 1 else ''
        filters.append(f'[{i+1}:v]setpts=PTS-STARTPTS,{crop}scale=540:406:force_original_aspect_ratio=decrease,setsar=1,format=rgba[v{i}]')
        filters.append(f'[{prev}][v{i}]overlay=x={i*540}+(540-overlay_w)/2:y=48+(406-overlay_h)/2:shortest=1[o{i}]')
        prev = f'o{i}'
    out = SITE / 'assets/videos/living-room-enlarged.mp4'
    args += ['-filter_complex_threads', '2', '-filter_complex', ';'.join(filters), '-map', f'[{prev}]', '-t', '15', '-an', '-c:v', 'libx264', '-crf', '18', '-preset', 'fast', '-threads', '2', '-pix_fmt', 'yuv420p', '-r', '2', '-movflags', '+faststart', str(out)]
    run(args)
    run(['-ss', '4', '-i', str(out), '-frames:v', '1', '-q:v', '2', str(SITE / 'assets/images/living-room-enlarged.jpg')])
    run(['-i', str(out), '-f', 'null', '-'])
    report = {'output': str(out.relative_to(SITE)), 'local_occupancy_zoom': zoom, 'fixed_crop_xywh': [x, y, cw, ch], 'all_frame_alpha_bounds': [left, top, right, bottom], 'duration': 15, 'fps': 2, 'full_decode': 'pass'}
    (SITE / 'tools/living-room-enlarged-manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report), flush=True)


def build_scannet():
    folder = ROOT / 'AI Day/高清剪辑素材/卧室 ScanNet_scene0000_00'
    # Reuse the shared crop established from every frame of all three methods.
    report = json.loads((SITE / 'tools/comparison-row-manifest.json').read_text())[0]
    x, y, cw, ch = report['shared_crop_xywh']
    width, height, title = 640, 560, 54
    plate = Image.new('RGB', (width * 4, height + title), 'white')
    draw = ImageDraw.Draw(plate)
    font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 27)
    for i, label in enumerate(['RGB input', 'Ground truth', 'Previous SOTA', 'OVM-Occ (ours)']):
        draw.text((i * width + 23, 13), label, font=font, fill='#087e74' if i == 3 else '#46575c')
        if i:
            draw.line((i * width, 0, i * width, height + title), fill='#e1e7e4', width=2)
    platefile = SITE / 'tools/.media-cache/comparison-scannet-enlarged-plate.png'
    plate.save(platefile)
    args = ['-loop', '1', '-framerate', '2', '-i', str(platefile)]
    for name in ['input.mp4', 'ground_truth.mov', 'Baseline.mov', 'Ours.mov']:
        args += ['-threads', '2', '-i', str(folder / name)]
    filters, prev = [], '0:v'
    for i in range(4):
        crop = '' if i == 0 else f'crop={cw}:{ch}:{x}:{y},'
        target_height = 480 if i == 0 else height
        filters.append(f'[{i+1}:v]setpts=PTS-STARTPTS,{crop}scale={width}:{target_height}:force_original_aspect_ratio=decrease,setsar=1,format=rgba[v{i}]')
        filters.append(f'[{prev}][v{i}]overlay=x={i*width}+({width}-overlay_w)/2:y={title}+({height}-overlay_h)/2:shortest=1[o{i}]')
        prev = f'o{i}'
    out = SITE / 'assets/videos/comparison-scannet-enlarged.mp4'
    args += ['-filter_complex_threads', '2', '-filter_complex', ';'.join(filters), '-map', f'[{prev}]', '-t', '15', '-an', '-c:v', 'libx264', '-crf', '18', '-preset', 'fast', '-threads', '2', '-pix_fmt', 'yuv420p', '-r', '2', '-movflags', '+faststart', str(out)]
    run(args)
    run(['-ss', '4', '-i', str(out), '-frames:v', '1', '-q:v', '2', str(SITE / 'assets/images/comparison-scannet-enlarged.jpg')])
    run(['-i', str(out), '-f', 'null', '-'])
    result = {'output': str(out.relative_to(SITE)), 'shared_crop_xywh': [x, y, cw, ch], 'occupancy_zoom': min(width/cw, height/ch) / min(width/cw, 480/ch), 'duration': 15, 'fps': 2, 'rgb_scale': 'unchanged', 'full_decode': 'pass'}
    (SITE / 'tools/scannet-enlarged-manifest.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    import sys
    if 'scannet' in sys.argv:
        build_scannet()
    else:
        build_living_room()
