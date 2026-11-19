"""Build the self-contained static homepage from the latest pages.md."""
from pathlib import Path
import html,re,sys
SITE=Path(__file__).resolve().parents[1]
if (SITE/'index.html').exists() and '--overwrite' not in sys.argv:
 raise SystemExit('Existing index.html may contain manual edits. Patch it in place. Full regeneration requires explicit --overwrite and will replace those edits.')
source=(SITE.parent/'pages.md').read_text()
def esc(s): return html.escape(s,quote=True)
def rich(s): return re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',esc(s))
def field(label):
 return re.search(r'^- '+re.escape(label)+r'：(.+)$',source,re.M).group(1).strip()
def paragraph(a,b):
 text=source.split(a,1)[1].split(b,1)[0].strip()
 return re.sub(r'\s+',' ',text)
author_section = source.split('## 4. 作者与单位', 1)[1].split('## 5.', 1)[0]
author_rows = []
for line in author_section.splitlines():
 if re.match(r'\|\s*\d+\s*\|', line):
  author_rows.append([cell.strip() for cell in line.strip('|').split('|')])
author_items = []
corresponding = []
for order, name, affiliations, email, marker in author_rows:
 name_html = f'<a href="mailto:{esc(email)}">{esc(name)}</a>' if email else f'<span>{esc(name)}</span>'
 author_items.append(f'<li>{name_html}<sup>{esc(marker)}</sup></li>')
 if '†' in marker:
  corresponding.append(f'<a href="mailto:{esc(email)}">{esc(name)}</a>')
authors_html = '<div class="authors"><ul class="author-list" aria-label="Authors">' + ''.join(author_items) + '</ul><p class="affiliations"><span><sup>1</sup> Zhejiang University</span><span><sup>2</sup> AgiBot</span><span class="author-note">† Corresponding author: ' + ', '.join(corresponding) + '</span></p></div>'
abstract=paragraph('### 项目摘要','### 希望突出的贡献')
for old,new in [('finegrained','fine-grained'),('OVMOcc','OVM-Occ'),('instanceaware','instance-aware')]:abstract=abstract.replace(old,new)
contrib=source.split('### 希望突出的贡献',1)[1].split('## 3.',1)[0]
contributions=re.findall(r'\d\. \*\*(.+?)\*\*\s*(.*?)(?=\n\d\. \*\*|\Z)',contrib,re.S)
contribution_html=''.join(f'<article class="contribution"><span class="index">0{i+1}</span><h3>{esc(title.rstrip("."))}</h3><p>{esc(re.sub(chr(10)," ",text.strip()))}</p></article>' for i,(title,text) in enumerate(contributions))
figures=[]
for key,heading,title in [('teacher','#### 教师特征生产管线','Instance-aware vision-language teacher'),('student','#### 学生模型','Geometry-aware Gaussian occupancy')]:
 part=source.split(heading,1)[1].split('###',1)[0]
 caption=re.search(r'- 图片说明：(.+)',part).group(1)
 figures.append(f'''<figure class="method-figure"><div class="figure-heading"><h3>{title}</h3><span>Click to enlarge ↗</span></div><a class="zoomable" href="assets/images/{key}.png" aria-label="Enlarge {title}"><img src="assets/images/{key}.png" alt="{esc(caption)}" loading="lazy" width="2400" height="{1334 if key=='teacher' else 1177}"></a><figcaption>{esc(caption)}</figcaption></figure>''')

def video_panel(group,key,title,detail,first=False):
 attributes = f'role="tabpanel" aria-labelledby="tab-{group}-{key}" tabindex="0"' if group != 'navigation' else f'aria-label="{esc(title)}"'
 return f'''<div id="{group}-{key}" class="tab-panel" {attributes}><div class="video-frame"><video controls playsinline muted loop preload="none" poster="assets/images/{key}.jpg" aria-label="{esc(title)}"><source src="assets/videos/{key}.mp4" type="video/mp4">Your browser does not support video playback. <a href="assets/videos/{key}.mp4">Download the video</a>.</video></div><div class="media-caption"><span>{esc(title)}</span><span>{esc(detail)}</span></div></div>'''
def gallery(group,items):
 buttons=''.join(f'<button type="button" role="tab" id="tab-{group}-{key}" aria-controls="{group}-{key}" aria-selected="{str(i==0).lower()}" tabindex="{0 if i==0 else -1}">{esc(label)}</button>' for i,(key,label,title,detail) in enumerate(items))
 panels=''.join(video_panel(group,key,title,detail,i==0) for i,(key,label,title,detail) in enumerate(items))
 return f'<div class="tabs" data-tabs><div class="tab-list" role="tablist" aria-label="{group} scenes">{buttons}</div>{panels}</div>'
