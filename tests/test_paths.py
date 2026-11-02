"""Tests for bounded evidence-path endpoints."""
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_paths_preserve_nodes_edges_and_qualification():
    """A returned relationship identifies direction and source when available."""
    row = {"nodes": [{"id": "a"}, {"id": "p"}], "relationships": [
        {"type": "REFERENCES", "from_id": "a", "to_id": "p", "source_url": "https://example.org"}
    ]}
    with TestClient(app) as client, patch("app.main.read", return_value=[row]) as read:
        result = client.get("/api/articles/a/paths/papers/p").json()["data"][0]
        assert result["relationships"][0]["source_url"] == "https://example.org"
        assert "not proof" in result["interpretation"]
        assert "shortestPath" in read.call_args.args[1]
        assert "*1..4" in read.call_args.args[1]
        assert read.call_args.kwargs == {"start_id": "a", "target_id": "p"}


def test_missing_disconnected_and_same_article():
    """Missing endpoints, no bounded path, and identical article IDs differ."""
    with TestClient(app) as client, patch("app.main.read") as read:
        read.return_value = []
        assert client.get("/api/articles/a/paths/articles/missing").status_code == 404
        read.return_value = [{"nodes": None, "relationships": None}]
        assert client.get("/api/articles/a/paths/articles/b").json() == {"data": []}
        assert client.get("/api/articles/a/paths/articles/a").status_code == 422
