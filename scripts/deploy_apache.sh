#!/usr/bin/env bash
# Publish the public files from the same checkout used by GitHub Pages and Codex.
# Do not serve private Git, Codex scripts, checkpoint IDs, or log files.
set -Eeuo pipefail
SOURCE=/home/ljs1092/jaram-miri-profile
DESTINATION=/var/www/jaram-miri

[[ -f "$SOURCE/index.html" && -f "$SOURCE/activities.html" && -f "$SOURCE/data/gallery.json" ]] || {
  echo 'JARAM deployment blocked: website source is incomplete' >&2; exit 1;
}
[[ -d "$DESTINATION/.well-known/acme-challenge" ]] || {
  echo 'JARAM deployment blocked: TLS challenge directory is missing' >&2; exit 1;
}
[[ "$(git -C "$SOURCE" branch --show-current)" == 'main' ]] || {
  echo 'JARAM deployment blocked: repository is not on main' >&2; exit 1;
}
[[ -z "$(git -C "$SOURCE" status --porcelain)" ]] || {
  echo 'JARAM deployment skipped: local repository has uncommitted changes' >&2; exit 1;
}

# Pick up commits pushed from other machines without replacing local edits.
git -C "$SOURCE" pull --ff-only --quiet origin main

# Publication allowlist: protect the SSL verification folder and exclude all
# private workspace content. An excluded file cannot be created on the webroot.
rsync -a --delete \
  --filter='P /.well-known/***' \
  --filter='P /secret/***' \
  --filter='P /preview/***' \
  --filter='P /board/***' \
  --include='/*.html' \
  --include='/*.css' \
  --include='/*.js' \
  --include='/robots.txt' \
  --include='/*.txt' \
  --include='/sitemap.xml' \
  --include='/assets/***' \
  --include='/data/' \
  --include='/data/gallery.json' \
  --exclude='*' \
  "$SOURCE/" "$DESTINATION/"

# This host has its own public hostname; the repo remains the primary source.
# Change absolute canonical/share links only on the deployed copy.
python3 - "$DESTINATION" <<'PY'
from pathlib import Path
import sys
root = Path(sys.argv[1])
for name in ('index.html','activities.html','credits.html','sitemap.xml','robots.txt'):
    path = root / name
    if path.is_file():
        text = path.read_text(encoding='utf-8')
        text = text.replace('https://jungsuplee-hub.github.io/jaram_miri/', 'https://jaram-miri.kro.kr/')
        path.write_text(text, encoding='utf-8')
PY
chmod -R a+rX "$DESTINATION"

python3 - "$DESTINATION" <<'PY'
from pathlib import Path
import json,sys
from bs4 import BeautifulSoup
root=Path(sys.argv[1])
site=BeautifulSoup((root/'index.html').read_text(encoding='utf-8'),'html.parser')
assert len(site.select('.hero-desc-line')) == 2, 'Hero text was not updated'
assert len(site.select('#home-audiences .home-audience-card')) == 6, 'Audience section was not updated'
assert len(json.loads((root/'data/gallery.json').read_text(encoding='utf-8'))) == len(site.select('[data-gallery-card]')), 'Gallery mismatch'
assert not (root/'data/instagram-known.json').exists(), 'Private checkpoint must not be published'
assert not (root/'.git').exists(), 'Git internals must not be published'
assert (root/'secret/index.php').is_file(), 'Private administrator page must be preserved'
assert (root/'board/index.php').is_file(), 'Public community board must be preserved'
assert (root/'secret/community.php').is_file(), 'Community administration must be preserved'
assert (root/'preview').is_dir(), 'Approved preview directory must not be deleted by deploy'
print('JARAM Apache publish verified:', root)
PY

# Inform participating search engines only when canonical sitemap changed.
# Failed notifications never roll back a successful website publication.
/usr/bin/python3 "$SOURCE/scripts/notify_indexnow.py" || echo "IndexNow notification could not be completed; site remains deployed" >&2
