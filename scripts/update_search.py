#!/usr/bin/env python3
"""Build canonical SEO, factual JSON-LD, robots and image sitemap for JARAM.

Run after render_gallery.py whenever new curated field cases are added.
The .kro.kr Apache domain is canonical; the GitHub Pages mirror points to it.
"""
from __future__ import annotations
from collections import Counter
from datetime import datetime
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = 'https://jaram-miri.kro.kr/'
INSTAGRAM = 'https://www.instagram.com/jaram_miri/'
CONTACT = 'https://business.inpock.co.kr/form?partner=ymr13'
IMAGE_NS = 'http://www.google.com/schemas/sitemap-image/1.1'
SITEMAP_NS = 'http://www.sitemaps.org/schemas/sitemap/0.9'

PAGE_META = {
    'index.html': {
        'canonical': DOMAIN,
        'title': '자람원예치료연구소 | 원예치료·원예교육·맞춤형 원예키트',
        'description': '유미리 대표의 자람원예치료연구소. 아동·청소년·어르신·장애인 대상 맞춤 원예치료, 학교 원예교육, 전문인력 교육, 원예활동 키트·컨설팅 및 실제 활동 사진을 소개합니다.',
        'og_description': '대상자에 맞춘 원예치료·원예교육·활동 키트와 실제 현장 사례를 확인하세요.',
    },
    'activities.html': {
        'canonical': DOMAIN + 'activities.html',
        'title': '원예치료·원예교육 실제 활동 사진 | 자람원예치료연구소',
        'description': '자람원예치료연구소의 실제 현장 기록. 장애인 원예치료, 어르신 돌봄, 치매·인지지원, 아동·청소년 원예교육, 강사 연수 등 프로그램별 사진과 활동 내용을 확인하세요.',
        'og_description': '학교·복지기관·치매안심센터 등 다양한 현장의 원예치료 및 원예교육 활동 사례와 사진.',
    },
    'faq.html': {
        'canonical': DOMAIN + 'faq.html',
        'title': '원예치료·원예교육·원예키트 FAQ | 자람원예치료연구소',
        'description': '자람원예치료연구소의 대상자 맞춤 원예치료, 학교 원예교육, 어르신 돌봄, 키트 제작, 강사 연수 및 컨설팅 상담에 관한 자주 묻는 질문.',
        'og_description': '원예치료 프로그램과 원예키트, 상담 방법에 관한 궁금한 점을 확인하세요.',
    },
    'credits.html': {
        'canonical': DOMAIN + 'credits.html',
        'title': '활동 사진·저서 자료 출처 | 자람원예치료연구소',
        'description': '자람원예치료연구소 홈페이지의 원예치료 현장 사진, 『행복 자람 원예교실』 도서와 경력 정보의 출처 및 이미지 사용 안내.',
        'og_description': '원예치료 현장 사진과 저서·연구소 소개에 사용된 공개 자료의 출처 안내.',
    },
}


