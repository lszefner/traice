"""Compare a date-filter query before and after a temporary index."""
import json
import os
import statistics
import time
import uuid

from neo4j import GraphDatabase


QUERY = "MATCH (a:Article) WHERE a.published_at = $date RETURN count(a) AS articles"


def measure(session, date):
    """Warm the query, sample client round-trip latency, and capture PROFILE."""
    for _ in range(5):
        session.run(QUERY, date=date).consume()
    elapsed = []
    for _ in range(30):
        started = time.perf_counter()
        result = session.run(QUERY, date=date).single()["articles"]
        elapsed.append((time.perf_counter() - started) * 1000)
    profile = session.run("PROFILE " + QUERY, date=date).consume().profile
    return {"matches": result, "median_ms": round(statistics.median(elapsed), 3),
            "min_ms": round(min(elapsed), 3), "max_ms": round(max(elapsed), 3),
            "profile": profile}


def main():
    """Use a unique temporary index and remove only that index afterwards."""
    name = "traice_bench_" + uuid.uuid4().hex
    with GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"]),
    ) as driver, driver.session(database=os.getenv("NEO4J_DATABASE", "neo4j")) as session:
        existing = list(session.run(
            "SHOW INDEXES YIELD name, labelsOrTypes, properties "
            "WHERE 'Article' IN labelsOrTypes AND 'published_at' IN properties "
            "RETURN name"
        ))
        if existing:
            raise RuntimeError("An Article.published_at index already exists; cannot measure a before case")
        selected = session.run(
            "MATCH (a:Article) WHERE a.published_at IS NOT NULL "
            "RETURN a.published_at AS date, count(*) AS n ORDER BY n, date LIMIT 1"
        ).single()
        if selected is None:
            raise RuntimeError("Import dated articles before benchmarking")
        date = selected["date"]
        before = measure(session, date)
        created = False
        try:
            session.run(f"CREATE INDEX {name} FOR (a:Article) ON (a.published_at)").consume()
            created = True
            session.run("CALL db.awaitIndex($name, 60)", name=name).consume()
            after = measure(session, date)
        finally:
            if created:
                session.run(f"DROP INDEX {name}").consume()
        print(json.dumps({"date": date, "before": before, "after": after}, indent=2))


if __name__ == "__main__":
    main()
