"""
tests/test_tools.py

Tests for each FitFindr tool. Run with: pytest tests/
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from tools import search_listings, create_fit_card


# ── search_listings tests ─────────────────────────────────────────────────────

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []  # empty list, no exception

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)

def test_search_size_filter():
    results = search_listings("tee", size="M", max_price=None)
    for item in results:
        assert "m" in item["size"].lower()

def test_search_no_price_filter():
    results_all = search_listings("vintage", size=None, max_price=None)
    results_cheap = search_listings("vintage", size=None, max_price=5)
    assert len(results_all) >= len(results_cheap)

def test_search_returns_list_of_dicts():
    results = search_listings("denim", size=None, max_price=None)
    assert isinstance(results, list)
    if results:
        assert isinstance(results[0], dict)
        assert "title" in results[0]
        assert "price" in results[0]


def test_fit_card_empty_outfit_returns_error():
    fake_item = {"title": "Test Tee", "price": 20.0, "platform": "depop"}
    result = create_fit_card("", fake_item)
    assert "Cannot generate fit card" in result

def test_fit_card_whitespace_outfit_returns_error():
    fake_item = {"title": "Test Tee", "price": 20.0, "platform": "depop"}
    result = create_fit_card("   ", fake_item)
    assert "Cannot generate fit card" in result

def test_fit_card_returns_string():
    fake_item = {"title": "Faded Band Tee", "price": 22.0, "platform": "depop"}
    result = create_fit_card("", fake_item)
    assert isinstance(result, str)
    assert len(result) > 0