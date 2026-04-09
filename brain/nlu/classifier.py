from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from math import sqrt

from brain.nlu.schema import AVAILABLE_INTENTS


@dataclass(slots=True)
class ClassificationResult:
    intent: str
    confidence: float
    source: str


class IntentClassifier:
    """Hybrid classifier: optional sentence embeddings + lightweight keyword scoring."""

    def __init__(self) -> None:
        self._embedder = None
        self._prototypes: dict[str, list[str]] = {
            "open_app": ["open chrome", "launch vscode", "start spotify"],
            "set_volume": ["set volume to 50", "volume 20 percent"],
            "volume_up": ["increase volume", "turn it louder"],
            "volume_down": ["decrease volume", "turn it quieter"],
            "set_brightness": ["set brightness to 60", "brightness 30"],
            "brightness_up": ["increase brightness"],
            "brightness_down": ["decrease brightness"],
            "play_music": ["play some music"],
            "stop_music": ["stop music"],
            "play_youtube": ["play lofi on youtube"],
            "search_youtube": ["search youtube for trailers"],
            "get_weather": ["weather in london"],
            "get_news": ["latest technology news"],
            "get_time": ["what time is it"],
            "get_date": ["what is today date"],
            "get_crypto_price": ["price of bitcoin in usd"],
            "check_price_alert": ["alert me when bitcoin is above 100000"],
            "schedule_task": ["remind me in 10 minutes"],
            "take_screenshot": ["take screenshot"],
            "evaluate_trigger": ["if battery low then notify me"],
            "apply_rules": ["apply automation rules"],
            "chat": ["why is the sky blue", "tell me a story"],
        }
        self._pattern_hints: list[tuple[re.Pattern[str], str, float]] = [
            (re.compile(r"\b(weather|temperature|forecast)\b"), "get_weather", 0.83),
            (re.compile(r"\b(news|headlines|top stories)\b"), "get_news", 0.81),
            (re.compile(r"\b(open|launch|start)\b"), "open_app", 0.73),
            (re.compile(r"\b(youtube|yt)\b.*\b(play|watch)\b|\b(play|watch)\b.*\b(youtube|yt)\b"), "play_youtube", 0.82),
            (re.compile(r"\b(search|find|look up)\b.*\b(youtube|yt)\b"), "search_youtube", 0.82),
            (re.compile(r"\b(what\s+time|current\s+time|time\s+now)\b"), "get_time", 0.9),
            (re.compile(r"\b(what\s+date|today\'?s\s+date|current\s+date)\b"), "get_date", 0.9),
            (re.compile(r"\b(play|start)\b.*\b(music|song|playlist)\b"), "play_music", 0.82),
            (re.compile(r"\b(stop|pause)\b.*\b(music|song|playlist)\b"), "stop_music", 0.82),
            (re.compile(r"\b(volume)\b.*\b(set|to|percent|%)\b"), "set_volume", 0.8),
            (re.compile(r"\b(brightness)\b.*\b(set|to|percent|%)\b"), "set_brightness", 0.8),
            (re.compile(r"\b(crypto|bitcoin|ethereum|btc|eth|doge)\b"), "get_crypto_price", 0.78),
            (re.compile(r"\b(remind|schedule|timer|after|in)\b.*\b(second|minute|hour)\b"), "schedule_task", 0.81),
            (re.compile(r"\b(screenshot|screen shot|take a snap)\b"), "take_screenshot", 0.86),
        ]

        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            self._prototype_vectors = {
                name: self._embedder.encode(samples) for name, samples in self._prototypes.items()
            }
        except Exception:
            self._embedder = None
            self._prototype_vectors = {}

    def classify(self, text: str, normalized: str) -> ClassificationResult:
        if self._embedder:
            emb = self._embedder.encode([text])[0]
            best_intent = "chat"
            best_sim = -1.0
            for intent, vectors in self._prototype_vectors.items():
                sim = max(self._cosine(emb, v) for v in vectors)
                if sim > best_sim:
                    best_sim = sim
                    best_intent = intent
            confidence = max(0.0, min(0.97, 0.55 + (best_sim * 0.4)))
            return ClassificationResult(best_intent, confidence, "embedding_classifier")

        for pattern, intent, conf in self._pattern_hints:
            if pattern.search(normalized):
                return ClassificationResult(intent, conf, "keyword_classifier")

        tokens = set(normalized.split())
        best_intent = "chat"
        best_score = 0.0
        for intent, samples in self._prototypes.items():
            score = max(self._token_overlap(tokens, self._tokenize(sample)) for sample in samples)
            if score > best_score:
                best_score = score
                best_intent = intent

        confidence = 0.35 + (best_score * 0.45)
        if best_intent not in AVAILABLE_INTENTS:
            best_intent = "chat"
            confidence = 0.35
        return ClassificationResult(best_intent, max(0.0, min(0.92, confidence)), "lightweight_classifier")

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    @staticmethod
    def _token_overlap(left: set[str], right: set[str]) -> float:
        if not left or not right:
            return 0.0
        return len(left & right) / len(left | right)

    @staticmethod
    def _cosine(v1: Iterable[float], v2: Iterable[float]) -> float:
        a = list(v1)
        b = list(v2)
        dot = sum(x * y for x, y in zip(a, b))
        n1 = sqrt(sum(x * x for x in a))
        n2 = sqrt(sum(y * y for y in b))
        if not n1 or not n2:
            return 0.0
        return dot / (n1 * n2)
