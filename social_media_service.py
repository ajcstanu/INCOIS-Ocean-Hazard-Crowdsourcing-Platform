"""
Social media ingestion service.
Currently supports Twitter/X API v2.
"""

import httpx
from datetime import datetime, timedelta
from typing import Optional, List
from loguru import logger

from app.models.social_post import SocialPost, SocialPlatform
from app.services.nlp_service import nlp_service
from config.settings import settings


TWITTER_SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"
SEARCH_QUERY = (
    "(tsunami OR cyclone OR storm surge OR high waves OR coastal flood OR oil spill OR "
    "red tide OR waterspout OR riptide OR seismic wave) "
    "(sea OR ocean OR coast OR beach OR bay OR port) lang:en -is:retweet"
)


class SocialMediaService:

    async def fetch_twitter_posts(self, max_results: int = 100) -> List[dict]:
        if not settings.TWITTER_BEARER_TOKEN:
            logger.warning("Twitter bearer token not configured. Skipping.")
            return []

        headers = {"Authorization": f"Bearer {settings.TWITTER_BEARER_TOKEN}"}
        params = {
            "query": SEARCH_QUERY,
            "max_results": min(max_results, 100),
            "tweet.fields": "created_at,author_id,lang,public_metrics,geo",
            "expansions": "author_id",
            "user.fields": "username,name",
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(TWITTER_SEARCH_URL, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as e:
            logger.error(f"Twitter API error: {e}")
            return []

        tweets = data.get("data", [])
        users  = {u["id"]: u for u in data.get("includes", {}).get("users", [])}

        results = []
        for tweet in tweets:
            author = users.get(tweet.get("author_id", ""), {})
            metrics = tweet.get("public_metrics", {})
            results.append({
                "platform": SocialPlatform.TWITTER,
                "external_id": tweet["id"],
                "text": tweet["text"],
                "author_handle": author.get("username"),
                "author_name": author.get("name"),
                "url": f"https://twitter.com/i/web/status/{tweet['id']}",
                "posted_at": tweet.get("created_at"),
                "language": tweet.get("lang", "en"),
                "retweet_count": metrics.get("retweet_count", 0),
                "like_count": metrics.get("like_count", 0),
                "reply_count": metrics.get("reply_count", 0),
            })
        return results

    async def fetch_and_analyze(self) -> dict:
        """Fetch from all platforms, run NLP, persist new posts."""
        raw_posts = await self.fetch_twitter_posts()
        new_count = 0
        hazard_count = 0

        for raw in raw_posts:
            # Dedup check
            existing = await SocialPost.find_one(
                {"platform": raw["platform"], "external_id": raw["external_id"]}
            )
            if existing:
                continue

            # NLP
            nlp = await nlp_service.analyze_social_post(raw["text"])

            post = SocialPost(
                platform=raw["platform"],
                external_id=raw["external_id"],
                text=raw["text"],
                author_handle=raw.get("author_handle"),
                author_name=raw.get("author_name"),
                url=raw.get("url"),
                posted_at=datetime.fromisoformat(raw["posted_at"].replace("Z", "+00:00"))
                          if raw.get("posted_at") else None,
                language=raw.get("language", "en"),
                retweet_count=raw.get("retweet_count", 0),
                like_count=raw.get("like_count", 0),
                reply_count=raw.get("reply_count", 0),
                is_hazard_related=nlp["is_hazard_related"],
                hazard_types=nlp["hazard_types"],
                urgency_score=nlp["urgency_score"],
                sentiment_score=nlp.get("sentiment_score", 0.0),
                extracted_locations=nlp["entities"].get("locations", []),
                extracted_entities=nlp["entities"],
            )
            await post.insert()
            new_count += 1
            if nlp["is_hazard_related"]:
                hazard_count += 1

        logger.info(f"Social fetch: {new_count} new posts, {hazard_count} hazard-related")
        return {"new_posts": new_count, "hazard_posts": hazard_count}

    async def get_trends(
        self,
        platform: Optional[SocialPlatform] = None,
        hours: int = 24,
    ) -> dict:
        """Aggregate hazard trend stats."""
        since = datetime.utcnow() - timedelta(hours=hours)
        query: dict = {"is_hazard_related": True, "collected_at": {"$gte": since}}
        if platform:
            query["platform"] = platform

        posts = await SocialPost.find(query).to_list()
        if not posts:
            return {"total": 0, "by_hazard": {}, "top_posts": []}

        by_hazard: dict = {}
        for p in posts:
            for h in p.hazard_types:
                by_hazard[h] = by_hazard.get(h, 0) + 1

        top_posts = sorted(posts, key=lambda p: p.urgency_score, reverse=True)[:10]

        return {
            "total": len(posts),
            "by_hazard": by_hazard,
            "avg_urgency": round(sum(p.urgency_score for p in posts) / len(posts), 3),
            "top_posts": [
                {
                    "id": str(p.id),
                    "platform": p.platform,
                    "text": p.text[:200],
                    "urgency_score": p.urgency_score,
                    "url": p.url,
                }
                for p in top_posts
            ],
        }


social_service = SocialMediaService()