comparison=gallery('comparison',[
 ('comparison-scannet','ScanNet · Bedroom','OpenOcc-ScanNet: Bedroom Scene','RGB · Ground truth · LegoOcc · OVM-Occ'),
 ('comparison-replica','Replica · Bedroom','OpenOcc-Replica: Bedroom Scene','RGB · Ground truth · LegoOcc · OVM-Occ')])
generalization=gallery('generalization',[
 ('tearoom','Tearoom','Tearoom Scene','RGB · Local occupancy · Global map'),
 ('elevator','Elevator lobby','Elevator Lobby Scene','RGB · Local occupancy · Global map'),
 ('office-e2','Office','Office Scene','RGB · Local occupancy · Global map')])
mapping=gallery('mapping',[
 ('living-room','Living room','Living Room Scene','RGB · Local occupancy · Global map'),
 ('supermarket','Supermarket','Supermarket Scene','RGB · Local occupancy · Global map'),
 ('office-e1','Office','Office Scene','RGB · Local occupancy · Global map')])
# Tables remain faithful to the current requirements document, including deliberate omissions.
tables=[]
notes=[
 'Open-vocabulary methods supervised by geometry-only annotations. Bold values indicate the best result among the listed methods.',
 'Per-class IoU is shown for selected categories under the 40-class protocol. The final columns report mIoU for the 11-, 20-, and 40-class protocols.',
 'Each entry reports IoU / mIoU. Pre-training uses Occ-ScanNet; fine-tuning uses 100 or 1.1K Replica frames. “Ours” denotes OVM-Occ.',
 'Factorized ablation on Occ-ScanNet. VL denotes vision-language; “Ours” denotes the OVM-Occ student framework.'
]
labels=['Occ-ScanNet','OpenOcc-ScanNet','Few-shot transfer','Factorized ablation']
for i in range(1,5):
 block=source.split(f'### Table {i}. ',1)[1].split('\n### ',1)[0].split('\n## ',1)[0]
 title=block.splitlines()[0]
 rows=[[c.strip() for c in line.strip().strip('|').split('|')] for line in block.splitlines() if line.startswith('|')]
 header,values=rows[0],rows[2:]
 assert all(len(row)==len(header) for row in values)
 head=''.join(f'<th scope="col">{esc(cell)}</th>' for cell in header)
 body=''
 for row in values:
  is_ours='Ours' in row[0]
  body+=f'<tr class="{"ours" if is_ours else ""}"><th scope="row">{rich(row[0])}</th>'+''.join(f'<td>{rich(c)}</td>' for c in row[1:])+'</tr>'
 tables.append(f'''<div class="tab-panel result-panel" id="result-{i}" role="tabpanel" aria-labelledby="tab-result-{i}" tabindex="0"><div class="table-heading"><span class="eyebrow">Table 0{i}</span><h3>{esc(title)}</h3></div><div class="table-scroll" role="region" aria-label="Table {i}: {esc(title)}" tabindex="0"><table><caption class="sr-only">Table {i}: {esc(title)}. All metrics are percentages; higher is better.</caption><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div><p class="table-note">{notes[i-1]}</p></div>''')
