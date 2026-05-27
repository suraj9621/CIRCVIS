"""Simple NLP helper service for CIRCVIS feedback and summary text generation."""

import re
from typing import Dict, List, Optional

CLASS_KEYWORDS = {
    "Plastic": ["plastic", "pet", "bottle", "wrapper", "poly"],
    "Glass": ["glass", "bottle", "jar", "pane", "shard"],
    "Paper/Cardboard": ["paper", "cardboard", "box", "sheet", "carton"],
    "Metal": ["metal", "tin", "can", "steel", "aluminum", "iron"],
    "Organic": ["organic", "food", "vegetable", "fruit", "waste", "compost"],
    "Textile": ["textile", "cloth", "fabric", "rag", "t-shirt", "garment"],
    "Miscellaneous": ["miscellaneous", "mixed", "other", "unknown", "trash"],
}

POSITIVE_WORDS = ["good", "great", "excellent", "accurate", "correct", "love", "nice", "helpful", "best"]
NEGATIVE_WORDS = ["wrong", "bad", "incorrect", "poor", "slow", "mistake", "hate", "problem", "fail", "issue"]

INTENT_KEYWORDS = {
    "correction": ["wrong", "incorrect", "misclassified", "mistake", "fix"],
    "performance": ["slow", "speed", "time", "latency", "delay"],
    "accuracy": ["accuracy", "accurate", "wrong", "correct", "precision"],
    "quality": ["better", "improve", "improvement", "enhance"],
    "report": ["report", "summary", "insight", "analysis"],
}


def _find_keywords(text: str, keywords: List[str]) -> bool:
    return any(re.search(rf"\b{re.escape(word)}\b", text) for word in keywords)


def analyze_feedback_text(text: Optional[str]) -> Dict[str, object]:
    if not text:
        return {
            "sentiment": "neutral",
            "sentiment_score": 0.0,
            "mentioned_classes": [],
            "intent": "general_feedback",
            "summary": "No feedback text provided.",
        }

    normalized = text.lower()
    score = sum(1 for w in POSITIVE_WORDS if _find_keywords(normalized, [w]))
    score -= sum(1 for w in NEGATIVE_WORDS if _find_keywords(normalized, [w]))

    sentiment = "neutral"
    if score >= 1:
        sentiment = "positive"
    elif score <= -1:
        sentiment = "negative"

    mentioned_classes = [category for category, keywords in CLASS_KEYWORDS.items() if _find_keywords(normalized, keywords)]
    mentioned_classes = list(dict.fromkeys(mentioned_classes))

    intent = "general_feedback"
    for intent_name, keywords in INTENT_KEYWORDS.items():
        if _find_keywords(normalized, keywords):
            intent = intent_name
            break

    summary_parts = []
    if sentiment != "neutral":
        summary_parts.append(f"The feedback tone is {sentiment}.")
    if mentioned_classes:
        summary_parts.append(f"It mentions classes: {', '.join(mentioned_classes)}.")
    if intent != "general_feedback":
        summary_parts.append(f"Detected intent: {intent}.")

    summary_text = " ".join(summary_parts) or "Feedback text contains general comments."

    return {
        "sentiment": sentiment,
        "sentiment_score": score,
        "mentioned_classes": mentioned_classes,
        "intent": intent,
        "summary": summary_text,
    }


def generate_nlp_summary(class_distribution: Dict[str, int], total_predictions: int = 0) -> str:
    if not class_distribution or total_predictions == 0:
        return "No prediction records available yet to generate a summary."

    sorted_classes = sorted(class_distribution.items(), key=lambda item: item[1], reverse=True)
    top_classes = sorted_classes[:2]
    top_text = ", ".join([f"{name} ({count})" for name, count in top_classes])

    rare_classes = [name for name, count in sorted_classes if count <= max(1, total_predictions // 20)]
    rare_text = "" if not rare_classes else f"Less frequent predictions include {', '.join(rare_classes)}."

    summary = (
        f"In the latest evaluation, CIRCVIS logged {total_predictions} predictions. "
        f"Top categories were {top_text}. "
        f"{rare_text} Overall the system is producing consistent class recognition results."
    )
    return summary.strip()
