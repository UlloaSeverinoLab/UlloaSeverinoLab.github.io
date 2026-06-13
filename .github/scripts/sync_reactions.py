import urllib.request, json, time, os

NS = 'ulloaseverinolab'
NEWS_IDS = [
    'cagla-visit-jun26',
    'francesca-welcome-jun26',
    'marta-astrocafe-jun26',
    'lab-lunch-may26',
]
REACTIONS = ['heart', 'clap', 'thumbsup']

existing = {}
try:
    with open('data/reactions.json') as f:
        existing = json.load(f)
except Exception:
    pass

counts = {}
for news_id in NEWS_IDS:
    counts[news_id] = {}
    for reaction in REACTIONS:
        url = f'https://api.counterapi.dev/v1/{NS}/news-{news_id}-{reaction}'
        prev = existing.get(news_id, {}).get(reaction, 0)
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'SyncBot/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                counts[news_id][reaction] = max(data.get('count', 0), prev)
        except Exception as e:
            print(f'Warning: {news_id}-{reaction}: {e}')
            counts[news_id][reaction] = prev
        time.sleep(0.35)

os.makedirs('data', exist_ok=True)
with open('data/reactions.json', 'w') as f:
    json.dump(counts, f, indent=2)
print(json.dumps(counts, indent=2))
