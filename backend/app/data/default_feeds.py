from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NewsCountry:
    code: str
    name: str


@dataclass(frozen=True, slots=True)
class DefaultOutlet:
    url: str
    title: str
    country_code: str
    language: str = "en"
    default_selected: bool = True


# RSS URLs verified against feedparser + is_valid_parsed_feed (see scripts/probe_catalog_feeds.py).
NEWS_COUNTRIES: tuple[NewsCountry, ...] = (
    NewsCountry("CA", "Canada"),
    NewsCountry("US", "United States"),
    NewsCountry("GB", "United Kingdom"),
    NewsCountry("AU", "Australia"),
    NewsCountry("BD", "Bangladesh"),
    NewsCountry("IN", "India"),
    NewsCountry("DE", "Germany"),
    NewsCountry("FR", "France"),
    NewsCountry("JP", "Japan"),
    NewsCountry("WW", "International"),
    NewsCountry("IE", "Ireland"),
    NewsCountry("NZ", "New Zealand"),
    NewsCountry("ZA", "South Africa"),
    NewsCountry("SG", "Singapore"),
    NewsCountry("PK", "Pakistan"),
    NewsCountry("NG", "Nigeria"),
    NewsCountry("MX", "Mexico"),
    NewsCountry("ES", "Spain"),
    NewsCountry("IT", "Italy"),
    NewsCountry("NL", "Netherlands"),
    NewsCountry("PH", "Philippines"),
    NewsCountry("TH", "Thailand"),
    NewsCountry("MY", "Malaysia"),
    NewsCountry("HK", "Hong Kong"),
    NewsCountry("BR", "Brazil"),
)

