#!/usr/bin/env python3
"""Notify IndexNow search engines when a public JARAM sitemap changes.

IndexNow is a discovery notification, not a guarantee of indexing or ranking.
Uses the public site root key and only canonical URLs, never private URLs.
"""
from __future__ import annotations
from pathlib import Path
from hashlib import sha256
from urllib.parse import urlparse
import json
import sys
import xml.etree.ElementTree as ET
import requests

ROOT=Path(__file__).resolve().parents[1]
BASE='https://jaram-miri.kro.kr/'
SITEMAP=ROOT/'sitemap.xml'
STATE=ROOT/'.cache/indexnow-last-success.json'
NS={'s':'http://www.sitemaps.org/schemas/sitemap/0.9'}


def main():
    keyfiles=[file for file in ROOT.glob('*.txt')
              if len(file.stem)==32 and set(file.stem).issubset(set('0123456789abcdef'))
              and file.read_text(encoding='utf-8').strip()==file.stem]
    if len(keyfiles)!=1:
        raise RuntimeError('Expected one valid public IndexNow key file')
    keyfile=keyfiles[0]
    doc=ET.parse(SITEMAP)
    urls=[(node.text or '').strip() for node in doc.findall('.//s:url/s:loc',NS)]
    if len(urls)!=len(set(urls)) or not urls:
        raise RuntimeError('Invalid or duplicated canonical URL list')
    if any(urlparse(u).scheme!='https' or urlparse(u).netloc!='jaram-miri.kro.kr'
           or '/secret/' in u or '/preview/' in u for u in urls):
        raise RuntimeError('Refusing to notify nonpublic or noncanonical URLs')
    digest=sha256(SITEMAP.read_bytes()).hexdigest()
    if STATE.exists():
        old=json.loads(STATE.read_text(encoding='utf-8'))
        if old.get('digest')==digest:
            print('IndexNow unchanged; skip notification')
            return
    key_url=BASE+keyfile.name
    verification=requests.get(key_url,timeout=10)
    if verification.status_code!=200 or verification.text.strip()!=keyfile.stem:
        raise RuntimeError('Public ownership key is not available at the canonical domain')
    data={'host':'jaram-miri.kro.kr','key':keyfile.stem,
          'keyLocation':key_url,'urlList':urls}
    response=requests.post('https://api.indexnow.org/indexnow',json=data,timeout=16,
                           headers={'User-Agent':'JaramHorticulturalTherapySite/1.0'})
    print('IndexNow returned',response.status_code,'for',len(urls),'public URLs')
    if response.status_code not in (200,202):
        raise RuntimeError('IndexNow did not accept the URL notification: HTTP '+str(response.status_code))
    STATE.parent.mkdir(parents=True,exist_ok=True)
    STATE.write_text(json.dumps({'digest':digest,'status':response.status_code,'urls':urls},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        print('IndexNow notification skipped:',str(error)[:250],file=sys.stderr)
        sys.exit(1)