results_buttons=''.join(f'<button type="button" role="tab" id="tab-result-{i}" aria-controls="result-{i}" aria-selected="{str(i==1).lower()}" tabindex="{0 if i==1 else -1}">{label}</button>' for i,label in enumerate(labels,1))
bib=source.split('@misc{',1)[1].split('\n}',1)[0]
bib='@misc{'+bib+'\n}'
# Preserve the citation supplied in pages.md as plain text; paper/code entry buttons remain hidden.
page=f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>OVM-Occ — Open-Vocabulary Monocular Occupancy Prediction</title>
<meta name="description" content="{esc(field('一句话介绍'))}">
<meta name="theme-color" content="#087e74">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="styles.css"><script src="app.js" defer></script>
</head>
<body>
<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><nav class="nav-shell" aria-label="Main navigation"><a class="brand" href="#top"><svg width="27" height="29" viewBox="0 0 27 29" aria-hidden="true"><path d="M13.5 1 26 8v13l-12.5 7L1 21V8Z M1 8l12.5 7L26 8 M13.5 15v13" fill="none" stroke="currentColor" stroke-width="1.7"/></svg> OVM-Occ</a><div class="nav-links"><a href="#overview">Overview</a><a href="#method">Method</a><a href="#demos">Demos</a><a href="#results">Results</a></div><a class="nav-citation" href="#citation">Cite this work ↗</a></nav></header>
<main id="main">
<section class="hero container" id="top">
<p class="eyebrow">Monocular vision · Open-vocabulary semantics</p>
<h1><span>OVM-Occ</span><br>Open-Vocabulary Monocular Occupancy Prediction <span class="title-sub">via Geometry-Aware Vision-Language Distillation</span></h1>
{authors_html}
<div class="hero-actions"><a class="button primary" href="#demos"><svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true"><path d="m5 3 8 5-8 5Z" fill="currentColor"/></svg> Explore the demos</a><a class="button secondary" href="#method">Discover the method <span aria-hidden="true">↓</span></a></div>
<figure class="hero-figure distillation-figure"><a class="zoomable" href="assets/images/teacher-student-overview-hq.png" aria-label="Enlarge teacher–student distillation overview"><img src="assets/images/teacher-student-overview-hq.png" width="6000" height="1666" alt="Teacher construction and student model pipelines connected by a distillation arrow." fetchpriority="high"></a><figcaption>Teacher construction and student model, connected through semantic distillation during training.</figcaption></figure>
</section>
<section class="section soft" id="overview"><div class="container"><div class="contributions">{contribution_html}</div><div class="section-heading abstract-heading"><h2>Abstract</h2></div><div class="abstract"><p>{esc(abstract)}</p></div></div></section>
<section class="section container" id="method"><div class="section-heading"><h2>Method</h2></div>{''.join(figures)}</section>
<section class="section soft" id="demos"><div class="container"><div class="section-heading"><h2>Demos</h2></div><article class="demo-block"><div class="demo-heading"><span class="index">A</span><div><h3>Performance comparison</h3><p>Qualitative video comparisons demonstrate that our method outperforms the baseline, achieving more accurate semantic predictions and stronger instance-level semantic consistency.</p></div></div>{comparison}</article><article class="demo-block"><div class="demo-heading"><span class="index">B</span><div><h3>Few-shot adaptation to real-world environments</h3><p>OVM-Occ adapts to new real-world environments through few-shot fine-tuning using limited data collected by a physical robot.</p></div></div>{generalization}</article><article class="demo-block"><div class="demo-heading"><span class="index">C</span><div><h3>Application: EmbodiedOcc task</h3><p>OVM-Occ integrates multi-frame occupancy predictions through cumulative voting to construct a globally consistent 3D semantic occupancy map.</p></div></div>{mapping}</article><article class="demo-block"><div class="demo-heading"><span class="index">D</span><div><h3>Application: Open-vocabulary semantic navigation</h3><p>Language-guided semantic queries connect the occupancy map with global and local planning.</p></div></div>{video_panel('navigation','navigation','Classroom Scene','Global & local semantic maps and planning')}</article></div></section>
<section class="section container" id="results"><div class="section-heading"><h2>Results</h2></div><div class="results-meta"><span>IoU &amp; mIoU (%) · Higher is better ↑</span><span>Scroll wide tables horizontally ↔</span></div><div class="tabs result-tabs" data-tabs><div class="tab-list" role="tablist" aria-label="Experimental results">{results_buttons}</div>{''.join(tables)}</div></section>
<section class="section soft" id="citation"><div class="container citation-layout"><div><h2>Citation</h2></div><div class="citation-box"><div class="code-heading"><span>BibTeX</span><button type="button" class="copy-button" id="copy-citation">Copy citation</button></div><pre><code id="bibtex">{esc(bib)}</code></pre><span class="sr-only" id="copy-status" aria-live="polite"></span></div></div></section>
</main><footer class="container footer"><a class="brand" href="#top">OVM-Occ</a><p>Open-vocabulary scene understanding from a single image.</p><a href="mailto:youngyu@zju.edu.cn">Contact ↗</a></footer>
<dialog id="figure-dialog" aria-label="Expanded method figure"><div class="dialog-bar"><span>Method overview</span><button type="button" id="close-figure" aria-label="Close expanded figure">Close ×</button></div><img id="expanded-figure" alt=""></dialog>
</body></html>'''
(SITE/'index.html').write_text(page)
print('Built index.html from pages.md: 4 result tables, 9 video scenes, 2 method figures.')
