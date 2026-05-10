"""
NLP Engine for ocean hazard detection.

Pipeline:
  1. Language detection
  2. Keyword matching (multilingual ocean-hazard vocabulary)
  3. Urgency / sentiment scoring
  4. Entity extraction (locations, hazard type, time references)
"""

import re
from typing import Optional
from loguru import logger

try:
    from langdetect import detect as detect_lang
except ImportError:
    detect_lang = None


# ──────────────────────────────────────────────
# Vocabulary
# ──────────────────────────────────────────────

HAZARD_KEYWORDS = {
    "en": {
        "tsunami": ["tsunami", "tidal wave", "seismic wave"],
        "storm_surge": ["storm surge", "storm tide", "surge"],
        "high_waves": ["high waves", "giant waves", "rough sea", "heavy swell"],
        "cyclone": ["cyclone", "hurricane", "typhoon", "tropical storm"],
        "flooding": ["flood", "inundation", "waterlogging"],
        "oil_spill": ["oil spill", "oil slick", "petroleum leak"],
        "algal_bloom": ["algal bloom", "red tide", "algae bloom", "green water"],
        "rogue_wave": ["rogue wave", "freak wave", "monster wave"],
        "waterspout": ["waterspout", "marine tornado"],
        "current": ["strong current", "rip current", "riptide"],
    },
    "hi": {
        "tsunami": ["सुनामी", "ज्वारीय लहर"],
        "cyclone": ["चक्रवात", "तूफान"],
        "high_waves": ["ऊँची लहरें", "विशाल लहरें"],
        "flooding": ["बाढ़", "जलभराव"],
        "storm_surge": ["तूफानी उफान"],
    },
    "ta": {
        "tsunami": ["சுனாமி", "அலை"],
        "cyclone": ["சூறாவளி", "புயல்"],
        "high_waves": ["உயர் அலைகள்"],
        "flooding": ["வெள்ளம்"],
    },
    "te": {
        "tsunami": ["సునామీ"],
        "cyclone": ["తుఫాను", "సైక్లోన్"],
        "flooding": ["వరద"],
    },
    "ml": {
        "tsunami": ["സൂനാമി"],
        "cyclone": ["ചുഴലിക്കാറ്"],
        "flooding": ["വെള്ളപ്പൊക്കം"],
    },
}

URGENCY_PATTERNS = [
    r"\b(emergency|SOS|mayday|help|danger|critical|evacuate|immediate|NOW)\b",
    r"\b(life|death|trapped|injured|stranded|rescue)\b",
]

LOCATION_PATTERNS = [
    r"\b(beach|coast|shore|port|harbour|bay|gulf|sea|ocean|island|creek|lagoon)\b",
]


# ──────────────────────────────────────────────
# Service
# ──────────────────────────────────────────────

class NLPService:
    def __init__(self):
        self._flat_keywords: dict[str, list[str]] = {}
        self._build_flat_keywords()

    def _build_flat_keywords(self):
        """Build a flat {hazard_type: [all multilingual keywords]} map."""
        for lang_vocab in HAZARD_KEYWORDS.values():
            for hazard, kws in lang_vocab.items():
                self._flat_keywords.setdefault(hazard, []).extend(kws)

    def _detect_language(self, text: str) -> str:
        if detect_lang:
            try:
                return detect_lang(text)
            except Exception:
                pass
        return "en"

    def _match_hazards(self, text: str) -> list[str]:
        text_lower = text.lower()
        found = []
        for hazard, kws in self._flat_keywords.items():
            if any(kw.lower() in text_lower for kw in kws):
                found.append(hazard)
        return found

    def _urgency_score(self, text: str) -> float:
        score = 0.0
        for pattern in URGENCY_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            score += len(matches) * 0.25
        # Normalise
        return min(score, 1.0)

    def _extract_entities(self, text: str, hazards: list[str]) -> dict:
        entities: dict = {"hazard_types": hazards, "locations": [], "time_refs": []}

        # Simple location extraction
        for pattern in LOCATION_PATTERNS:
            entities["locations"] += re.findall(pattern, text, re.IGNORECASE)

        # Simple time reference extraction
        time_pattern = r"\b(\d{1,2}:\d{2}|\d{1,2}\s*(?:am|pm)|yesterday|today|tonight|morning|evening|night)\b"
        entities["time_refs"] = re.findall(time_pattern, text, re.IGNORECASE)

        return entities

    async def analyze(self, text: str) -> dict:
        """Full NLP pipeline. Returns analysis dict."""
        try:
            language = self._detect_language(text)
            hazards  = self._match_hazards(text)
            urgency  = self._urgency_score(text)
            entities = self._extract_entities(text, hazards)

            return {
                "language": language,
                "hazard_types": hazards,
                "is_hazard_related": bool(hazards),
                "urgency_score": urgency,
                "entities": entities,
            }
        except Exception as e:
            logger.error(f"NLP analysis error: {e}")
            return {
                "language": "en",
                "hazard_types": [],
                "is_hazard_related": False,
                "urgency_score": 0.0,
                "entities": {},
            }

    async def analyze_social_post(self, text: str) -> dict:
        result = await self.analyze(text)
        result["sentiment_score"] = self._sentiment(text)
        return result

    def _sentiment(self, text: str) -> float:
        """Very simple rule-based sentiment (-1 to +1)."""
        positive_words = ["safe", "rescued", "cleared", "normal", "calm"]
        negative_words = ["dangerous", "fatal", "severe", "extreme", "dead", "casualties"]
        text_lower = text.lower()
        score = 0.0
        for w in positive_words:
            if w in text_lower:
                score += 0.2
        for w in negative_words:
            if w in text_lower:
                score -= 0.2
        return max(-1.0, min(1.0, score))


nlp_service = NLPService()
