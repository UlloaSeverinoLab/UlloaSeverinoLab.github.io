"""
Weekly sync of citation and publication counts.
Sources: OpenAlex (citations) + ORCID (publication count).
Saves result to data/scholar.json so the website always has
an up-to-date fallback even if live API calls fail.
"""

import urllib.request, json, os, datetime

ORCID   = '0000-0003-3725-9713'
OA_MAIL = 'mailto=francesco.ulloa@cajal.csic.es'

def fetch(url, accept=None):
    headers = {'User-Agent': 'ScholarSync/1.0'}
    if accept:
        headers['Accept'] = accept
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

# ── Load existing values as safe fallback ──────────────────────────
existing = {'citations': 0, 'publications': 0}
try:
    with open('data/scholar.json') as f:
        existing = json.load(f)
except Exception:
    pass

# ── Publications from ORCID ────────────────────────────────────────
pub_count = existing['publications']
try:
    data = fetch(f'https://pub.orcid.org/v3.0/{ORCID}/works',
                 accept='application/json')
    n = len(data.get('group', []))
    if n > 0:
        pub_count = n
        print(f'Publications (ORCID): {pub_count}')
    else:
        raise ValueError('empty')
except Exception as e:
    print(f'Warning: ORCID publications failed: {e} — keeping {pub_count}')

# ── Citations from OpenAlex ────────────────────────────────────────
cit_count = existing['citations']
try:
    # Resolve author ID
    a = fetch(f'https://api.openalex.org/authors?filter=orcid:{ORCID}&{OA_MAIL}')
    author = a['results'][0]
    author_id = author['id'].replace('https://openalex.org/', '')

    # Fetch all works
    w = fetch(f'https://api.openalex.org/works?filter=authorships.author.id:{author_id}'
              f'&per-page=200&select=title,cited_by_count,type&{OA_MAIL}')
    works = w.get('results', [])

    # Deduplicate preprints + journal articles by normalised title
    def norm(t):
        import re
        return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9\s]', '',
               (t or '').lower())).strip()

    groups = {}
    for work in works:
        if work.get('type') not in ('journal-article', 'posted-content'):
            continue
        key = norm(work.get('title', ''))
        if not key:
            continue
        groups[key] = groups.get(key, 0) + (work.get('cited_by_count') or 0)

    total = sum(groups.values())
    if total > 0:
        cit_count = max(total, existing['citations'])
        print(f'Citations (OpenAlex): {cit_count}')
    else:
        raise ValueError('zero total')
except Exception as e:
    print(f'Warning: OpenAlex citations failed: {e} — keeping {cit_count}')

# ── Write output ───────────────────────────────────────────────────
os.makedirs('data', exist_ok=True)
result = {
    'citations':    cit_count,
    'publications': pub_count,
    'updated':      datetime.date.today().isoformat(),
}
with open('data/scholar.json', 'w') as f:
    json.dump(result, f, indent=2)
print(json.dumps(result, indent=2))
