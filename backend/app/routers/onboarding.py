from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.default_feeds import (
    DEFAULT_NEWS_OUTLETS,
    NEWS_COUNTRIES,
    default_selected_urls,
    normalize_outlet_url,
    resolve_outlets,
)
from app.database import get_db
from app.dependencies import get_current_user
from app.models.topic import Topic
from app.models.user import User
from app.schemas.auth import UserResponse
from app.services.default_feeds import seed_outlets
from app.services.feed_subscribe import subscribe_user_to_feed

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class DefaultOutletResponse(BaseModel):
    title: str
    region: str
    url: str


class CatalogOutletResponse(BaseModel):
    url: str
    title: str
    language: str
    default_selected: bool


class CatalogCountryResponse(BaseModel):
    code: str
    name: str
    outlets: list[CatalogOutletResponse]


class OnboardingCatalogResponse(BaseModel):
    countries: list[CatalogCountryResponse]
    default_selected_urls: list[str]


class OnboardingCompleteRequest(BaseModel):
    timezone: str
    topic_name: str = Field(default="Headlines", min_length=1, max_length=64)
    selected_outlet_urls: list[str] = Field(default_factory=list)
    extra_feed_url: str | None = None


def _build_catalog() -> OnboardingCatalogResponse:
    outlets_by_country: dict[str, list[CatalogOutletResponse]] = {
        country.code: [] for country in NEWS_COUNTRIES
    }
    for outlet in DEFAULT_NEWS_OUTLETS:
        outlets_by_country[outlet.country_code].append(
            CatalogOutletResponse(
                url=outlet.url,
                title=outlet.title,
                language=outlet.language,
                default_selected=outlet.default_selected,
            )
        )

    countries = [
        CatalogCountryResponse(code=country.code, name=country.name, outlets=outlets_by_country[country.code])
        for country in NEWS_COUNTRIES
        if outlets_by_country[country.code]
    ]
    return OnboardingCatalogResponse(
        countries=countries,
        default_selected_urls=default_selected_urls(),
    )


@router.get("/catalog", response_model=OnboardingCatalogResponse)
async def get_onboarding_catalog(user: User = Depends(get_current_user)):
    return _build_catalog()


@router.get("/defaults", response_model=list[DefaultOutletResponse])
async def list_default_outlets(user: User = Depends(get_current_user)):
    """Legacy flat list — region is the country name."""
    country_names = {country.code: country.name for country in NEWS_COUNTRIES}
    return [
        DefaultOutletResponse(
            title=outlet.title,
            region=country_names.get(outlet.country_code, outlet.country_code),
            url=outlet.url,
        )
        for outlet in DEFAULT_NEWS_OUTLETS
    ]


@router.post("/complete", response_model=UserResponse)
async def complete_onboarding(
    body: OnboardingCompleteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.onboarded:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already onboarded")

    extra = (body.extra_feed_url or "").strip()
    selected = [normalize_outlet_url(url) for url in body.selected_outlet_urls if url.strip()]

    if not selected and not extra:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Select at least one news outlet or add a custom source",
        )

    try:
        resolve_outlets(selected)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    user.timezone = body.timezone.strip() or "UTC"
    user.onboarded = True

    topic = Topic(user_id=user.id, name=body.topic_name.strip(), keywords="")
    db.add(topic)
    await db.flush()

    if selected:
        seeded = await seed_outlets(db, user, topic.id, selected)
        if not seeded and not extra:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not subscribe to any of the selected outlets. Try again or add a custom source.",
            )

    if extra:
        try:
            await subscribe_user_to_feed(db, user, url=extra, topic_ids=[topic.id])
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not add extra source: {exc}",
            ) from exc

    await db.commit()
    await db.refresh(user)
    return user
