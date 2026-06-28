"""Probe candidate outlet RSS URLs for onboarding catalog."""
import asyncio

import feedparser
import httpx

from app.services.entry_quality import is_valid_parsed_feed
from app.services.rss_http import USER_AGENT

CANDIDATES = [
    ("CA", "CBC News", "https://www.cbc.ca/webfeed/rss/rss-topstories"),
    ("CA", "Global News", "https://globalnews.ca/feed/"),
    ("CA", "National Post", "https://nationalpost.com/feed"),
    ("CA", "Toronto Star", "https://www.thestar.com/search/?f=rss"),
    ("BD", "The Daily Star", "https://www.thedailystar.net/rss.xml"),
    ("BD", "Prothom Alo (EN)", "https://en.prothomalo.com/feed"),
    ("BD", "Dhaka Tribune", "https://www.dhakatribune.com/feed/"),
    ("US", "NPR News", "https://feeds.npr.org/1001/rss.xml"),
    ("US", "NYT Home", "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml"),
    ("US", "CNN Top", "http://rss.cnn.com/rss/cnn_topstories.rss"),
    ("US", "AP Top", "https://apnews.com/index.rss"),
    ("US", "Washington Post", "https://feeds.washingtonpost.com/rss/national"),
    ("GB", "BBC News", "http://feeds.bbci.co.uk/news/rss.xml"),
    ("GB", "The Guardian UK", "https://www.theguardian.com/uk/rss"),
    ("GB", "Sky News", "https://feeds.skynews.com/feeds/rss/home.xml"),
    ("GB", "Independent", "https://www.independent.co.uk/news/uk/rss"),
    ("AU", "ABC News", "https://www.abc.net.au/news/feed/51120/rss.xml"),
    ("AU", "Guardian AU", "https://www.theguardian.com/australia-news/rss"),
    ("AU", "Sydney Morning Herald", "https://www.smh.com.au/rss/feed.xml"),
    ("IN", "The Hindu", "https://www.thehindu.com/news/national/feeder/default.rss"),
    ("IN", "Times of India", "https://timesofindia.indiatimes.com/rssfeedstopstories.cms"),
    ("IN", "NDTV Top", "https://feeds.feedburner.com/ndtvnews-top-stories"),
    ("DE", "DW English", "https://rss.dw.com/rdf/rss-en-all"),
    ("DE", "SPIEGEL", "https://www.spiegel.de/schlagzeilen/index.rss"),
    ("FR", "Le Monde", "https://www.lemonde.fr/rss/une.xml"),
    ("FR", "France 24 EN", "https://www.france24.com/en/rss"),
    ("JP", "NHK World", "https://www3.nhk.or.jp/rss/news/cat0.xml"),
    ("JP", "Japan Times", "https://www.japantimes.co.jp/feed/"),
    ("QA", "Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("IE", "RTÉ News", "https://www.rte.ie/news/rss/news-headlines.xml"),
    ("NZ", "RNZ News", "https://www.rnz.co.nz/rss/national.xml"),
    ("ZA", "News24", "https://feeds.news24.com/articles/news24/TopStories/rss"),
    ("SG", "CNA", "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml"),
    ("PK", "Dawn", "https://www.dawn.com/feeds/home"),
    ("NG", "Premium Times", "https://www.premiumtimesng.com/feed"),
    ("MX", "Mexico News Daily", "https://mexiconewsdaily.com/feed/"),
    ("BR", "Agência Brasil EN", "https://agenciabrasil.ebc.com.br/en/rss/feed.xml"),
    ("KR", "Korea Herald", "http://www.koreaherald.com/common/rss/rss.php"),
    # Alternates for failed / extra coverage
    ("NZ", "NZ Herald", "https://www.nzherald.co.nz/arc/outboundfeeds/rss/?outputType=xml"),
    ("ZA", "Mail & Guardian", "https://mg.co.za/feed/"),
    ("BR", "Reuters World", "https://www.reuters.com/rssFeed/worldNews"),
    ("KR", "KBS World", "https://world.kbs.co.kr/rss/rss_english.htm"),
    ("ES", "El País (EN)", "https://feeds.elpais.com/mrss-s/pages/ep/site/english.elpais.com/portada"),
    ("IT", "ANSA English", "https://www.ansa.it/english/news/english_rss.xml"),
    ("NL", "NOS", "https://feeds.nos.nl/nosnieuwsalgemeen"),
    ("PH", "Inquirer", "https://newsinfo.inquirer.net/feed"),
    ("TH", "Bangkok Post", "https://www.bangkokpost.com/rss/data/topstories.xml"),
    ("MY", "Malay Mail", "https://www.malaymail.com/feed/rss"),
    ("CN", "SCMP", "https://www.scmp.com/rss/91/feed"),
    ("US", "USA Today", "https://rssfeeds.usatoday.com/usatoday-NewsTopStories"),
    ("US", "NBC News", "https://feeds.nbcnews.com/nbcnews/public/news"),
    ("CA", "Radio-Canada", "https://ici.radio-canada.ca/info/rss/nouvelle"),
]


async def probe(code: str, title: str, url: str) -> None:
    try:
        async with httpx.AsyncClient(
            timeout=20, follow_redirects=True, headers={"User-Agent": USER_AGENT}
        ) as client:
            response = await client.get(url)
            parsed = feedparser.parse(response.text)
            ok = (
                response.status_code == 200
                and is_valid_parsed_feed(parsed)
                and len(parsed.entries) >= 3
            )
            mark = "OK" if ok else "NO"
            print(
                f"{mark:2} {code} {title:22} entries={len(parsed.entries):3} "
                f"status={response.status_code} {url[:70]}"
            )
            if not ok and parsed.bozo_exception:
                print(f"   bozo: {parsed.bozo_exception}")
    except Exception as exc:
        print(f"NO {code} {title:22} ERROR {exc}")


async def main() -> None:
    for item in CANDIDATES:
        await probe(*item)


if __name__ == "__main__":
    asyncio.run(main())
