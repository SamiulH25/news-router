import pytest

from app.services.matcher import article_matches_topic
from app.services.story_cluster import cluster_key
from app.models.topic import Topic


def test_keyword_match():
    topic = Topic(id=1, user_id=1, name="Tech", keywords="apple, ai", exclude_keywords="")
    article = type("A", (), {"title": "Apple unveils new AI chip", "summary": ""})()
    assert article_matches_topic(article, topic) is True


def test_exclude_keyword():
    topic = Topic(id=1, user_id=1, name="Tech", keywords="apple", exclude_keywords="rumor")
    article = type("A", (), {"title": "Apple rumor mill spins", "summary": ""})()
    assert article_matches_topic(article, topic) is False


def test_cluster_key_groups_similar_titles():
    a = cluster_key("Apple unveils new MacBook Pro today")
    b = cluster_key("Apple unveils new MacBook Pro in event")
    assert a == b
