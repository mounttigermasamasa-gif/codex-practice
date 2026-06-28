import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pdf_toolbox import (
    extract_file_links,
    format_extensions_for_status,
    is_file_link,
    normalize_extensions,
    parse_page_ranges,
    safe_download_name,
)


def test_parse_page_ranges_accepts_single_pages_and_ranges():
    assert parse_page_ranges("1-3, 5, 8-10", 10) == [(1, 3), (5, 5), (8, 10)]


def test_parse_page_ranges_rejects_out_of_bounds_page():
    with pytest.raises(ValueError):
        parse_page_ranges("1-4", 3)


def test_parse_page_ranges_rejects_empty_input():
    with pytest.raises(ValueError):
        parse_page_ranges(" , ", 5)


def test_is_file_link_detects_supported_file_extensions():
    assert is_file_link("https://example.com/files/report.pdf?download=1")
    assert is_file_link("/images/photo.JPG")
    assert not is_file_link("https://example.com/articles/report")


def test_is_file_link_filters_to_selected_extensions():
    assert is_file_link("https://example.com/files/report.pdf", {".pdf", ".docx"})
    assert is_file_link("https://example.com/files/proposal.docx", {".pdf", ".docx"})
    assert not is_file_link("https://example.com/files/archive.zip", {".pdf", ".docx"})


def test_normalize_extensions_adds_dots_and_lowercases_values():
    assert normalize_extensions({"PDF", ".DOCX"}) == {".pdf", ".docx"}


def test_format_extensions_for_status_sorts_normalized_extensions():
    assert format_extensions_for_status({"docx", ".PDF"}) == ".docx, .pdf"


def test_extract_file_links_returns_unique_absolute_file_links():
    html = """
    <a href="/docs/report.pdf">report</a>
    <a href="https://cdn.example.com/archive.zip">archive</a>
    <a href="/docs/report.pdf">duplicate</a>
    <a href="/page.html">page</a>
    <img src="images/chart.png">
    """

    assert extract_file_links(html, "https://example.com/base/index.html") == [
        "https://example.com/docs/report.pdf",
        "https://cdn.example.com/archive.zip",
        "https://example.com/base/images/chart.png",
    ]


def test_safe_download_name_sanitizes_and_deduplicates_names():
    used_names: set[str] = set()

    assert safe_download_name("https://example.com/files/my%20report.pdf", used_names) == "my report.pdf"
    assert safe_download_name("https://example.com/other/my%20report.pdf", used_names) == "my report_2.pdf"
    assert safe_download_name("https://example.com/files/a:b.zip", used_names) == "a_b.zip"


def test_extract_file_links_filters_multiple_selected_extensions():
    html = """
    <a href="/docs/report.pdf">report</a>
    <a href="/docs/proposal.docx">proposal</a>
    <a href="/docs/archive.zip">archive</a>
    <img src="/images/chart.png">
    """

    assert extract_file_links(html, "https://example.com/", {"pdf", ".docx"}) == [
        "https://example.com/docs/report.pdf",
        "https://example.com/docs/proposal.docx",
    ]
