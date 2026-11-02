"""Opt-in smoke tests for the locally running Compose stack."""

import os
from urllib.request import urlopen

import pytest
from neo4j import GraphDatabase


@pytest.mark.integration
def test_proxy_reaches_healthy_api():
    """The reverse proxy reaches the running API."""
    with urlopen("http://127.0.0.1:8080/health", timeout=5) as response:
        assert response.status == 200


@pytest.mark.integration
def test_neo4j_connectivity():
    """The Neo4j Bolt port accepts authenticated connections."""
    password = os.environ["NEO4J_PASSWORD"]
    with GraphDatabase.driver(
        "bolt://127.0.0.1:7687", auth=(os.getenv("NEO4J_USER", "neo4j"), password)
    ) as driver:
        driver.verify_connectivity()
