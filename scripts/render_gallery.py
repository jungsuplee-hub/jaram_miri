#!/usr/bin/env python3
"""Regenerate the portfolio cards and modal data from verified public posts."""
from pathlib import Path
import json,html,re
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/'index.html'
DATA=ROOT/'data/gallery.json'

def escape(v):return html.escape(str(v),quote=True)

def main():
 posts=json.loads(DATA.read_text(encoding='utf-8'))
 assert len(posts)==len({p['id'] for p in posts}), 'Duplicate posts'
 for p in posts:
  for asset in p['images']:
   assert (ROOT/asset).is_file(), 'Missing image: '+asset
 counts=Counter(p["date"][:4] for p in posts)
 years=sorted(counts,reverse=True)
 cards=[]
 for ix,p in enumerate(posts):
  card='''          <article class="field-card reveal" data-gallery-card data-gallery-id="{id}" data-gallery-year="{year}"{hidden}>
            <button type="button" class="field-photo photo-open" data-gallery-open="{id}" aria-label="{title} 사진 자세히 보기">
              <img src="{image}?v=4" width="900" height="900" loading="lazy" decoding="async" alt="{title} 활동 사진">
              <span class="photo-photo-overlay">사진 보기 <span aria-hidden="true">↗</span></span>
              <span class="photo-fallback" hidden>사진을 불러오지 못했습니다.</span>
            </button>
            <div class="field-info">
              <span class="field-date">{date} · {category}</span>
              <h4>{title}</h4>
              <p>{summary}</p>
              <button class="field-detail-button" type="button" data-gallery-open="{id}">사진과 내용 자세히 보기 <span aria-hidden="true">↗</span></button>
            </div>
          </article>'''.format(id=escape(p['id']),hidden=' hidden' if ix>=4 else '',title=escape(p['title']),image=escape(p['images'][0]),date=escape(p['date']),year=escape(p['date'][:4]),category=escape(p['category']),summary=escape(p['summary']))
  cards.append(card)
 filter_items=''.join('<button class="gallery-year-button" type="button" data-gallery-year-button="'+escape(year)+'" aria-pressed="false">'+escape(year)+' <span>'+str(counts[year])+'</span></button>' for year in years)
 filter_markup='<div class="gallery-year-filter" id="gallery-year-filter" role="group" aria-label="활동 연도별 보기" hidden><span class="gallery-year-label">연도별 활동</span><button class="gallery-year-button is-active" type="button" data-gallery-year-button="all" aria-pressed="true">전체 <span>'+str(len(posts))+'</span></button>'+filter_items+'</div>\n'
 body=filter_markup+'''        <div class="field-gallery" id="field-gallery" aria-label="자람의 실제 활동 사진">
'''+ '\n'.join(cards) +'''\n        </div>
        <div class="gallery-controls">
          <button id="gallery-toggle" class="gallery-show-more" type="button" aria-controls="field-gallery" aria-expanded="false">
            <span>전체 활동 보기</span><small>{shown} / {total}</small><span class="gallery-toggle-icon" aria-hidden="true">↓</span>
          </button>
        </div>
        <noscript><style>.field-card[hidden]{{display:grid!important}}.gallery-controls{{display:none!important}}</style></noscript>
'''.format(shown=min(4,len(posts)),total=len(posts))
 s=INDEX.read_text(encoding='utf-8')
 begin=s.index('        <div class="field-gallery" id="field-gallery"')
 end=s.index('        <div class="historical-heading reveal">',begin)
 s=s[:begin]+body+s[end:]
 m=re.compile(r'(<script type="application/json" id="photo-gallery-data">)(.*?)(</script>)',re.S)
 payload=json.dumps(posts,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
 assert len(m.findall(s))==1
 s=m.sub(lambda mat:mat.group(1)+payload+mat.group(3),s,count=1)
 INDEX.write_text(s,encoding='utf-8')
 print('rendered',len(posts),'posts',sum(len(p['images']) for p in posts),'photos')
if __name__=='__main__':main()
