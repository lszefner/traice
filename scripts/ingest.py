"""Idempotently import Traice's source-attributed metadata snapshot to Neo4j."""
import json
import os
from pathlib import Path

CONSTRAINTS = [
    "CREATE CONSTRAINT article_id IF NOT EXISTS FOR (n:Article) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT publisher_id IF NOT EXISTS FOR (n:Publisher) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT topic_id IF NOT EXISTS FOR (n:Topic) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT paper_id IF NOT EXISTS FOR (n:Paper) REQUIRE n.id IS UNIQUE",
]
IMPORT_QUERY = """
UNWIND $rows AS row
MERGE (a:Article {id: row.id})
SET a.url = row.url, a.title = row.title, a.published_at = row.published_at
MERGE (publisher:Publisher {id: row.publisher.id})
SET publisher.name = row.publisher.name
MERGE (a)-[:PUBLISHED_BY]->(publisher)
WITH a, row
UNWIND row.topics AS topic
MERGE (t:Topic {id: topic.id})
SET t.name = topic.name
MERGE (a)-[:HAS_TOPIC]->(t)
"""
PAPER_QUERY = """
UNWIND $rows AS row
MATCH (a:Article {id: row.id})
UNWIND row.papers AS paper
MERGE (p:Paper {id: paper.id})
SET p.url = paper.url, p.title = paper.title, p.openalex_id = paper.openalex_id
MERGE (a)-[r:REFERENCES]->(p)
SET r.source_url = row.url, r.linked_url = paper.linked_url,
    r.method = CASE WHEN size(row.feed_urls) > 0 THEN 'feed_link' ELSE 'manually_verified_page_link' END,
    r.feed_urls = paper.linked_feed_urls
"""
CITATION_QUERY = """
UNWIND $rows AS row
UNWIND row.papers AS paper
MATCH (p:Paper {id: paper.id})
UNWIND paper.references AS ref
MATCH (other:Paper {id: ref})
MERGE (p)-[r:CITES]->(other)
SET r.source = 'OpenAlex'
"""


def load_snapshot(path):
    """Read the checked-in snapshot and reject invalid basic records."""
    with open(path, encoding='utf-8') as source:
        doc = json.load(source)
    rows = doc['articles']
    if not isinstance(rows, list) or not rows:
        raise ValueError('Snapshot must contain articles')
    for row in rows:
        if not all(row.get(key) for key in ('id', 'url', 'title', 'published_at', 'publisher', 'topics')):
            raise ValueError('Article is missing required fields')
        if 'papers' not in row or not isinstance(row['papers'], list):
            raise ValueError('Article papers must be a list')
    return rows


def import_snapshot(driver, rows):
    """Create constraints and merge records in bounded parameterized batches."""
    with driver.session() as session:
        for query in CONSTRAINTS:
            session.run(query).consume()
        for start in range(0, len(rows), 100):
            session.run(IMPORT_QUERY, rows=rows[start:start + 100]).consume()
        for start in range(0, len(rows), 100):
            session.run(PAPER_QUERY, rows=rows[start:start + 100]).consume()
        for start in range(0, len(rows), 100):
            session.run(CITATION_QUERY, rows=rows[start:start + 100]).consume()


def main():
    """Connect using environment configuration and import the default fixture."""
    from neo4j import GraphDatabase  # pylint: disable=import-outside-toplevel

    uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    user = os.environ.get('NEO4J_USER', 'neo4j')
    password = os.environ['NEO4J_PASSWORD']
    path = Path(__file__).resolve().parents[1] / 'data' / 'articles.json'
    rows = load_snapshot(path)
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        import_snapshot(driver, rows)
    print(f'Imported {len(rows)} article records')


if __name__ == '__main__':
    main()
