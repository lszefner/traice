"""Traice API: explore evidence linking AI news and research."""

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from neo4j import GraphDatabase, unit_of_work
from neo4j.exceptions import Neo4jError, ServiceUnavailable
from pydantic import BaseModel


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Create one driver for the life of the service."""
    application.state.driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password")),
    )
    yield
    application.state.driver.close()


app = FastAPI(title="Traice", version="0.1.0", lifespan=lifespan)


class Result(BaseModel):
    """Results and the graph evidence used to obtain them."""

    data: list[dict[str, Any]]


def read(request: Request, cypher: str, **parameters: Any) -> list[dict[str, Any]]:
    """Execute a parameterized, time-limited query in a read transaction."""
    try:
        with request.app.state.driver.session(database=os.getenv("NEO4J_DATABASE", "neo4j")) as session:

            @unit_of_work(timeout=5)
            def query_transaction(tx):
                return [dict(row) for row in tx.run(cypher, **parameters)]

            return session.execute_read(query_transaction)
    except (Neo4jError, ServiceUnavailable) as exc:
        raise HTTPException(status_code=503, detail="Graph database unavailable or query failed") from exc


@app.get("/health")
def health() -> dict[str, str]:
    """Report process liveness."""
    return {"status": "ok"}


@app.get("/api/articles", response_model=Result)
def articles(request: Request, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)) -> Result:
    """Browse articles by most recent publication date."""
    return Result(
        data=read(
            request,
            """
        MATCH (a:Article)-[:PUBLISHED_BY]->(p:Publisher)
        RETURN a.id AS id, a.title AS title, a.url AS url,
               a.published_at AS published_at, a.authors AS authors, p.name AS publisher
        ORDER BY published_at DESC, id SKIP $offset LIMIT $limit
    """,
            limit=limit,
            offset=offset,
        )
    )


@app.get("/api/articles/{article_id}/evidence", response_model=Result)
def evidence(article_id: str, request: Request) -> Result:
    """Return a story's publisher, topics and explicitly linked papers."""
    rows = read(
        request,
        """
        MATCH (a:Article {id: $id})-[:PUBLISHED_BY]->(publisher:Publisher)
        OPTIONAL MATCH (a)-[:HAS_TOPIC]->(topic:Topic)
        WITH a, publisher, collect(DISTINCT topic.name) AS topics
        OPTIONAL MATCH (a)-[ref:REFERENCES]->(paper:Paper)
        RETURN a.id AS id, a.title AS title, a.url AS url, a.published_at AS published_at,
               publisher.name AS publisher, a.authors AS authors, topics,
               collect(DISTINCT CASE WHEN paper IS NULL THEN null ELSE
                   {id: paper.id, title: paper.title, url: paper.url,
                    source_url: ref.source_url, linked_url: ref.linked_url,
                    feed_urls: ref.feed_urls, method: ref.method} END) AS papers
    """,
        id=article_id,
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Article not found")
    return Result(data=rows)


@app.get("/api/articles/{article_id}/related", response_model=Result)
def related(article_id: str, request: Request, limit: int = Query(10, ge=1, le=50)) -> Result:
    """Find related stories through their shared topics, not inferred references."""
    if not read(request, "MATCH (a:Article {id:$id}) RETURN a.id AS id", id=article_id):
        raise HTTPException(status_code=404, detail="Article not found")
    return Result(
        data=read(
            request,
            """
        MATCH (a:Article {id:$id})-[:HAS_TOPIC]->(t:Topic)<-[:HAS_TOPIC]-(other:Article)
        MATCH (other)-[:PUBLISHED_BY]->(publisher:Publisher)
        WHERE other <> a
        WITH other, publisher, collect(DISTINCT t.name) AS shared_topics
        RETURN other.id AS id, other.title AS title, other.url AS url, other.authors AS authors,
               publisher.name AS publisher, shared_topics,
               size(shared_topics) AS score, 'shared_topic' AS connection
        ORDER BY score DESC, id LIMIT $limit
    """,
            id=article_id,
            limit=limit,
        )
    )


@app.get("/api/papers/{paper_id}/coverage", response_model=Result)
def coverage(paper_id: str, request: Request, limit: int = Query(20, ge=1, le=50)) -> Result:
    """Find articles with explicit source links to a research paper."""
    if not read(request, "MATCH (p:Paper {id:$id}) RETURN p.id AS id", id=paper_id):
        raise HTTPException(status_code=404, detail="Paper not found")
    return Result(
        data=read(
            request,
            """
        MATCH (a:Article)-[r:REFERENCES]->(p:Paper {id:$id})
        MATCH (a)-[:PUBLISHED_BY]->(publisher:Publisher)
        RETURN a.id AS id, a.title AS title, a.url AS url, a.authors AS authors, publisher.name AS publisher,
               r.source_url AS source_url, r.linked_url AS linked_url, r.feed_urls AS feed_urls, r.method AS method
        ORDER BY a.published_at DESC, id LIMIT $limit
    """,
            id=paper_id,
            limit=limit,
        )
    )


@app.get("/api/topics/{topic_id}/connections", response_model=Result)
def connections(topic_id: str, request: Request, limit: int = Query(20, ge=1, le=50)) -> Result:
    """Explore bounded two-hop article-topic-article paths."""
    if not read(request, "MATCH (t:Topic {id:$id}) RETURN t.id AS id", id=topic_id):
        raise HTTPException(status_code=404, detail="Topic not found")
    return Result(
        data=read(
            request,
            """
        MATCH (t:Topic {id:$id})<-[:HAS_TOPIC]-(a:Article)
        WITH t, a ORDER BY a.id LIMIT 100
        MATCH (t)<-[:HAS_TOPIC]-(b:Article)
        WHERE a.id < b.id
        RETURN a.id AS from_id, a.title AS from_title, a.url AS from_url, a.authors AS from_authors,
               [(a)-[:PUBLISHED_BY]->(ap:Publisher) | ap.name] AS from_publishers, t.name AS topic,
               b.id AS to_id, b.title AS to_title, b.url AS to_url, b.authors AS to_authors,
               [(b)-[:PUBLISHED_BY]->(bp:Publisher) | bp.name] AS to_publishers, 'shared_topic' AS connection
        ORDER BY from_id, to_id LIMIT $limit
    """,
            id=topic_id,
            limit=limit,
        )
    )


class AskRequest(BaseModel):
    """A supported natural-language question about the evidence graph."""

    question: str


class AskResponse(BaseModel):
    """The validated query, its parameters and the evidence returned."""

    query: str
    parameters: dict[str, Any]
    evidence: list[dict[str, Any]]


@app.post("/api/ask", response_model=AskResponse)
def ask_question(body: AskRequest, request: Request) -> AskResponse:
    """Select and validate a supported Cypher query using a local language model."""
    from app.ai import ModelUnavailable, RejectedQuery, ask  # pylint: disable=import-outside-toplevel

    try:
        answer = ask(body.question, lambda query, parameters: read(request, query, **parameters))
    except RejectedQuery as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ModelUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return AskResponse(**answer)


def find_path(request: Request, article_id: str, target_id: str, target_label: str) -> Result:
    """Find one shortest bounded path, preserving actual edge direction and provenance."""
    # The label is selected by the endpoint, never supplied as query text by a client.
    if target_label not in ("Article", "Paper"):
        raise ValueError("Unsupported target label")
    if target_label == "Article" and article_id == target_id:
        raise HTTPException(status_code=422, detail="Choose two different articles")
    cypher = """
        MATCH (start:Article {id: $start_id})
        MATCH (target:TARGET_LABEL {id: $target_id})
        OPTIONAL MATCH path = shortestPath((start)-[:HAS_TOPIC|REFERENCES*1..4]-(target))
        RETURN CASE WHEN path IS NULL THEN null ELSE
            [node IN nodes(path) | {id: node.id, labels: labels(node),
              title: node.title, name: node.name, url: node.url, authors: node.authors,
              publishers: [(node)-[:PUBLISHED_BY]->(pub:Publisher) | pub.name]}] END AS nodes,
            CASE WHEN path IS NULL THEN null ELSE
            [rel IN relationships(path) | {type: type(rel),
              from_id: startNode(rel).id, to_id: endNode(rel).id,
              source_url: rel.source_url, method: rel.method}] END AS relationships
    """.replace("TARGET_LABEL", target_label)
    rows = read(request, cypher, start_id=article_id, target_id=target_id)
    if not rows:
        raise HTTPException(status_code=404, detail="Article or target not found")
    if rows[0]["nodes"] is None:
        return Result(data=[])
    rows[0]["interpretation"] = (
        "A path shows recorded connections, not proof that articles report the same event "
        "or that claims are true."
    )
    return Result(data=rows)


@app.get("/api/articles/{article_id}/paths/articles/{other_id}", response_model=Result)
def article_path(article_id: str, other_id: str, request: Request) -> Result:
    """Find a shortest path between distinct articles in at most four edges."""
    return find_path(request, article_id, other_id, "Article")


@app.get("/api/articles/{article_id}/paths/papers/{paper_id}", response_model=Result)
def article_paper_path(article_id: str, paper_id: str, request: Request) -> Result:
    """Find a shortest path from an article to a paper in at most four edges."""
    return find_path(request, article_id, paper_id, "Paper")
