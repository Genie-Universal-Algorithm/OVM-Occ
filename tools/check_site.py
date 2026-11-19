"""Check document fidelity, static resource integrity, and complete video decoding."""
from pathlib import Path
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor
import html,json,re,subprocess
SITE=Path(__file__).resolve().parents[1];ROOT=SITE.parents[1]
class Parser(HTMLParser):
    def __init__(self):super().__init__();self.ids=[];self.refs=[];self.elements=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs);self.elements.append((tag,attrs))
        if 'id' in attrs:self.ids.append(attrs['id'])
        for name in ['href','src','poster']:
            if attrs.get(name):self.refs.append(attrs[name])
p=Parser();content=(SITE/'index.html').read_text();p.feed(content)
assert len(p.ids)==len(set(p.ids)),'Duplicate IDs'
for ref in p.refs:
    if ref.startswith('#'):assert ref[1:] in p.ids,ref
    elif not ref.startswith(('mailto:','http:','https:','data:')):assert (SITE/ref).is_file(),ref
for tag,attrs in p.elements:
    for name in ['aria-controls','aria-labelledby']:
        if name in attrs:assert attrs[name] in p.ids
    if tag=='img':assert 'alt' in attrs
    if tag=='video':assert 'controls' in attrs and 'playsinline' in attrs
    if attrs.get('role')=='tab':assert attrs.get('aria-selected') in ['true','false']
assert len([x for x in p.elements if x[0]=='video'])==9
assert not re.search(r'href="https?://',content),'Unexpected public paper/code link'
source=(SITE.parent/'pages.md').read_text()
tables=re.findall(r'<table>(.*?)</table>',content,re.S)
assert len(tables)==4
for i,table in enumerate(tables,1):
    block=source.split(f'### Table {i}. ',1)[1].split('\n### ',1)[0].split('\n## ',1)[0]
    expected=[[c.strip().replace('**','') for c in line.strip().strip('|').split('|')] for line in block.splitlines() if line.startswith('|')]
    expected=expected[:1]+expected[2:]
    actual=[]
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>',table,re.S):
        actual.append([html.unescape(re.sub('<[^>]+>','',c)) for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>',tr,re.S)])
    assert actual==expected,f'Table {i} mismatch'
ff=str(ROOT/'visualization/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1')
manifest=json.loads((SITE/'tools/media-manifest.json').read_text())
def check_video(item):
    path=SITE/'assets/videos'/f'{item["id"]}.mp4'
    result=subprocess.run([ff,'-hide_banner','-v','error','-threads','2','-i',str(path),'-f','null','-'],capture_output=True,text=True)
    assert result.returncode==0 and not result.stderr,(item['id'],result.stderr)
    meta=subprocess.run([ff,'-hide_banner','-i',str(path)],capture_output=True,text=True).stderr
    assert 'Video: h264' in meta and 'yuv420p' in meta
    h,m,s=map(float,re.search(r'Duration: (\d+):(\d+):([\d.]+)',meta).groups())
    assert abs(h*3600+m*60+s-item['duration'])<.06,item['id']
    return item['id']
with ThreadPoolExecutor(max_workers=2) as pool:checked=list(pool.map(check_video,manifest))
report={'static_resources':'pass','unique_ids_and_aria_targets':'pass','table_fidelity_to_pages_md':'all cells pass in all 4 tables','video_decode':'all 9 videos pass','source_duration_preserved':True,'decoded_videos':checked,'javascript_syntax':'checked separately with node --check','browser_visual_and_interaction_test':'not run: local browser use disabled','reference_site':'unavailable during build','public_deployment':False}
(SITE/'tools/qa-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
