"""Opt-in test of bounded path Cypher against the imported graph."""
import os
from types import SimpleNamespace

import pytest
from neo4j import GraphDatabase

from app.main import find_path


@pytest.mark.integration
def test_direct_reference_path_preserves_recorded_evidence():
    """A real explicit article–paper edge is returned with its provenance."""
    with GraphDatabase.driver(
        "bolt://127.0.0.1:7687", auth=(os.getenv("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"])
    ) as driver:
        with driver.session() as session:
            record = session.run(
                "MATCH (a:Article)-[r:REFERENCES]->(p:Paper) "
                "WHERE r.source_url IS NOT NULL RETURN a.id AS a, p.id AS p, r.source_url AS source LIMIT 1"
            ).single()
        assert record is not None, "Import the snapshot before running integration tests"
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(driver=driver)))
        result = find_path(request, record["a"], record["p"], "Paper")
        assert len(result.data) == 1
        edge = result.data[0]["relationships"][0]
        assert edge["type"] == "REFERENCES"
        assert edge["source_url"] == record["source"]
        assert edge["from_id"] == record["a"]
        assert edge["to_id"] == record["p"]