DEFAULT_NEWS_OUTLETS: tuple[DefaultOutlet, ...] = (
    # Canada
    DefaultOutlet(
        url="https://www.cbc.ca/webfeed/rss/rss-topstories",
        title="CBC News",
        country_code="CA",
    ),
    DefaultOutlet(
        url="https://globalnews.ca/feed/",
        title="Global News",
        country_code="CA",
    ),
    DefaultOutlet(
        url="https://nationalpost.com/feed",
        title="National Post",
        country_code="CA",
        default_selected=False,
    ),
    DefaultOutlet(
        url="https://www.thestar.com/search/?f=rss",
        title="Toronto Star",
        country_code="CA",
        default_selected=False,
    ),
    # United States
    DefaultOutlet(
        url="https://feeds.npr.org/1001/rss.xml",
        title="NPR News",
        country_code="US",
    ),
    DefaultOutlet(
        url="https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
        title="The New York Times",
        country_code="US",
    ),
    DefaultOutlet(
        url="http://rss.cnn.com/rss/cnn_topstories.rss",
        title="CNN",
        country_code="US",
        default_selected=False,
    ),
    DefaultOutlet(
        url="https://feeds.washingtonpost.com/rss/national",
        title="The Washington Post",
        country_code="US",
        default_selected=False,
    ),
    DefaultOutlet(
        url="https://feeds.nbcnews.com/nbcnews/public/news",
        title="NBC News",
        country_code="US",
        default_selected=False,
    ),
    # United Kingdom
    DefaultOutlet(
        url="http://feeds.bbci.co.uk/news/rss.xml",
        title="BBC News",
        country_code="GB",
    ),
    DefaultOutlet(
        url="https://www.theguardian.com/uk/rss",
        title="The Guardian",
        country_code="GB",
    ),
    DefaultOutlet(
        url="https://feeds.skynews.com/feeds/rss/home.xml",
        title="Sky News",
        country_code="GB",
        default_selected=False,
    ),
    DefaultOutlet(
        url="https://www.independent.co.uk/news/uk/rss",
        title="The Independent",
        country_code="GB",
        default_selected=False,
    ),
    # Australia
    DefaultOutlet(
        url="https://www.abc.net.au/news/feed/51120/rss.xml",
        title="ABC News",
        country_code="AU",
    ),
    DefaultOutlet(
        url="https://www.theguardian.com/australia-news/rss",
        title="The Guardian Australia",
        country_code="AU",
    ),
    DefaultOutlet(
        url="https://www.smh.com.au/rss/feed.xml",
        title="Sydney Morning Herald",
        country_code="AU",
        default_selected=False,
    ),
    # Bangladesh
    DefaultOutlet(
        url="https://www.thedailystar.net/rss.xml",
        title="The Daily Star",
        country_code="BD",
    ),
    DefaultOutlet(
        url="https://en.prothomalo.com/feed",
        title="Prothom Alo (English)",
        country_code="BD",
    ),
    DefaultOutlet(
        url="https://www.dhakatribune.com/feed/",
        title="Dhaka Tribune",
        country_code="BD",
        default_selected=False,
    ),
    # India
    DefaultOutlet(
        url="https://www.thehindu.com/news/national/feeder/default.rss",
        title="The Hindu",
        country_code="IN",
    ),
    DefaultOutlet(
        url="https://feeds.feedburner.com/ndtvnews-top-stories",
        title="NDTV",
        country_code="IN",
    ),
    DefaultOutlet(
        url="https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        title="Times of India",
        country_code="IN",
        default_selected=False,
    ),
    # Germany
    DefaultOutlet(
        url="https://rss.dw.com/rdf/rss-en-all",
        title="Deutsche Welle (English)",
        country_code="DE",
    ),
    DefaultOutlet(
        url="https://www.spiegel.de/schlagzeilen/index.rss",
        title="Der Spiegel",
        country_code="DE",
        language="de",
    ),
    # France
    DefaultOutlet(
        url="https://www.lemonde.fr/rss/une.xml",
        title="Le Monde",
        country_code="FR",
        language="fr",
    ),
    DefaultOutlet(
        url="https://www.france24.com/en/rss",
        title="France 24 (English)",
        country_code="FR",
    ),
    # Japan
    DefaultOutlet(
        url="https://www3.nhk.or.jp/rss/news/cat0.xml",
        title="NHK World",
        country_code="JP",
    ),
    DefaultOutlet(
        url="https://www.japantimes.co.jp/feed/",
        title="The Japan Times",
        country_code="JP",
    ),
    # International
    DefaultOutlet(
        url="https://www.aljazeera.com/xml/rss/all.xml",
        title="Al Jazeera English",
        country_code="WW",
    ),
    # Ireland
    DefaultOutlet(
        url="https://www.rte.ie/news/rss/news-headlines.xml",
        title="RTÉ News",
        country_code="IE",
    ),
    # New Zealand
    DefaultOutlet(
        url="https://www.stuff.co.nz/rss",
        title="Stuff",
        country_code="NZ",
    ),
    # South Africa
    DefaultOutlet(
        url="https://rss.iol.io/iol/news",
        title="IOL",
        country_code="ZA",
    ),
    # Singapore
    DefaultOutlet(
        url="https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml",
        title="CNA",
        country_code="SG",
    ),
    # Pakistan
    DefaultOutlet(
        url="https://www.dawn.com/feeds/home",
        title="Dawn",
        country_code="PK",
    ),
    # Nigeria
    DefaultOutlet(
        url="https://www.premiumtimesng.com/feed",
        title="Premium Times",
        country_code="NG",
    ),
    # Mexico
    DefaultOutlet(
        url="https://mexiconewsdaily.com/feed/",
        title="Mexico News Daily",
        country_code="MX",
    ),
    # Spain
    DefaultOutlet(
        url="https://feeds.elpais.com/mrss-s/pages/ep/site/english.elpais.com/portada",
        title="El País (English)",
        country_code="ES",
    ),
    # Italy
    DefaultOutlet(
        url="https://www.ansa.it/english/news/english_rss.xml",
        title="ANSA (English)",
        country_code="IT",
    ),
    # Netherlands
    DefaultOutlet(
        url="https://feeds.nos.nl/nosnieuwsalgemeen",
        title="NOS",
        country_code="NL",
        language="nl",
    ),
    # Philippines
    DefaultOutlet(
        url="https://newsinfo.inquirer.net/feed",
        title="Philippine Daily Inquirer",
        country_code="PH",
    ),
    # Thailand
    DefaultOutlet(
        url="https://www.bangkokpost.com/rss/data/topstories.xml",
        title="Bangkok Post",
        country_code="TH",
    ),
    # Malaysia
    DefaultOutlet(
        url="https://www.malaymail.com/feed/rss",
        title="Malay Mail",
        country_code="MY",
    ),
    # Hong Kong
    DefaultOutlet(
        url="https://www.scmp.com/rss/91/feed",
        title="South China Morning Post",
        country_code="HK",
    ),
    # Brazil
    DefaultOutlet(
        url="https://g1.globo.com/rss/g1/",
        title="G1",
        country_code="BR",
        language="pt",
    ),
    DefaultOutlet(
        url="https://feeds.folha.uol.com.br/emcimadahora/rss091.xml",
        title="Folha de S.Paulo",
        country_code="BR",
        language="pt",
        default_selected=False,
    ),
)

_COUNTRY_BY_CODE = {country.code: country for country in NEWS_COUNTRIES}


def normalize_outlet_url(url: str) -> str:
    return url.strip().rstrip("/")


_OUTLET_BY_URL = {normalize_outlet_url(outlet.url): outlet for outlet in DEFAULT_NEWS_OUTLETS}


def get_outlet(url: str) -> DefaultOutlet | None:
    return _OUTLET_BY_URL.get(normalize_outlet_url(url))


def default_selected_urls() -> list[str]:
    return [outlet.url for outlet in DEFAULT_NEWS_OUTLETS if outlet.default_selected]


def resolve_outlets(urls: list[str]) -> list[DefaultOutlet]:
    seen: set[str] = set()
    resolved: list[DefaultOutlet] = []
    for raw in urls:
        normalized = normalize_outlet_url(raw)
        if not normalized or normalized in seen:
            continue
        outlet = get_outlet(normalized)
        if outlet is None:
            raise ValueError(f"Unknown outlet: {raw}")
        seen.add(normalized)
        resolved.append(outlet)
    return resolved


def country_for_code(code: str) -> NewsCountry | None:
    return _COUNTRY_BY_CODE.get(code.upper())
