# Phase 5B: AI-Generated Image Detection

## Objective
This phase introduces probabilistic AI-generated image detection to the Content Provenance & Watermarking platform. It is designed as an independent subsystem that supplements the deterministic watermark verification process, ensuring that the existing cryptographic provenance guarantees remain completely unaffected.

## Architecture
The new subsystem introduces an abstraction layer allowing for multiple detector implementations:
- `BaseAIDetector`: Abstract interface for all image detection providers.
- `MockAIDetector`: A deterministic provider used in automated tests and local development to prevent unintended live API requests.
- `HuggingFaceDetector`: The primary production implementation, leveraging the Hugging Face Inference API (`huggingface_hub.AsyncInferenceClient`) to invoke an image-classification model.

The `get_ai_detector()` provider factory dynamically returns the active detector based on environment configuration.

## Configuration
The detection subsystem introduces the following environment variables:
- `AI_DETECTOR_PROVIDER`: Configures the active provider (`mock` or `huggingface`).
- `AI_DETECTOR_MODEL`: Specifies the Hugging Face model repository. (Default: `Nahrawy/AI-Vs-Human-Image-Detection`).
- `AI_DETECTOR_THRESHOLD`: (Default: `0.70`) Defines the minimum confidence required to assert a classification. Below this, the output falls back to `UNCERTAIN`.

*(Authentication for the Hugging Face detector relies on the existing `AI_API_KEY`.)*

## API Endpoint
### `POST /detect-ai`
- **Description:** Analyzes an image file (multipart/form-data) and returns a probabilistic assessment.
- **Request:** `multipart/form-data` with a single file parameter `file`.
- **Response:**
  ```json
  {
      "label": "AI_GENERATED" | "LIKELY_HUMAN" | "UNCERTAIN",
      "confidence": 0.94,
      "provider": "huggingface",
      "model": "Nahrawy/AI-Vs-Human-Image-Detection"
  }
  ```

## Confidence & Mapping
The `HuggingFaceDetector` parses the highest scoring label from the `image_classification` task.
- Labels such as `ai`, `artificial`, or `fake` are mapped to `AI_GENERATED`.
- Labels such as `human`, `real`, or `natural` are mapped to `LIKELY_HUMAN`.
- If the model's confidence is below `AI_DETECTOR_THRESHOLD` (or if the label is unparseable), the result maps to `UNCERTAIN`.

## Error Handling
The subsystem handles various API failure scenarios gracefully (401, 403, 404, 429, 503, timeouts).
In the event of an API error, `detect_ai` will return a 5xx or 4xx HTTP response. The frontend uses `Promise.allSettled` to guarantee that the primary provenance verification continues to display, regardless of the detector's state.

## Frontend Integration
The `VerifyFlow.tsx` component triggers both `POST /verify` and `POST /detect-ai` in parallel.
The results are rendered as two distinct UI cards:
1. **Provenance Verification**: Deterministic match based on hidden watermark.
2. **AI Image Detection**: Probabilistic estimation of origin.

## Limitations
- **Probabilistic Nature**: AI detection models are fundamentally probabilistic and may generate false positives or false negatives. This result should NOT be considered cryptographic proof of origin.
- **Format Constraint**: `image_validation.py` enforces minimum dimensions (64x64) and acceptable mime-types (PNG, JPEG, WEBP, TIFF, BMP) before an image ever reaches the detection API.

## Manual Testing Commands
1. Start the backend with real AI features enabled:
   ```bash
   # Ensure .env has:
   # AI_DETECTOR_PROVIDER=huggingface
   # AI_API_KEY=hf_...
   uvicorn app.main:app --reload
   ```
2. Start the frontend:
   ```bash
   npm run dev
   ```
3. Open `http://localhost:5173` and navigate to the Verify tab.
4. Upload:
   - **Test 1**: An AI-generated image (from Phase 5A output). Check for `AI-GENERATED`.
   - **Test 2**: A real photograph captured via a standard camera. Check for `LIKELY HUMAN`.
   - **Test 3**: An unwatermarked external AI image. Provenance should show `NO WATERMARK` while detection shows `AI-GENERATED`.
   - **Test 4**: A generated, watermarked image. Provenance should show `AUTHENTIC & UNMODIFIED`, while detection shows `AI-GENERATED`.
