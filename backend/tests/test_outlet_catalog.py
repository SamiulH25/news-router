import pytest

from app.data.default_feeds import (
    DEFAULT_NEWS_OUTLETS,
    NEWS_COUNTRIES,
    default_selected_urls,
    resolve_outlets,
)


def test_every_outlet_has_valid_country():
    codes = {country.code for country in NEWS_COUNTRIES}
    for outlet in DEFAULT_NEWS_OUTLETS:
        assert outlet.country_code in codes


def test_default_selected_urls_are_catalog_urls():
    catalog_urls = {outlet.url for outlet in DEFAULT_NEWS_OUTLETS}
    for url in default_selected_urls():
        assert url in catalog_urls


def test_resolve_outlets_deduplicates():
    first = DEFAULT_NEWS_OUTLETS[0].url
    resolved = resolve_outlets([first, first])
    assert len(resolved) == 1


def test_resolve_outlets_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown outlet"):
        resolve_outlets(["https://example.com/not-in-catalog"])
