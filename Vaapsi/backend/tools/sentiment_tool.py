from backend.models.domain import Language, SentimentLabel, SentimentRecord


NEGATIVE_TERMS = {"angry", "cancel", "fraud", "wrong", "late", "refuse", "nahi", "mat"}
POSITIVE_TERMS = {"yes", "haan", "ok", "redeliver", "available", "correct", "please"}
SUSPICIOUS_TERMS = {"never ordered", "free", "refund first", "otp", "change phone"}


class SentimentAnalyzer:
    async def analyze(self, text: str, language: Language) -> SentimentRecord:
        normalized = text.lower()
        if any(term in normalized for term in SUSPICIOUS_TERMS):
            return SentimentRecord(
                label=SentimentLabel.SUSPICIOUS,
                score=0.85,
                language=language,
                rationale="Buyer response contains suspicious intent markers.",
            )
        if any(term in normalized for term in NEGATIVE_TERMS):
            return SentimentRecord(
                label=SentimentLabel.NEGATIVE,
                score=0.72,
                language=language,
                rationale="Buyer response contains refusal or complaint markers.",
            )
        if any(term in normalized for term in POSITIVE_TERMS):
            return SentimentRecord(
                label=SentimentLabel.POSITIVE,
                score=0.78,
                language=language,
                rationale="Buyer response indicates cooperation.",
            )
        return SentimentRecord(
            label=SentimentLabel.NEUTRAL,
            score=0.55,
            language=language,
            rationale="No strong sentiment markers detected.",
        )
