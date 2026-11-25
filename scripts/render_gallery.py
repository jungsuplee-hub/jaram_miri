#!/usr/bin/env python3
"""Generate four-at-a-time homepage gallery and category-indexed archive from curated photos."""
from pathlib import Path
from collections import Counter
from html import escape
import json,re

ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/'index.html'
ARCHIVE=ROOT/'activities.html'
DATA=ROOT/'data/gallery.json'

GROUPS=[
 ('장애인 원예치료','장애인 원예치료','주간보호센터와 장애인 대상 맞춤 원예 프로그램'),
 ('어르신 돌봄','어르신 돌봄','복지관·노인요양시설·어르신 마음돌봄 프로그램'),
 ('치매·인지지원','치매 예방·인지지원','치매안심센터와 인지활동 연계 프로그램'),
 ('어르신 원예활동','어르신 원예활동','어르신 반려식물·가드닝 프로그램'),
 ('직장인 정서지원','직장인 정서지원','직무스트레스 관리와 감정노동자 마음돌봄 프로그램'),
 ('아동·청소년 원예교육','아동·청소년 원예교육','학교·Wee클래스·교육지원청·아동시설 원예교육 프로그램'),
 ('가족·지역사회 원예교육','가족·지역사회 원예교육','가족 참여와 주민 대상의 원예교육·체험 활동'),
 ('강사·전문인력 교육','전문인력 양성·강연','강사 양성과정·워크숍·교수 및 강연 현장'),
 ('원예치료','기타 원예치료','활동 기록으로 확인되는 원예치료 현장'),
]

def card(post, home=False, i=0):
 p=post
 hidden=' hidden' if home and i>=4 else ''
 cls='field-card reveal'+(' archive-card' if not home else '')
 return '''<article class="{cls}" data-gallery-card data-gallery-id="{id}" data-gallery-year="{year}"{hidden}>
 <button type="button" class="field-photo photo-open" data-gallery-open="{id}" aria-label="{title} 사진 자세히 보기">
 <img src="{image}?v=6" width="900" height="900" loading="lazy" decoding="async" alt="{title} 현장 사진">
 <span class="photo-photo-overlay">사진 보기 <span aria-hidden="true">↗</span></span>
 <span class="photo-fallback" hidden>사진을 불러오지 못했습니다.</span></button>
 <div class="field-info"><span class="field-date">{date} · {category}</span><h4>{title}</h4><p>{summary}</p>
 <button class="field-detail-button" type="button" data-gallery-open="{id}">사진과 내용 자세히 보기 <span aria-hidden="true">↗</span></button></div>
 </article>'''.format(cls=cls,id=escape(p['id'],quote=True),year=escape(p['date'][:4]),hidden=hidden,
    title=escape(p['title']),image=escape(p['images'][0],quote=True),date=escape(p['date']),category=escape(p['category']),summary=escape(p['summary']))

