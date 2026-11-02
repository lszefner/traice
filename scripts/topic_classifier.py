"""Evaluate a chronological article-node topic classifier against a baseline."""
import argparse
from collections import Counter, defaultdict
import json
import math
import re


def words(title):
    """Extract simple lowercase word features."""
    return re.findall(r"[a-z0-9]+", title.lower())


def evaluate(articles):
    """Predict the single recorded feed topic for later articles from their titles.

    Only single-topic dated records are eligible. All articles on the test start
    date are held out, and vocabulary/statistics are fitted on training only.
    """
    eligible = [a for a in articles if a.get("published_at") and a.get("title")
                and len(a.get("topics", [])) == 1 and a["topics"][0].get("name")]
    eligible.sort(key=lambda a: (a["published_at"], a["id"]))
    if len(eligible) < 10:
        raise ValueError("Need at least 10 dated, single-topic articles")
    cutoff = eligible[int(len(eligible) * 0.8)]["published_at"]
    train = [a for a in eligible if a["published_at"] < cutoff]
    test = [a for a in eligible if a["published_at"] >= cutoff]
    if not train or not test:
        raise ValueError("Need articles on at least two distinct dates")
    labels = Counter(a["topics"][0]["name"] for a in train)
    vocab = set()
    counts = defaultdict(Counter)
    for article in train:
        tokens = words(article["title"])
        vocab.update(tokens)
        counts[article["topics"][0]["name"]].update(tokens)
    if not vocab:
        raise ValueError("Training titles contain no usable tokens")
    totals = {label: sum(counts[label].values()) for label in labels}
    majority = sorted(labels, key=lambda label: (-labels[label], label))[0]
    predictions = []
    for article in test:
        tokens = [token for token in words(article["title"]) if token in vocab]
        scores = {
            label: math.log(n / len(train)) + sum(
                math.log((counts[label][token] + 1) / (totals[label] + len(vocab)))
                for token in tokens
            ) for label, n in labels.items()
        }
        predicted = sorted(scores, key=lambda label: (-scores[label], label))[0]
        predictions.append((article["topics"][0]["name"], predicted))
    return {
        "target": "recorded single feed topic of article",
        "cutoff_date": cutoff,
        "training_count": len(train), "test_count": len(test),
        "training_labels": dict(labels),
        "unseen_test_labels": sorted({actual for actual, _ in predictions} - set(labels)),
        "baseline_majority_topic": majority,
        "baseline_accuracy": sum(actual == majority for actual, _ in predictions) / len(test),
        "model_accuracy": sum(actual == predicted for actual, predicted in predictions) / len(test),
    }


def main():
    """Evaluate a saved article snapshot without contacting an external service."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", help="Path to collected articles JSON")
    args = parser.parse_args()
    with open(args.snapshot, encoding="utf-8") as source:
        snapshot = json.load(source)
    print(json.dumps(evaluate(snapshot["articles"]), indent=2))


if __name__ == "__main__":
    main()
