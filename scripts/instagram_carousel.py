#!/usr/bin/env python3
"""Complete already curated activity carousels from official public Instagram embeds.
No login, private APIs or access-control workarounds. Stop on rate/permission errors.
Available public photos and MP4 videos retain original order. No access workarounds.
"""
from __future__ import annotations
import argparse, datetime as dt, io, json, os, re, subprocess, sys, time
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageOps

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/gallery.json'
ASSETS=ROOT/'assets/instagram'
STATE=ROOT/'.cache/carousel-backfill.json'
CARDS=Path('/home/ljs1092/jaram-miri-scan/public_cards_20261121.json')
CODE=re.compile(r'^[A-Za-z0-9_-]{6,32}$')
SESSION=requests.Session()
SESSION.headers.update({'User-Agent':'Mozilla/5.0','Referer':'https://www.instagram.com/'})
Image.MAX_IMAGE_PIXELS=35_000_000

class AccessBlocked(RuntimeError):pass
def log(*x):print(dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),*x,flush=True)
def command(args,timeout=120):
    return subprocess.run(args,cwd=ROOT,check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout).stdout.strip()
def valid_code(code):return isinstance(code,str) and bool(CODE.fullmatch(code))

def public_get(url,*,image=False,video=False):
    parsed=urlparse(url)
    host=(parsed.hostname or '').lower()
    allowed=(host.endswith('.cdninstagram.com') or host.endswith('.fbcdn.net')) if (image or video) else host=='www.instagram.com'
    if parsed.scheme!='https' or not allowed or parsed.username or parsed.password:raise ValueError('Unexpected public source host')
    with SESSION.get(url,timeout=(7,15),stream=True,allow_redirects=False) as r:
        if r.status_code in (401,403,429):raise AccessBlocked('Public source returned HTTP '+str(r.status_code))
        if r.status_code!=200:raise RuntimeError('Public source HTTP '+str(r.status_code))
        chunks=[];size=0
        for chunk in r.iter_content(65536):
            size+=len(chunk)
            if size>(40_000_000 if video else 15_000_000 if image else 5_000_000):raise RuntimeError('Source response too large')
            chunks.append(chunk)
        return b''.join(chunks)

def media_objects(obj):
    if isinstance(obj,dict):
        if isinstance(obj.get('shortcode_media'),dict):yield obj['shortcode_media']
        for k,v in obj.items():
            if k=='contextJSON' and isinstance(v,str):
                try:yield from media_objects(json.loads(v))
                except ValueError:pass
            elif isinstance(v,(dict,list)):yield from media_objects(v)
    elif isinstance(obj,list):
        for v in obj:yield from media_objects(v)

def official_media(code):
    if not valid_code(code):raise ValueError('Invalid shortcode')
    raw=public_get('https://www.instagram.com/p/'+code+'/embed/')
    soup=BeautifulSoup(raw,'html.parser')
    for t in soup.find_all('script'):
        z=t.string or t.get_text()
        if 'shortcode_media' not in z or 's.handle(' not in z:continue
        try:
            obj,_=json.JSONDecoder().raw_decode(z[z.index('s.handle(')+9:])
        except ValueError:continue
        for media in media_objects(obj):
            if media.get('shortcode')==code and media.get('owner',{}).get('username','').lower()=='jaram_miri':
                return media
    raise RuntimeError('Public embed does not expose verified account media')

def source_count(post):
    n=post.get('media_total',0)
    return n if isinstance(n,int) and 0<n<=50 else 0

def choose_source(node):
    # display_url is the original aspect ratio, not the square profile thumbnail.
    u=node.get('display_url')
    if isinstance(u,str) and u.startswith('https://'):return u
    resources=node.get('display_resources',[])
    return max(resources,key=lambda x:x.get('config_width',0)*x.get('config_height',0)).get('src','') if resources else ''

def download_image(node):
    raw=public_get(choose_source(node),image=True)
    with Image.open(io.BytesIO(raw)) as im:
        if im.format not in ('JPEG','PNG','WEBP','HEIF') or min(im.size)<220:raise RuntimeError('Invalid photo response')
        im=ImageOps.exif_transpose(im).convert('RGB')
        im.thumbnail((1200,1200),Image.Resampling.LANCZOS)
        buf=io.BytesIO();im.save(buf,'JPEG',quality=85,optimize=True,progressive=True);return buf.getvalue()

def complete(post):
    code=post['id'];media=official_media(code)
    edges=media.get('edge_sidecar_to_children',{}).get('edges')
    expected=source_count(post)
    if not edges:
        if expected>1:raise RuntimeError('Public embed returned no carousel children')
        nodes=[media]
    else:
        if not isinstance(edges,list) or not 2<=len(edges)<=50:raise RuntimeError('Unexpected carousel size')
        if expected>1 and len(edges)<expected:raise RuntimeError('Public embed has fewer items than previously observed')
        nodes=[e.get('node',{}) for e in edges]
    if any(not isinstance(n,dict) or not valid_code(n.get('shortcode')) for n in nodes):raise RuntimeError('Invalid child identity')
    if len({n['shortcode'] for n in nodes})!=len(nodes):raise RuntimeError('Duplicate child identity')
    cache=ROOT/'.cache/carousel-downloads';cache.mkdir(parents=True,exist_ok=True)
    photos=[];items=[];prepared=[];videos=0;unavailable=0
    for i,node in enumerate(nodes,1):
        name=f'{code}-carousel-{i:02d}.jpg';target=cache/name
        if not target.exists():
            blob=download_image(node);tmp=target.with_suffix('.tmp');tmp.write_bytes(blob);tmp.replace(target)
        with Image.open(target) as im:im.verify()
        relative='assets/instagram/'+name
        prepared.append((target,ASSETS/name));photos.append(relative)
        if node.get('is_video') is True:
            videos+=1;vname=f'{code}-carousel-{i:02d}.mp4';vtarget=cache/vname
            try:
                if not vtarget.exists():
                    blob=public_get(node.get('video_url',''),video=True)
                    if len(blob)<1024 or blob[4:8]!=b'ftyp':raise RuntimeError('Not a valid MP4 container')
                    tmp=vtarget.with_suffix('.tmp');tmp.write_bytes(blob);tmp.replace(vtarget)
                prepared.append((vtarget,ASSETS/vname))
                items.append({'type':'video','src':'assets/instagram/'+vname,'poster':relative})
            except AccessBlocked:raise
            except Exception as exc:
                unavailable+=1;log('Video unavailable',code,i,type(exc).__name__)
                items.append({'type':'image','src':relative,'video_unavailable':True})
        else:items.append({'type':'image','src':relative})
        time.sleep(.25)
    for source,destination in prepared:destination.write_bytes(source.read_bytes())
    return {**post,'images':photos,'media':items,'media_total':len(nodes),'media_checked':True,'video_count':videos,'media_unavailable':unavailable}