def payload(posts):
 return json.dumps(posts,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')

def page_head(home):
 head=home[home.index('<head>'):home.index('</head>')+7]
 head=re.sub(r'\s*<script[^>]*id="site-structured-data"[^>]*>.*?</script>', '', head, flags=re.I|re.S)
 head=head.replace('<meta name="description" content="자람원예치료연구소 | 꽃과 식물이 전하는 회복과 성장. 맞춤형 원예치료, 실제 활동 사례, 원예교육, 원예키트 문의, 프로그램 컨설팅.">',
 '<meta name="description" content="자람원예치료연구소의 실제 원예치료 현장을 프로그램 유형별로 살펴보세요. 장애인·어르신·치매안심센터 활동 사진과 기록.">')
 head=head.replace('자람원예치료연구소 | 식물이 자라는 시간, 마음도 함께 자랍니다','원예치료 프로그램별 활동 사진 | 자람원예치료연구소')
 head=head.replace('<title>자람원예치료연구소 | JARAM Horticultural Therapy</title>','<title>프로그램별 실제 활동 사진 | 자람원예치료연구소</title>')
 head=head.replace('https://jungsuplee-hub.github.io/jaram_miri/"','https://jungsuplee-hub.github.io/jaram_miri/activities.html"')
 head=head.replace('  <link rel="stylesheet" href="main-profile.css?v=20261121-2">\n','')
 head=head.replace('href="styles.css"','href="styles.css"')
 head=head.replace('gallery.css?v=20261121-5','gallery.css?v=20261125-caption4')
 head=head.replace('script.js?v=20261121-5','script.js?v=20261125-caption4')
 head=head.replace('<script src="script.js?v=20261125-caption4" defer></script>','<link rel="stylesheet" href="activities-full.css?v=20261125-grid3">\n  <script src="script.js?v=20261125-caption4" defer></script>\n  <script src="activities-full.js?v=20261121-7" defer></script>')
 # Keep canonical and OpenGraph URLs correct whenever the Instagram gallery
 # renderer rebuilds the archive page from the homepage HTML head.
 head=re.sub(r'<meta\s+name="description"[^>]*>', '<meta name="description" content="자람원예치료연구소의 실제 현장 기록. 장애인 원예치료, 어르신 돌봄, 치매·인지지원, 아동·청소년 원예교육, 강사 연수 등 프로그램별 사진과 활동 내용을 확인하세요.">', head, count=1)
 for prop,content in (
  ('og:title','원예치료·원예교육 실제 활동 사진 | 자람원예치료연구소'),
  ('og:description','학교·복지기관·치매안심센터 등 다양한 현장의 원예치료 및 원예교육 활동 사례와 사진.'),
  ('og:url','https://jaram-miri.kro.kr/activities.html'),
 ):
  head=re.sub(r'<meta\s+property="'+re.escape(prop)+r'"[^>]*>',lambda m:'<meta property="'+prop+'" content="'+content+'">',head,count=1)
 head=re.sub(r'<link\s+rel="canonical"[^>]*>', '<link rel="canonical" href="https://jaram-miri.kro.kr/activities.html">',head,count=1)
 return head

def page_nav(home):
 header=home[home.index('<header class="site-header"'):home.index('</header>')+9]
 for fragment in ('#about','#programs','#kits','#activities','#publication','#story','#director'):
  header=header.replace('href="'+fragment+'"','href="index.html'+fragment+'"')
 header=header.replace('href="#top"','href="index.html"')
 header=header.replace('href="index.html#activities"','href="activities.html"')
 return header

def page_footer(home):
 footer=home[home.index('<footer class="site-footer"'):home.index('</footer>')+9]
 for fragment in ('#about','#programs','#kits','#activities','#publication','#story','#director'):
  footer=footer.replace('href="'+fragment+'"','href="index.html'+fragment+'"')
 footer=footer.replace('href="index.html#activities"','href="activities.html"')
 return footer

def page_dialog(home):
 return home[home.index('<dialog id="photo-dialog"'):home.index('</dialog>')+9]

def main():
 posts=json.loads(DATA.read_text(encoding='utf-8'))
 assert len(posts)==len({p['id'] for p in posts}), 'Duplicate post ids'
 assert all((ROOT/path).is_file() for p in posts for path in p['images']), 'Image missing'
 home=INDEX.read_text(encoding='utf-8')
 # Replace the entire generated gallery region, including legacy duplicated year controls.
 first=home.find('<div class="gallery-year-filter"')
 if first<0:first=home.index('<div class="field-gallery" id="field-gallery"')
 start=home.rfind('\n',0,first)+1
 end=home.index('<div class="historical-heading',start)
 home_body='''        <div class="field-gallery" id="field-gallery" aria-label="자람의 원예치료 활동 사진">
'''+ '\n'.join(card(p,home=True,i=i) for i,p in enumerate(posts))+'''
        </div>
        <div class="gallery-controls gallery-controls-split">
          <button id="gallery-toggle" class="gallery-show-more" type="button" aria-controls="field-gallery" aria-expanded="false">
            <span>4개 더보기</span><small>4 / {n}</small><span class="gallery-toggle-icon" aria-hidden="true">↓</span>
          </button>
          <a class="gallery-archive-link" href="activities.html">프로그램별 전체 활동 보기 <span aria-hidden="true">↗</span></a>
        </div>
        '''.format(n=len(posts))
 home=home[:start]+home_body+home[end:]
 home=re.sub(r'(<script type="application/json" id="photo-gallery-data">).*?(</script>)',lambda m:m.group(1)+payload(posts)+m.group(2),home,flags=re.S)
 home=home.replace('gallery.css?v=20261121-5','gallery.css?v=20261125-caption4').replace('script.js?v=20261121-5','script.js?v=20261125-caption4')
 if 'id="photo-dialog-source"' not in home:
  home=home.replace('        <div class="photo-dialog-caption-wrap" id="photo-dialog-caption-wrap">','        <a id="photo-dialog-source" class="photo-dialog-source" href="https://www.instagram.com/jaram_miri/" target="_blank" rel="noopener noreferrer">인스타그램 원문 보기 ↗</a>\n        <div class="photo-dialog-caption-wrap" id="photo-dialog-caption-wrap">')
 INDEX.write_text(home,encoding='utf-8')
 # Category-specific full gallery: each record appears in its own grounded type.
 types=Counter(p['category'] for p in posts)
 groups=[(k,label,subtitle) for k,label,subtitle in GROUPS if types.get(k)]
 groups += [(k,k,'원예치료 현장 기록') for k in sorted(types) if k not in {g[0] for g in groups}]
 buttons=['<button type="button" class="archive-filter is-active" data-category="all" aria-pressed="true">전체 활동 <span>'+str(len(posts))+'</span></button>']
 buttons += ['<button type="button" class="archive-filter" data-category="'+escape(cat,quote=True)+'" aria-pressed="false">'+escape(label)+' <span>'+str(types[cat])+'</span></button>' for cat,label,_ in groups]
 years=sorted({p['date'][:4] for p in posts},reverse=True)
 options=''.join('<option value="'+year+'">'+year+'년</option>' for year in years)
 blocks=[]
 for key,title,desc in groups:
  items=sorted((p for p in posts if p['category']==key),key=lambda x:x['date'],reverse=True)
  blocks.append('''<section class="archive-section" data-archive-group="{cat}" aria-label="{name}">
    <div class="archive-section-heading"><div><span>JARAM FIELD NOTES</span><h2>{name}</h2><p>{desc}</p></div><strong class="archive-section-count">{num}<small> CASES</small></strong></div>
    <div class="field-gallery archive-grid">{cards}</div></section>'''.format(cat=escape(key,quote=True),name=escape(title),desc=escape(desc),num=len(items),cards='\n'.join(card(p) for p in items)))
 dialog=page_dialog(home)
 footer=page_footer(home)
 archive='''<!doctype html><html lang="ko">'''+page_head(home)+'''<body class="archive-page">
 <a class="skip-link" href="#main">본문으로 바로가기</a>
 '''+page_nav(home)+'''
 <main id="main">
 <section class="archive-hero"><div class="container">
   <a class="archive-back" href="index.html#activities">← 연구소 소개로 돌아가기</a>
   <div class="archive-hero-grid"><div><span class="archive-overline">JARAM · PROGRAM ARCHIVE</span>
   <h1>식물과 함께한<br><em>모든 현장의 기록.</em></h1>
   <p>자람원예치료연구소가 공개한 활동 중 프로그램의 대상과 현장 내용이 확인되는 사례를 엄선했습니다. 장애인·어르신 원예치료와 학교·아동청소년 원예교육, 전문인력 교육을 포함하되 개인 일상·단순 모집 공지 등은 제외했습니다.</p>
   </div><div class="archive-hero-stat"><span>ACTIVITY ARCHIVE</span><strong>'''+str(len(posts))+'''</strong><small>선별된 실제 활동 기록 · '''+str(sum(len(p['images']) for p in posts))+'''장의 사진</small></div></div>
 </div></section>
 <section class="archive-content container" aria-labelledby="archive-content-title">
  <div class="archive-content-heading"><div><span>EXPLORE THE PROGRAMS</span><h2 id="archive-content-title">프로그램 유형별 <em>활동 사례</em></h2></div><p>유형이나 연도를 선택하면 관련 현장만 표시됩니다.</p></div>
  <div class="archive-controls" aria-label="활동 분류"><div class="archive-filters" role="group" aria-label="프로그램 유형 선택">'''+''.join(buttons)+'''</div>
   <div class="archive-options"><label for="archive-year">활동 연도</label><select id="archive-year" aria-label="활동 연도"><option value="all">전체 기간</option>'''+options+'''</select></div></div>
  <p class="archive-result" id="archive-result" role="status" aria-live="polite">총 '''+str(len(posts))+'''건의 활동 사례</p>
  <div id="archive-groups">'''+''.join(blocks)+'''</div>
  <div class="archive-empty" id="archive-empty" hidden>선택한 유형과 연도에 해당하는 활동이 없습니다. 다른 조건을 선택해 주세요.</div>
  <div class="archive-bottom"><a href="index.html#activities">← 연구소 소개로 돌아가기</a><a href="https://www.instagram.com/jaram_miri/" target="_blank" rel="noopener noreferrer">인스타그램에서 더 보기 ↗</a></div>
 </section></main>
 '''+footer+'\n'+dialog+'\n<script type="application/json" id="photo-gallery-data">'+payload(posts)+'</script>\n</body></html>'
 ARCHIVE.write_text(archive,encoding='utf-8')
 print('generated',len(posts),'cases',sum(len(p['images']) for p in posts),'photos','categories',dict(types))
 # Rebuild image sitemap + per-page organization/FAQ schema after every update.
 import subprocess,sys
 subprocess.run([sys.executable,str(ROOT/'scripts/update_search.py')],check=True)

if __name__=='__main__':main()
