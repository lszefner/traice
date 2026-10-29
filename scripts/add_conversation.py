"""Append attributed AI article metadata from The Conversation's Atom feed."""
import json
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree

from scripts.collect import enrich, fetch, paper_links, stable_id

FEED = 'https://theconversation.com/topics/artificial-intelligence-ai-90/articles.atom'
ATOM = '{http://www.w3.org/2005/Atom}'
PATH = Path(__file__).resolve().parents[1] / 'data' / 'articles.json'


def collect_entries(document):
    """Extract only article metadata, author credits and explicit research links."""
    entries = []
    for entry in ElementTree.fromstring(document).findall(ATOM + 'entry'):
        link = entry.find(ATOM + 'link[@rel="alternate"]')
        url = link.get('href') if link is not None else ''
        title = entry.findtext(ATOM + 'title', '').strip()
        published = entry.findtext(ATOM + 'published', '')[:10]
        if not url or not title or not published:
            continue
        content = entry.findtext(ATOM + 'content', '')
        authors = [author.findtext(ATOM + 'name', '').strip()
                   for author in entry.findall(ATOM + 'author')]
        entries.append({'id': stable_id(url), 'url': url, 'title': title,
                        'published_at': published,
                        'publisher': {'id': 'theconversation.com', 'name': 'The Conversation'},
                        'authors': [author for author in authors if author],
                        'topics': [{'id': stable_id('artificial intelligence'),
                                    'name': 'Artificial intelligence'}],
                        'papers': [], 'feed_urls': [FEED],
                        '_links': {url: [FEED] for url in paper_links(content)}})
    return entries


def main():
    """Append unseen articles without altering the original pinned snapshot."""
    with PATH.open(encoding='utf-8') as source:
        snapshot = json.load(source)
    existing = {row['url'] for row in snapshot['articles']}
    rows = enrich([row for row in collect_entries(fetch(FEED)) if row['url'] not in existing])
    snapshot['articles'].extend(rows)
    snapshot.setdefault('additional_snapshots', []).append({
        'feed': FEED, 'collected_at': datetime.now(timezone.utc).isoformat(),
        'articles_added': len(rows), 'with_paper_links': sum(bool(row['papers']) for row in rows)})
    with PATH.open('w', encoding='utf-8') as output:
        json.dump(snapshot, output, ensure_ascii=False, indent=2)
        output.write('\n')
    print(f"Added {len(rows)} articles; {sum(bool(row['papers']) for row in rows)} link to resolved papers")


if __name__ == '__main__':
    main()