def seed(posts):
    if not CARDS.is_file():return 0
    records=json.loads(CARDS.read_text(encoding='utf-8'))['posts']
    byid={p['id']:p for p in records}
    n=0
    for p in posts:
        if p.get('editor_images_locked'):continue
        kind=byid.get(p['id'],{}).get('type','')
        if kind in ('Reel','Video') and not p.get('media'):
            if p.get('media_checked') is not False:p['media_total']=1;p['media_checked']=False;n+=1
            continue
        if p.get('media_checked') or p.get('media_total'):continue
        kind=byid.get(p['id'],{}).get('type','')
        m=re.search(r'Photos and videos in this post:,\s*(\d+)',kind)
        if m and 2<=int(m[1])<=50:
            p['media_total']=int(m[1]);p['media_checked']=False;n+=1
    return n

def publish(posts,old):
    if posts==old:return
    DATA.write_text(json.dumps(posts,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    command([sys.executable,'scripts/render_gallery.py'],90)
    command(['/usr/bin/node','--check','script.js'])
    # Stage only referenced, fully verified images; incomplete downloads stay in .cache.
    paths=['data/gallery.json','index.html','activities.html','sitemap.xml','robots.txt','llms.txt','faq.html','credits.html']
    paths+=sorted({img for p in posts if p.get('media_checked') for img in p['images'] if '-carousel-' in img})
    paths+=sorted({m['src'] for p in posts for m in p.get('media',[]) if m.get('type')=='video'})
    command(['git','add','--',*paths],60)
    command(['git','diff','--cached','--check'])
    command(['git','-c','user.name=JARAM Profile Bot','-c','user.email=jungsuplee-hub@users.noreply.github.com','commit','-m','Complete verified Instagram activity photo carousels'],90)
    command(['git','push','origin','main'],120)
    command(['/home/ljs1092/deploy-jaram-miri.sh'],120)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--limit',type=int,default=8)
    parser.add_argument('--first',default='',help='Prioritize a known curated shortcode')
    args=parser.parse_args()
    if not 1<=args.limit<=20:parser.error('limit must be 1..20')
    dirty=command(['git','status','--porcelain'])
    if dirty:raise RuntimeError('Tracked local edits exist; refusing overwrite')
    command(['git','pull','--ff-only','origin','main'],60)
    old=json.loads(DATA.read_text(encoding='utf-8'));posts=json.loads(json.dumps(old))
    seeded=seed(posts)
    state=json.loads(STATE.read_text()) if STATE.exists() else {}
    failures=state.get('failures',{})
    # Retry failed or unavailable posts no more than once every 24 hours.
    now=time.time()
    pending=[(i,p) for i,p in enumerate(posts) if (p.get('media_checked') is False or p.get('media_unavailable',0)>0) and not p.get('editor_images_locked')]
    ready=[(i,p) for i,p in pending if now-failures.get(p['id'],{}).get('at',0)>=86400]
    if args.first:ready.sort(key=lambda pair:pair[1]['id']!=args.first)
    # Back off on explicit denial or rate limiting, rather than attempting workarounds.
    if now<state.get('blocked_until',0):
        log('Public source cooldown; pending',len(pending))
        if seeded:publish(posts,old)
        return
    done=0;added=0
    for i,p in ready[:args.limit]:
        try:
            updated=complete(p)
            posts[i]=updated
            if updated.get('media_unavailable'):failures[p['id']]={'at':now,'reason':'Video unavailable'}
            else:failures.pop(p['id'],None)
            done+=1;added+=len(updated['images'])-len(p['images'])
            log('Verified',p['id'],'photos',len(updated['images']),'videos',updated.get('video_count',0))
        except AccessBlocked as exc:
            failures[p['id']]={'at':now,'reason':str(exc)}
            state['blocked_until']=time.time()+86400
            log('Source blocked; stopping batch',str(exc));break
        except Exception as exc:
            failures[p['id']]={'at':now,'reason':str(exc)[:200]}
            log('Unavailable',p['id'],str(exc)[:180])
        time.sleep(1.2)
    state['failures']=failures
    state['checked_at']=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')
    state['pending']=sum((p.get('media_checked') is False or p.get('media_unavailable',0)>0) and not p.get('editor_images_locked') for p in posts)
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    publish(posts,old)
    log('Batch complete: seeded',seeded,'verified',done,'net new photos',added,'pending',state['pending'])

if __name__=='__main__':main()
