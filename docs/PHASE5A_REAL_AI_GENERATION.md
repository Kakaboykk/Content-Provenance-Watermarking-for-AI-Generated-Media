# Phase 5A — Real AI Generation Implementation

This document covers the integration of a real AI image generation provider (Hugging Face) into the existing content provenance and watermarking pipeline.

## 1. Current Architecture
The AI Generation feature operates as a modular service. The `/generate` API endpoint delegates logic to a provider factory that instantiates a class inheriting from `BaseAIProvider`. The factory dynamically selects the provider based on the `AI_PROVIDER` environment variable.

## 2. Selected AI Provider
**Hugging Face Inference API**
We utilize the serverless Hugging Face Inference API via the official `huggingface_hub` `AsyncInferenceClient`. It supports dynamic model routing, robust error handling, and automatically handles image fetching and decoding using PIL before we safely convert it to PNG bytes.

## 3. Provider Model
- **Default Real Model**: `black-forest-labs/FLUX.1-schnell`
- Configurable via the `AI_MODEL` environment variable.

## 4. Environment Variables
Added to `backend/app/core/config.py` and `backend/.env.example`:
- `AI_PROVIDER` (e.g. `mock`, `huggingface`)
- `AI_API_KEY` (Your Hugging Face API token)
- `AI_MODEL` (e.g. `stabilityai/stable-diffusion-xl-base-1.0`)

## 5. Mock vs Real Provider
- **MockAIProvider**: Fallback mode. Simulates network delay, returns a local static synthetic image, and avoids consuming external rate limits. Always used automatically during Pytest automation.
- **HuggingFaceProvider**: Connects to the external Hugging Face server. Expects a valid API key.

## 6. API Flow
1. User submits text prompt to frontend.
2. Frontend sends JSON payload (`{ prompt: "..." }`) to `POST /generate`.
3. Backend determines the active provider (`settings.AI_PROVIDER`).
4. Provider executes the generation sequence (HTTP request to HF, or local simulation).
5. Resulting image bytes are safely checked, potentially converted to PNG if they arrive as WebP/JPEG, and immediately returned as a raw `image/png` HTTP Response.
6. Custom headers (`X-AI-Provider` and `X-AI-Model`) are attached to the response.

## 7. Error Handling
The provider implements robust error catching:
- **503**: Handles model loading states gracefully.
- **429**: Rate limiting.
- **401**: Missing or invalid API key configuration.
- **Timeout**: Handles stalled provider connections.

## 8. Test Results
- **Automated Tests**: 70 backend tests ran and passed (0 regressions).
- **Frontend Build**: Verified compatibility (`npm run build` passed).

## 9. Manual Verification
To manually test:
1. Copy `.env.example` to `.env` in the `backend` directory.
2. Provide your Hugging Face API key (`AI_API_KEY=hf_...`) and set `AI_PROVIDER=huggingface`.
3. Start the FastAPI backend: `uvicorn app.main:app --reload --port 8000`
4. Start the frontend: `npm run dev`
5. Type a prompt into the Generate page and verify the returned image is a unique AI generation, not the mock pattern.

## 10. Known Limitations
- The Hugging Face inference API might occasionally return a 503 error if the model needs to be loaded into memory. This takes ~20 seconds. The backend cleanly bubbles up this error to the frontend.
- Currently, format conversions are hard-coded to convert WebP/JPEG responses to PNG to ensure Phase 0-4 compatibility.
