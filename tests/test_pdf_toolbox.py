import pytest

from pdf_toolbox import parse_page_ranges


def test_parse_page_ranges_accepts_single_pages_and_ranges():
    assert parse_page_ranges("1-3, 5, 8-10", 10) == [(1, 3), (5, 5), (8, 10)]


def test_parse_page_ranges_rejects_out_of_bounds_page():
    with pytest.raises(ValueError):
        parse_page_ranges("1-4", 3)


def test_parse_page_ranges_rejects_empty_input():
    with pytest.raises(ValueError):
        parse_page_ranges(" , ", 5)
