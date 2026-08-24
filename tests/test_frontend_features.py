from pathlib import Path


def test_chat_page_has_filter_and_markdown_export():
    html = (Path(__file__).parents[1] / "web" / "page" / "chat.html").read_text(encoding="utf-8")
    assert 'id="contentTypeFilter"' in html
    assert "metadata_filters: contentType ? {content_type: contentType} : {}" in html
    assert 'id="btnExport"' in html
    assert "function markdownFromHistory(items)" in html
    assert "chunk: ${citation.chunk_id}" in html