def schema_graph(page: str, posts: list[dict]) -> dict:
    organization = {
        '@type': 'Organization', '@id': DOMAIN + '#organization',
        'name': '자람원예치료연구소',
        'alternateName': 'JARAM Horticultural Therapy Lab',
        'url': DOMAIN,
        'description': '참여자에 맞춘 원예치료와 원예교육, 맞춤형 원예활동 키트 및 원예치료 컨설팅을 소개하는 연구소.',
        'logo': {'@type': 'ImageObject', 'url': DOMAIN + 'assets/jaram-instagram-logo.png'},
        'image': DOMAIN + 'assets/og-cover.png',
        'telephone': '+82-10-9566-5407',
        'email': 'ymr13@daum.net',
        'sameAs': [INSTAGRAM],
        'contactPoint': {
            '@type': 'ContactPoint', 'contactType': 'program inquiries',
            'telephone': '+82-10-9566-5407', 'email': 'ymr13@daum.net',
            'url': CONTACT, 'availableLanguage': ['ko'],
        },
    }
    website = {
        '@type': 'WebSite', '@id': DOMAIN + '#website',
        'name': '자람원예치료연구소', 'url': DOMAIN,
        'inLanguage': 'ko-KR', 'publisher': {'@id': DOMAIN + '#organization'},
    }
    m = PAGE_META[page]
    sitepage = {
        '@type': 'WebPage', '@id': m['canonical'] + '#webpage',
        'name': m['title'], 'description': m['description'],
        'url': m['canonical'], 'inLanguage': 'ko-KR',
        'isPartOf': {'@id': DOMAIN + '#website'},
        'about': {'@id': DOMAIN + '#organization'},
    }
    graph = [organization, website, sitepage]
    if page == 'index.html':
        for name, service in (
            ('대상자 맞춤 프로그램', '대상자 특성에 맞춘 원예치료 및 원예활동 프로그램'),
            ('교육 및 전문가 양성', '학교·복지기관 원예교육과 강사·전문인력 교육'),
            ('맞춤형 원예활동 키트', '기관의 목적과 대상에 맞춘 원예활동 키트 구성·제작'),
            ('원예치료 컨설팅', '참여자·운영 목적·현장 여건에 맞춘 원예치료 상담'),
        ):
            graph.append({
                '@type': 'Service', 'name': name, 'serviceType': service,
                'provider': {'@id': DOMAIN + '#organization'},
            })
        graph.append({
            '@type': 'Book', 'name': '행복 자람 원예교실',
            'author': [{'@type': 'Person', 'name': x} for x in ('유미리', '이영기', '손장호')],
            'publisher': {'@type': 'Organization', 'name': '교우미디어'},
            'datePublished': '2022-05-25',
            'isbn': '9791185417424',
            'inLanguage': 'ko-KR',
            'url': 'https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=295674275',
        })
    if page == 'activities.html':
        summary = Counter(item['category'] for item in posts)
        graph[2]['@type'] = 'CollectionPage'
        graph[2]['mainEntity'] = {
            '@type': 'ItemList', 'name': '자람원예치료연구소 프로그램별 실제 활동 사례',
            'numberOfItems': len(posts),
            'itemListElement': [
                {'@type': 'ListItem', 'position': i,
                 'name': f'{category} 활동 {count}건',
                 'url': DOMAIN + 'activities.html'}
                for i,(category,count) in enumerate(summary.items(), 1)
            ],
        }
    if page == 'faq.html':
        soup=BeautifulSoup((ROOT/page).read_text(encoding='utf-8'), 'html.parser')
        questions=[]
        for article in soup.select('.faq-item'):
            q=article.find('h3')
            answer=article.find('p')
            if q and answer:
                questions.append({
                    '@type': 'Question','name': q.get_text(' ',strip=True),
                    'acceptedAnswer': {'@type': 'Answer', 'text': answer.get_text(' ',strip=True)},
                })
        graph[2]['@type'] = 'FAQPage'
        graph[2]['mainEntity'] = questions
    return {'@context': 'https://schema.org', '@graph': graph}


def set_tag(head: str, pattern: str, markup: str) -> str:
    result, count = re.subn(pattern, lambda _: markup, head, count=1, flags=re.I|re.S)
    if count == 0:
        result = result.replace('</head>', '  ' + markup + '\n</head>')
    return result


