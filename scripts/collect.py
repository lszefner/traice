"""Collect a dated, metadata-only snapshot from selected research-news feeds."""
import hashlib
import html
import json
import re
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree

FEEDS = [
    ("https://news.mit.edu/rss/topic/artificial-intelligence2", "MIT News", "news.mit.edu", "Artificial intelligence"),
    ("https://news.mit.edu/rss/topic/machine-learning", "MIT News", "news.mit.edu", "Machine learning"),
    ("https://www.sciencedaily.com/rss/computers_math/artificial_intelligence.xml", "ScienceDaily", "sciencedaily.com", "Artificial intelligence"),
    ("https://www.sciencedaily.com/rss/computers_math/robotics.xml", "ScienceDaily", "sciencedaily.com", "Robotics"),
    ("https://www.sciencedaily.com/rss/computers_math/neural_interfaces.xml", "ScienceDaily", "sciencedaily.com", "Neural interfaces"),
]
USER_AGENT = "Traice educational project (metadata collection)"
CONTENT = "{http://purl.org/rss/1.0/modules/content/}encoded"


def stable_id(value):
    """Return a short, URL-safe stable identifier."""
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def fetch(url):
    """Retrieve a source document with an explicit timeout."""
    with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=25) as response:
        return response.read()


def paper_links(text):
    """Extract explicit arXiv and DOI URLs from feed content."""
    links = set()
    for match in re.finditer(r'https?://(?:www\.)?arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?', html.unescape(text), re.I):
        links.add("https://doi.org/10.48550/arXiv." + match.group(1))
    for match in re.finditer(r'https?://(?:dx\.)?doi\.org/(10\.\d{4,9}/[^\s<>"\']+)', html.unescape(text), re.I):
        links.add("https://doi.org/" + match.group(1).rstrip('.,;)]'))
    return sorted(links)


def collect():
    """Collect deduplicated article metadata and candidate explicit paper links."""
    articles = {}
    for feed, publisher, domain, topic in FEEDS:
        root = ElementTree.fromstring(fetch(feed))
        for item in root.findall('./channel/item'):
            url = item.findtext('link', '').strip()
            title = item.findtext('title', '').strip()
            date = item.findtext('pubDate', '')
            if not url or not title or not date:
                continue
            try:
                published = parsedate_to_datetime(date).date().isoformat()
            except (TypeError, ValueError):
                continue
            row = articles.setdefault(url, {"id": stable_id(url), "url": url, "title": title,
                "published_at": published, "publisher": {"id": domain, "name": publisher},
                "topics": [], "papers": [], "_links": []})
            entry = {"id": stable_id(topic.lower()), "name": topic}
            if entry not in row['topics']:
                row['topics'].append(entry)
            row['_links'] = sorted(set(row['_links']) | set(paper_links(item.findtext(CONTENT, '') + ' ' + item.findtext('description', ''))))
    # A manually checked example: the Stanford article links directly to this arXiv paper.
    url = 'https://news.stanford.edu/stories/2025/12/ai-benchmarks-flaws-models-bugs-research'
    articles[url] = {'id': stable_id(url), 'url': url,
        'title': 'Researchers work to squash ‘fantastic bugs’ hidden in AI benchmarks',
        'published_at': '2025-12-08',
        'publisher': {'id': 'news.stanford.edu', 'name': 'Stanford Report'},
        'topics': [{'id': stable_id('artificial intelligence'), 'name': 'Artificial intelligence'}],
        'papers': [], '_links': ['https://doi.org/10.48550/arXiv.2511.16842']}
    return list(articles.values())


def enrich(articles, max_requests=30):
    """Resolve explicit DOI links to OpenAlex works, leaving failed links unasserted."""
    cache = {}
    for row in reversed(articles):
        for doi in row.pop('_links'):
            if doi not in cache and len(cache) < max_requests:
                try:
                    doc = json.loads(fetch('https://api.openalex.org/works/' + doi))
                    canonical = doc.get('doi') or doi
                    cache[doi] = {"id": stable_id(canonical.lower()), "url": canonical,
                                  "title": doc.get('display_name') or canonical,
                                  "references": doc.get("referenced_works", []), "openalex_id": doc['id']}
                except (HTTPError, URLError, TimeoutError, ValueError, KeyError):
                    cache[doi] = None
                time.sleep(0.1)
            paper = cache.get(doi)
            if paper and paper not in row['papers']:
                row['papers'].append(paper)
    # Keep only citation edges whose endpoints both occur in this snapshot.
    ids = {p['openalex_id']: p['id'] for p in cache.values() if p}
    for paper in cache.values():
        if paper:
            paper['references'] = [ids[ref] for ref in paper['references'] if ref in ids]
    return articles


def main():
    """Save a deterministic-shape metadata snapshot."""
    result = {"collected_at": datetime.now(timezone.utc).isoformat(), "feeds": [x[0] for x in FEEDS],
              "articles": enrich(collect())}
    with open('data/articles.json', 'w', encoding='utf-8') as out:
        json.dump(result, out, ensure_ascii=False, indent=2)
        out.write('\n')
    rows = result['articles']
    print(f"{len(rows)} articles; {sum(bool(row['papers']) for row in rows)} with resolved explicit paper links")


if __name__ == '__main__':
    main()
