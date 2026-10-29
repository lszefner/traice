"""The Conversation feed parsing retains credit and link provenance."""
from scripts.add_conversation import FEED, collect_entries


def test_atom_metadata_and_attribution():
    feed = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry>
        <title>Example AI research</title><published>2025-01-02T12:00:00Z</published>
        <link rel="alternate" href="https://example.org/story"/>
        <author><name>Example Author</name></author>
        <content type="html">&lt;a href="https://arxiv.org/abs/2511.16842"&gt;paper&lt;/a&gt;</content>
        </entry></feed>'''
    row = collect_entries(feed)[0]
    assert row['authors'] == ['Example Author']
    assert row['published_at'] == '2025-01-02'
    assert row['_links'] == {'https://arxiv.org/abs/2511.16842': [FEED]}
