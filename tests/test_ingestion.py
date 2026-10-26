"""Checks for stable IDs, provenance and snapshot ingestion."""
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from scripts.collect import paper_links, stable_id
from scripts.ingest import import_snapshot, load_snapshot

SNAPSHOT = Path(__file__).resolve().parents[1] / 'data' / 'articles.json'


def test_identifiers_and_explicit_paper_links():
    assert stable_id('https://example.org/a') == stable_id('https://example.org/a')
    assert '/' not in stable_id('https://example.org/a')
    assert paper_links('<a href="https://arxiv.org/abs/2511.16842">paper</a>') == [
        'https://doi.org/10.48550/arXiv.2511.16842']
    assert paper_links('just the words arxiv and AI') == []


def test_snapshot_sources_and_verified_example():
    rows = load_snapshot(SNAPSHOT)
    assert 200 <= len(rows) <= 400
    assert len({row['id'] for row in rows}) == len(rows)
    assert len({row['publisher']['id'] for row in rows}) >= 3
    example = next(row for row in rows if 'ai-benchmarks-flaws' in row['url'])
    assert any(p['url'].lower() == 'https://doi.org/10.48550/arxiv.2511.16842'
               for p in example['papers'])
    assert all(row['topics'] and row['url'].startswith('https://') for row in rows)


def test_invalid_snapshot_rejected(tmp_path):
    path = tmp_path / 'bad.json'
    path.write_text(json.dumps({'articles': [{}]}), encoding='utf-8')
    with pytest.raises(ValueError):
        load_snapshot(path)


def test_import_uses_parameterized_batches():
    driver = MagicMock()
    rows = load_snapshot(SNAPSHOT)
    import_snapshot(driver, rows)
    session = driver.session.return_value.__enter__.return_value
    calls = session.run.call_args_list
    assert len(calls) == 4 + 3 * ((len(rows) + 99) // 100)
    assert all('rows' in call.kwargs for call in calls[4:])
