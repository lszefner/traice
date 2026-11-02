"""Run two GDS algorithms on a temporary article–topic projection."""
import json
import os
import uuid

from neo4j import GraphDatabase


def run_analysis(driver):
    """Project the imported graph and return WCC and node similarity summaries."""
    graph = "traice_" + uuid.uuid4().hex
    with driver.session(database=os.getenv("NEO4J_DATABASE", "neo4j")) as session:
        session.run(
            "CALL gds.graph.project($graph, ['Article', 'Topic'], "
            "{HAS_TOPIC: {orientation: 'UNDIRECTED'}})", graph=graph
        ).consume()
        try:
            components = session.run(
                "CALL gds.wcc.stats($graph) YIELD componentCount, componentDistribution "
                "RETURN componentCount, componentDistribution", graph=graph
            ).single()
            similarities = session.run(
                "CALL gds.nodeSimilarity.stream($graph, {topK: 3, similarityCutoff: 0.1}) "
                "YIELD node1, node2, similarity "
                "WITH gds.util.asNode(node1) AS a, gds.util.asNode(node2) AS b, similarity "
                "WHERE a:Article AND b:Article AND a.id < b.id "
                "RETURN a.id AS article_id, b.id AS related_article_id, similarity "
                "ORDER BY similarity DESC, article_id, related_article_id LIMIT 20", graph=graph
            )
            return {"components": dict(components), "similar_articles": [dict(row) for row in similarities]}
        finally:
            session.run("CALL gds.graph.drop($graph, false)", graph=graph).consume()


def main():
    """Print analysis results without writing algorithm results to Neo4j."""
    with GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(os.getenv("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"]),
    ) as driver:
        print(json.dumps(run_analysis(driver), indent=2))


if __name__ == "__main__":
    main()
