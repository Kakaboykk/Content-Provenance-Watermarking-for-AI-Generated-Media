# Phase 6 Provider Implementation

## 1. Stability AI Integration (Generation)

- **File**: `backend/app/services/ai_providers/stability_provider.py`
- **Class**: `StabilityProvider(BaseAIProvider)`
- **Configuration**: Uses `AI_API_KEY` and `AI_MODEL`. The default model is `sd3.5-flash`.
- **Implementation**: Uses `httpx.AsyncClient` to call `https://api.stability.ai/v2beta/stable-image/generate/sd3`. It requests width=512, height=512, and `output_format=jpeg` as per the requirements.
- **Validation**: If the returned image is not exactly 512x512, it resizes the image.
- **Errors Handled**: HTTP 401 (Auth Failed), 402 (Insufficient Credits), 429 (Rate Limit), 500 (Server Error), and Timeout.

## 2. Sightengine Integration (Detection)

- **File**: `backend/app/services/ai_detectors/sightengine_detector.py`
- **Class**: `SightengineDetector(BaseAIDetector)`
- **Configuration**: Uses `SIGHTENGINE_API_USER` and `SIGHTENGINE_API_SECRET`.
- **Implementation**: Uses `httpx.AsyncClient` to call `https://api.sightengine.com/1.0/check.json`. Maps `ai_generated` to `AI_GENERATED` and `human` to `LIKELY_HUMAN` based on `AI_DETECTOR_THRESHOLD` (0.70).
- **Errors Handled**: HTTP 401, 402, 429, 500, Timeout, and malformed JSON payload.

## 3. Environment Variables

The `backend/.env.example` and `backend/app/core/config.py` have been updated:
```ini
AI_PROVIDER=stability
AI_API_KEY=
AI_MODEL=sd3.5-flash

AI_DETECTOR_PROVIDER=sightengine
SIGHTENGINE_API_USER=
SIGHTENGINE_API_SECRET=
AI_DETECTOR_THRESHOLD=0.70
```

## 4. API Flow

1. Client sends prompt to `POST /generate`.
2. `StabilityProvider` generates the image in JPEG format (if requested by Stability).
3. `POST /generate` reads the magic bytes and correctly responds with `image/jpeg` or `image/png`.
4. Client uploads the image to `POST /watermark/embed`.
5. The watermark route detects if the incoming image is a JPEG and converts it in-memory to a 512x512 RGB PNG image for the frozen watermark pipeline.

## 5. JPEG -> PNG Watermark Pipeline

The frozen watermark algorithm requires PNG bytes. Instead of modifying the core watermark logic, the conversion from JPEG to PNG happens at the HTTP routing boundary in `app/api/routes/watermark.py` immediately before calling `embed_watermark_in_bytes`.

## 6. AI Detection Independence

The AI detection logic in `SightengineDetector` remains entirely independent of the watermark verification flow. The frontend calls `POST /detect-ai` which independently consults Sightengine. The results (e.g. `AI_GENERATED 96%`) and the watermark results (e.g. `AUTHENTIC_UNMODIFIED`) are discrete signals.

## 7. Error Handling

Both new providers map specific HTTP responses (like 402 Insufficient credits) to meaningful exceptions (`AIGenerationError` or `PermissionError`) that translate to sensible `500` or `400` HTTP status codes at the API layer.

## 8. Testing

- 7 existing tests updated for dependency mocking.
- 10+ new tests introduced for `StabilityProvider` and `SightengineDetector` utilizing `unittest.mock.patch` for `httpx.AsyncClient.post`.
- All backend tests run and pass without requiring live API keys.
- Frontend build passes via Vite + TypeScript (`npm run build`).

## 9. Live Test Results

A full live test of Stability AI and Sightengine could not be run because no explicit valid API credentials for Stability or Sightengine were provided in the `.env` settings. Mock providers were utilized to successfully run the `robustness_test.py` workflow which confirmed that the integrations preserve existing functionality intact. 

## 10. Known Limitations

- The Stability API will fail with HTTP 402 if credits run out. The backend correctly relays this.
- False Authenticity claims (T2, T8) in the custom watermark remain by design (they were part of the frozen Phase 5B codebase).

## 11. Free-Credit Limitations

- Stability AI offers a one-time 25 credits.
- Sightengine offers 2,000 monthly free detections.
If `AI_API_KEY` runs out of credits, it must be replaced manually. 

## 12. Security Considerations

- Sightengine requires a user identifier and a secret key, both added to the server `.env` exclusively.
- API keys are completely stripped from any error messages bubbled up to the API consumer.
