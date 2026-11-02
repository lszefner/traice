"""Boundary tests for untrusted local-model HTTP responses."""
import io
import json
import unittest
from unittest.mock import patch

from app.ai import ARTICLES_BY_TOPIC, ModelUnavailable, RejectedQuery, ask, generate


def response(payload):
    """Build an Ollama response body from a JSON candidate."""
    return io.BytesIO(json.dumps({"response": json.dumps(payload)}).encode())


class ProviderTests(unittest.TestCase):
    """Model responses must be bounded and cannot select arbitrary Cypher."""

    def test_valid_model_choice_maps_to_a_parameterized_server_query(self):
        """A model selects an identifier; it cannot directly provide query text."""
        with patch("app.ai.urllib.request.urlopen", return_value=response(
            {"template": "articles_by_topic", "search": "agents"}
        )):
            result = ask("Which articles discuss agents?", lambda query, params: [{"query": query, **params}])
        self.assertEqual(result["query"], ARTICLES_BY_TOPIC)
        self.assertEqual(result["parameters"], {"search": "agents"})

    def test_malformed_responses_fail_without_execution(self):
        """Bad JSON, missing fields and oversized responses fail as unavailable."""
        bodies = [b"not json", b'{}', b'{"response":"not json"}',
                  json.dumps({"response": "{}"}).encode(), b"x" * 65537]
        for body in bodies:
            with self.subTest(body=body[:40]), patch(
                "app.ai.urllib.request.urlopen", return_value=io.BytesIO(body)
            ):
                called = []
                with self.assertRaises(ModelUnavailable):
                    ask("Find papers", lambda *args: called.append(args))
                self.assertEqual(called, [])

    def test_unknown_template_is_rejected_without_execution(self):
        """Even valid model JSON cannot introduce an arbitrary query."""
        with patch("app.ai.urllib.request.urlopen", return_value=response(
            {"template": "MATCH (n) DETACH DELETE n", "search": "AI"}
        )):
            called = []
            with self.assertRaises(RejectedQuery):
                ask("Delete everything", lambda *args: called.append(args))
            self.assertEqual(called, [])

    def test_network_failure_is_reported(self):
        """Connection failure is distinct from a rejected generated query."""
        with patch("app.ai.urllib.request.urlopen", side_effect=TimeoutError):
            with self.assertRaises(ModelUnavailable):
                generate("Find papers")


if __name__ == "__main__":
    unittest.main()
