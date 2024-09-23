from textblob import TextBlob

from src.engines.base import IModerationEngine


class TextBlobModerationEngine(IModerationEngine):
    def __init__(self, threshold: float) -> None:
        self.threshold = threshold

    def should_purge(self, text: str):
        return TextBlob(text).sentiment.polarity < self.threshold
