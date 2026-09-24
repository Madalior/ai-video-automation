"""
Caption Keyword Detector
========================
Routed through: llm_router.py (OpenRouter → NVIDIA NIM → Groq → Gemini fallback chain)

Decides which words in a transcript should be highlighted (neon green) in captions.
Applies a fast rules-based fallback if LLM fails.
"""

import re
import json
from typing import Optional


# ── Rules-based fallback (no LLM) ────────────────────────────────────────────

# Emotion/hook words that always pop in captions
ALWAYS_HIGHLIGHT = {
    "never", "always", "insane", "crazy", "literally", "actually",
    "honestly", "basically", "worst", "best", "biggest", "first",
    "last", "only", "every", "million", "billion", "thousand",
    "secret", "truth", "real", "fake", "free", "instantly",
    "immediately", "suddenly", "finally", "seriously", "absolutely",
    "incredible", "unbelievable", "impossible", "legendary", "viral",
    "shocking", "breaking", "exclusive", "rare", "hidden", "leaked",
}


class CaptionKeywordDetector:
    """
    Detects which words in a caption transcript should be highlighted.
    Returns a set of exact word strings (uppercase) to highlight.
    """

    def __init__(self):
        pass  # All LLM routing handled by llm_router.py

    def detect(self, words: list[dict], max_keywords: int = 6) -> set[str]:
        """
        Given a list of word dicts [{"text": "WORD", "start": 0.0, "end": 0.3}],
        returns a set of word texts (uppercase) that should be highlighted green.
        """
        if not words:
            return set()

        sentence = " ".join(w["text"] for w in words)

        # Try LLM first, fall back to rules-based
        result = self._detect_with_llm(sentence, max_keywords)
        if result:
            return result

        return self._detect_with_rules(words, max_keywords)

    def _detect_with_llm(self, sentence: str, max_keywords: int) -> Optional[set[str]]:
        """Ask the LLM which words to highlight in the caption."""
        prompt = f"""You are a viral short-form video editor.

Given this spoken caption text, pick up to {max_keywords} words to highlight in neon green.
Choose words that are:
- Proper nouns (people's names, places, brands)
- Numbers or statistics ("$1000", "3X", "100%")  
- Emotionally powerful words ("NEVER", "INSANE", "CRAZY", "BEST")
- The key subject word of the sentence
- Hook words that grab attention

Caption text: "{sentence}"

Return ONLY a JSON object like this:
{{"keywords": ["WORD1", "WORD2", "WORD3"]}}

Rules:
- Return the words in UPPERCASE exactly as they appear
- Maximum {max_keywords} words
- Only return words that actually appear in the caption
- Do NOT add punctuation to the words"""

        try:
            from clipper.utils.llm_router import call_llm_with_fallback
            # We don't want to enforce JSON response_format since different models might not support it natively
            # but we can try parsing the text since the prompt asks for JSON.
            content = call_llm_with_fallback(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=150
            )
            
            # Basic cleanup in case model returns markdown
            if "```" in content:
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
                if match:
                    content = match.group(1)
                else:
                    content = content.replace("```json", "").replace("```", "").strip()

            data = json.loads(content)
            keywords = data.get("keywords", [])

            # Clean and uppercase
            result = set()
            for kw in keywords:
                clean = re.sub(r"[^\w]", "", str(kw)).upper()
                if clean:
                    result.add(clean)

            print(f"[KEYWORDS] LLM detected: {result}")
            return result if result else None

        except Exception as e:
            print(f"[KEYWORDS] LLM failed: {e}. Using rules fallback.")
            return None

    def _detect_with_rules(self, words: list[dict], max_keywords: int) -> set[str]:
        """
        Fast rules-based fallback:
        1. Proper nouns (original text starts with uppercase)
        2. Numbers/stats
        3. Known emotional trigger words
        """
        result = set()

        for w in words:
            original = w.get("text", "").strip()
            clean = re.sub(r"[^\w]", "", original).upper()

            if not clean:
                continue

            # Proper noun: original word starts with uppercase letter
            if original and original[0].isupper() and len(original) > 1:
                result.add(clean)

            # Numbers or stats ($100, 3X, 50%)
            if re.search(r"\d", original):
                result.add(clean)

            # Emotional trigger words
            if clean.lower() in ALWAYS_HIGHLIGHT:
                result.add(clean)

            if len(result) >= max_keywords:
                break

        print(f"[KEYWORDS] Rules detected: {result}")
        return result
