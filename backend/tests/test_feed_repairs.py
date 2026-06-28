from app.services.feed_repairs import repair_for_url


def test_repair_ctv_to_global_news():
    repair = repair_for_url("https://www.ctvnews.ca/rss/ctvnews-ca-top-stories/")
    assert repair is not None
    assert repair.url == "https://globalnews.ca/feed/"
    assert repair.title == "Global News"


def test_repair_daily_star_feed_path():
    repair = repair_for_url("https://www.thedailystar.net/feed")
    assert repair is not None
    assert repair.url == "https://www.thedailystar.net/rss.xml"
