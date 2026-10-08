"""
backend/app/services/ai_detectors/huggingface_detector.py

Real AI detection provider using the Hugging Face Inference API.
Uses httpx directly to send raw image bytes with the correct Content-Type header.

Label/score mapping for dima806/ai_vs_real_image_detection:
  FAKE -> AI_GENERATED
  REAL -> LIKELY_HUMAN

Any label containing: fake, ai, artificial -> AI_GENERATED
Any label containing: real, human, natural -> LIKELY_HUMAN

Threshold behavior (AI_DETECTOR_THRESHOLD):
  ai_score   >= threshold  -> AI_GENERATED,  confidence = ai_score
  human_score >= threshold -> LIKELY_HUMAN,  confidence = human_score
  neither                  -> UNCERTAIN,     confidence = max(ai_score, human_score)
"""
import logging
import httpx
from fastapi import HTTPException, status

from .base import BaseAIDetector
from app.core.config import settings

logger = logging.getLogger(__name__)


class HuggingFaceDetector(BaseAIDetector):
    """
    Calls the Hugging Face Serverless Inference API directly via httpx to classify images.
    """
    def __init__(self):
        if not settings.AI_API_KEY:
            raise ValueError("AI_API_KEY is not configured for HuggingFaceDetector.")

        self.api_key = settings.AI_API_KEY
        self.model = settings.AI_DETECTOR_MODEL or "Nahrawy/AI-Vs-Human-Image-Detection"
        self.threshold = settings.AI_DETECTOR_THRESHOLD
        self.url = f"https://router.huggingface.co/hf-inference/models/{self.model}"

    def _classify_label(self, raw_label: str) -> str | None:
        """Map a raw model label string to our internal class. Returns None if unrecognised."""
        label = raw_label.lower()
        if "fake" in label or "ai" in label or "artificial" in label:
            return "AI"
        if "real" in label or "human" in label or "natural" in label:
            return "HUMAN"
        return None

    async def detect_image(self, image_bytes: bytes) -> dict:
        logger.info(f"[HuggingFaceDetector] Classifying image with model {self.model}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "image/jpeg",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.url,
                    headers=headers,
                    content=image_bytes,
                )

                if response.status_code != 200:
                    http_status = response.status_code
                    logger.error(f"Hugging Face HTTP error {http_status}: {response.text}")

                    if http_status == 401:
                        detail = "AI detection provider authentication failed."
                    elif http_status == 403:
                        detail = f"AI detection access forbidden for model '{self.model}'."
                    elif http_status == 429:
                        detail = "AI detection provider rate limit exceeded. Please try again later."
                    elif http_status == 503:
                        detail = "AI detection model is currently loading or unavailable."
                    elif http_status == 404:
                        detail = f"AI detection model '{self.model}' was not found."
                    elif http_status == 400:
                        detail = "AI detection provider rejected the request."
                    else:
                        detail = f"AI detection provider returned an error (HTTP {http_status})."

                    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)

                result = response.json()

            # Unwrap nested list format: [[{...}]] -> [{...}]
            if isinstance(result, list) and result and isinstance(result[0], list):
                result = result[0]

            if not result or not isinstance(result, list) or not isinstance(result[0], dict):
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="AI detection provider returned an unexpected response format.",
                )

            # ---------------------------------------------------------------
            # Extract ai_score and human_score from the FULL prediction list.
            # We search ALL predictions, not just result[0], because the model
            # may list REAL first when it is the highest-scoring class.
            # ---------------------------------------------------------------
            ai_score = 0.0
            human_score = 0.0
            unknown_labels: list[str] = []

            for prediction in result:
                raw_label = str(prediction.get("label", ""))
                score = float(prediction.get("score", 0.0))
                score = max(0.0, min(1.0, score))   # clamp to [0, 1]
                cls = self._classify_label(raw_label)
                if cls == "AI":
                    ai_score = max(ai_score, score)
                elif cls == "HUMAN":
                    human_score = max(human_score, score)
                else:
                    unknown_labels.append(raw_label)

            if unknown_labels:
                logger.warning(f"Unrecognised detector labels (ignored): {unknown_labels}")

            # ---------------------------------------------------------------
            # Apply threshold to determine the final label.
            # Confidence shown to the user always matches the displayed label.
            # ---------------------------------------------------------------
            if ai_score >= self.threshold:
                normalized_label = "AI_GENERATED"
                confidence = ai_score
            elif human_score >= self.threshold:
                normalized_label = "LIKELY_HUMAN"
                confidence = human_score
            else:
                normalized_label = "UNCERTAIN"
                confidence = max(ai_score, human_score)

            logger.info(
                f"[HuggingFaceDetector] ai_score={ai_score:.3f} human_score={human_score:.3f} "
                f"threshold={self.threshold} -> {normalized_label} ({confidence:.3f})"
            )

            return {
                "label": normalized_label,
                "confidence": confidence,
                "provider": "huggingface",
                "model": self.model,
            }

        except httpx.RequestError as e:
            logger.error(f"Hugging Face network error: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Network failure while contacting AI detection provider.",
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in HuggingFaceDetector: {e}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="An unexpected error occurred during AI detection.",
            )
