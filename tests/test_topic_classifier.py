"""Tests for the chronological topic classification experiment."""
import unittest

from scripts.topic_classifier import evaluate


class TopicClassifierTests(unittest.TestCase):
    """The classifier must preserve a strict chronological split."""

    def test_temporal_split_and_unseen_labels(self):
        """The test period is held out entirely and unseen classes are visible."""
        records = [
            {"id": str(i), "title": "robot arm", "published_at": "2025-01-01",
             "topics": [{"name": "Robotics"}]} for i in range(8)
        ]
        records += [
            {"id": str(i), "title": "new topic", "published_at": "2025-02-01",
             "topics": [{"name": "AI"}]} for i in range(8, 10)
        ]
        result = evaluate(records)
        self.assertEqual(result["training_count"], 8)
        self.assertEqual(result["test_count"], 2)
        self.assertEqual(result["unseen_test_labels"], ["AI"])
        self.assertEqual(result["model_accuracy"], 0)

    def test_rejects_unusable_snapshots(self):
        """Do not present a result when a temporal test cannot be formed."""
        with self.assertRaises(ValueError):
            evaluate([])


if __name__ == "__main__":
    unittest.main()
