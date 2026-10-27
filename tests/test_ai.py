"""Tests for the query boundary independent of model and graph availability."""

import unittest

from app.ai import ARTICLES_BY_TOPIC, PAPERS_BY_ARTICLE, RejectedQuery, ask, validate


class QueryGuardrailTests(unittest.TestCase):
    """Validate that untrusted model output cannot change the query."""

    def test_supported_query_is_parameterized_and_returns_evidence(self):
        """A supported model response reaches the executor as parameters."""
        search = "AI' MATCH (n) DETACH DELETE n //"
        observed = []

        def execute(query, parameters):
            observed.append((query, parameters))
            return [{"article": "Example", "paper": "Example paper"}]

        result = ask("Find papers", execute, lambda _: {"query": ARTICLES_BY_TOPIC, "search": search})
        self.assertEqual(observed, [(ARTICLES_BY_TOPIC, {"search": search})])
        self.assertEqual(result["evidence"][0]["article"], "Example")

    def test_unsafe_and_unsupported_queries_are_rejected(self):
        """No write, procedure, extra statement, or arbitrary read can execute."""
        for query in (
            "MATCH (n) DETACH DELETE n",
            ARTICLES_BY_TOPIC + " CALL db.labels()",
            ARTICLES_BY_TOPIC + "; MATCH (n) RETURN n",
            "MATCH (n) RETURN n LIMIT 1",
            None,
        ):
            with self.subTest(query=query), self.assertRaises(RejectedQuery):
                validate({"query": query, "search": "agents"})

    def test_invalid_model_responses_fail_closed(self):
        """Unexpected keys, types and unbounded terms are rejected."""
        for value in (None, {}, {"query": PAPERS_BY_ARTICLE, "search": " "},
                      {"query": PAPERS_BY_ARTICLE, "search": "x" * 121},
                      {"query": PAPERS_BY_ARTICLE, "search": [], "extra": 1}):
            with self.subTest(value=value), self.assertRaises(RejectedQuery):
                validate(value)

    def test_invalid_question_never_calls_model(self):
        """Input validation occurs before model or database work."""
        with self.assertRaises(ValueError):
            ask(" ", lambda *_: self.fail(), lambda _: self.fail())


if __name__ == "__main__":
    unittest.main()