def update_page_head(page: str, posts: list[dict]) -> None:
    filename=ROOT/page
    body=filename.read_text(encoding='utf-8')
    before, sep, after=body.partition('</head>')
    if not sep:
        raise RuntimeError(f'Missing document head: {page}')
    head=before+'</head>'
    m=PAGE_META[page]
    head=re.sub(r'\s*<script[^>]*id="site-structured-data"[^>]*>.*?</script>', '', head, flags=re.S|re.I)
    updates = [
        (r'<title\b[^>]*>.*?</title>', f'<title>{m["title"]}</title>'),
        (r'<meta\s+name="description"[^>]*>', f'<meta name="description" content="{m["description"]}">'),
        (r'<meta\s+name="robots"[^>]*>', '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">'),
        (r'<link\s+rel="canonical"[^>]*>', f'<link rel="canonical" href="{m["canonical"]}">'),
        (r'<meta\s+property="og:type"[^>]*>', '<meta property="og:type" content="website">'),
        (r'<meta\s+property="og:locale"[^>]*>', '<meta property="og:locale" content="ko_KR">'),
        (r'<meta\s+property="og:site_name"[^>]*>', '<meta property="og:site_name" content="자람원예치료연구소">'),
        (r'<meta\s+property="og:title"[^>]*>', f'<meta property="og:title" content="{m["title"]}">'),
        (r'<meta\s+property="og:description"[^>]*>', f'<meta property="og:description" content="{m["og_description"]}">'),
        (r'<meta\s+property="og:url"[^>]*>', f'<meta property="og:url" content="{m["canonical"]}">'),
        (r'<meta\s+property="og:image"[^>]*>', f'<meta property="og:image" content="{DOMAIN}assets/og-cover.png">'),
        (r'<meta\s+name="twitter:card"[^>]*>', '<meta name="twitter:card" content="summary_large_image">'),
    ]
    for pattern, tag in updates:
        head=set_tag(head,pattern,tag)
    ldjson=json.dumps(schema_graph(page,posts),ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    head=head.replace('</head>',f'<script type="application/ld+json" id="site-structured-data">{ldjson}</script>\n</head>')
    revised=head+after
    if revised!=body:
        filename.write_text(revised,encoding='utf-8')


def update_sitemap(posts: list[dict]):
    ET.register_namespace('',SITEMAP_NS)
    ET.register_namespace('image',IMAGE_NS)
    sitemap=ET.Element(f'{{{SITEMAP_NS}}}urlset')
    for filename in PAGE_META:
        path=ROOT/filename
        if not path.is_file():
            raise RuntimeError('Missing public page: '+filename)
        entry=ET.SubElement(sitemap,f'{{{SITEMAP_NS}}}url')
        ET.SubElement(entry,f'{{{SITEMAP_NS}}}loc').text=PAGE_META[filename]['canonical']
        modified=datetime.fromtimestamp(path.stat().st_mtime).astimezone().date().isoformat()
        ET.SubElement(entry,f'{{{SITEMAP_NS}}}lastmod').text=modified
        if filename=='activities.html':
            seen=set()
            for post in posts:
                for relative in post.get('images',[]):
                    path_str=str(relative)
                    if path_str in seen:
                        continue
                    if not path_str.startswith('assets/instagram/') or '..' in Path(path_str).parts:
                        raise RuntimeError('Unsafe image URL in activity data')
                    image_file=ROOT/path_str
                    if not image_file.is_file():
                        raise RuntimeError('Activity sitemap image does not exist: '+path_str)
                    seen.add(path_str)
                    extension=ET.SubElement(entry,f'{{{IMAGE_NS}}}image')
                    ET.SubElement(extension,f'{{{IMAGE_NS}}}loc').text=DOMAIN+quote(path_str,safe='/._-')
    notice=ET.SubElement(sitemap,f'{{{SITEMAP_NS}}}url')
    ET.SubElement(notice,f'{{{SITEMAP_NS}}}loc').text=DOMAIN+'board/?type=notice'
    xml=ET.tostring(sitemap,encoding='utf-8',xml_declaration=True)
    (ROOT/'sitemap.xml').write_bytes(xml)


def main():
    posts=json.loads((ROOT/'data/gallery.json').read_text(encoding='utf-8'))
    if not isinstance(posts,list):
        raise RuntimeError('Invalid activity archive JSON')
    for page in PAGE_META:
        update_page_head(page,posts)
    update_sitemap(posts)
    (ROOT/'robots.txt').write_text(
        'User-agent: *\nAllow: /\nDisallow: /secret/\nDisallow: /preview/\n'
        f'Sitemap: {DOMAIN}sitemap.xml\n',encoding='utf-8'
    )
    (ROOT/'llms.txt').write_text('''# 자람원예치료연구소 (JARAM Horticultural Therapy Lab)

> 한국어 원예치료·원예교육·맞춤형 원예활동 키트 및 컨설팅을 소개하는 연구소 사이트입니다. 대표 유미리. 운영 사이트: https://jaram-miri.kro.kr/

## 공식 콘텐츠
- [공지사항](https://jaram-miri.kro.kr/board/?type=notice): 연구소 공식 소식과 안내
- [연구소 소개와 프로그램](https://jaram-miri.kro.kr/): 연구소 소개, 대상자 맞춤 원예치료, 교육 및 전문가 양성, 원예활동 키트, 컨설팅, 소장·경력 및 연락처
- [실제 원예치료·원예교육 활동 기록](https://jaram-miri.kro.kr/activities.html): 장애인·어르신·치매·인지지원·학교·아동청소년 및 강사 교육 활동 사진과 사례
- [자주 묻는 질문](https://jaram-miri.kro.kr/faq.html): 프로그램 대상, 교육 운영, 원예키트, 컨설팅, 문의 방법
- [자료 및 이미지 출처](https://jaram-miri.kro.kr/credits.html): 사진과 대표 저서 및 공개 근거 안내
- [공식 인스타그램](https://www.instagram.com/jaram_miri/): 연구소가 공개한 활동 기록

## 문의
- 전화: 010-9566-5407
- 이메일: ymr13@daum.net
- 공식 프로그램 문의: https://business.inpock.co.kr/form?partner=ymr13

## 참고
- 활동별 내용과 사진은 공개된 현장 사례를 기반으로 하며, 개별 프로그램의 일정·가격·성과를 보장하지 않습니다.
- 검색용 대표 주소는 https://jaram-miri.kro.kr/ 입니다. 비공개 관리 페이지와 난수 미리보기는 공식 검색 콘텐츠에 포함되지 않습니다.
- 이 문서는 기계가 공식 공개 페이지를 찾는 데 도움을 주기 위한 안내입니다. 검색엔진 또는 AI 서비스의 색인·노출을 보장하지 않습니다.
''',encoding='utf-8')
    print(f'SEO metadata: {len(PAGE_META)} pages; sitemap: {len(posts)} cases / {sum(len(x.get("images",[])) for x in posts)} pictures; canonical={DOMAIN}')


if __name__ == '__main__':
    main()
