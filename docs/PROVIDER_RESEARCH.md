# Provider Research: AI Generation, Detection and Provenance
## Content Provenance Watermarking Project — Phase 6 Research

**Research Date:** October 2026
**Researcher:** Antigravity IDE (automated web research + codebase inspection)
**Status:** Research Only — No code has been modified

---

> [!IMPORTANT]
> This document is **research only**. No code modifications have been made.
> The existing watermark engine (DWT/DCT/QIM), provenance pipeline, and all Phase 0–5B
> implementations remain **frozen and untouched**.

---

## Table of Contents

1. [Project Context and Hard Constraints](#1-project-context-and-hard-constraints)
2. [Existing Architecture Summary](#2-existing-architecture-summary)
3. [Candidate AI Image Generation Providers](#3-candidate-ai-image-generation-providers)
4. [Candidate AI Detection Providers](#4-candidate-ai-detection-providers)
5. [Candidate Provenance / Watermark / C2PA Solutions](#5-candidate-provenance--watermark--c2pa-solutions)
6. [Master Comparison Table](#6-master-comparison-table)
7. [Free Credit Comparison](#7-free-credit-comparison)
8. [Pricing Comparison](#8-pricing-comparison)
9. [API Quality Comparison](#9-api-quality-comparison)
10. [Format and Resolution Compatibility](#10-format-and-resolution-compatibility)
11. [Watermark Robustness Analysis](#11-watermark-robustness-analysis)
12. [C2PA / Provenance Support Analysis](#12-c2pa--provenance-support-analysis)
13. [Detection Quality Considerations](#13-detection-quality-considerations)
14. [Integration Complexity](#14-integration-complexity)
15. [Reliability and Risks](#15-reliability-and-risks)
16. [Proposed Validation Test Plan](#16-proposed-validation-test-plan)
17. [Recommended Architecture](#17-recommended-architecture)
18. [Final Recommendations](#18-final-recommendations)
19. [Next Implementation Phase](#19-next-implementation-phase)
20. [Appendix: Official Provider URLs](#20-appendix-official-provider-urls)

---

## 1. Project Context and Hard Constraints

### 1.1 System Overview

This project is a multimedia content provenance system with a custom cryptographic watermarking engine. The system supports:

- **POST /generate** — AI image generation (via `ai_providers/` abstraction)
- **POST /watermark/embed** — Custom DWT/DCT/QIM watermark embedding
- **POST /verify** — Blind watermark extraction + SHA-256 hash comparison
- **POST /detect-ai** — Probabilistic AI-generated image detection (via `ai_detectors/` abstraction)
- **POST /upload** — Direct image upload workflow
- **PostgreSQL** — Provenance and verification record persistence

### 1.2 Hard Constraints (Non-Negotiable)

| Constraint | Detail |
|------------|--------|
| **512×512 PNG required** | The watermark engine operates on DWT of Y channel in a 512×512 image. Any generated image **must** be exactly 512×512 pixels (or resized to exactly 512×512 before watermarking). |
| **Frozen phases** | Watermark engine (Phase 0/1/1.5), provenance pipeline (Phase 2A/2B), AI integration layer (Phase 3), and detection (Phase 5B) must not be modified. |
| **Provider abstraction preserved** | New providers must implement `BaseAIProvider` or `BaseAIDetector` and register in factory `__init__.py`. |
| **Deterministic labeling** | AI detection must return `AI_GENERATED`, `LIKELY_HUMAN`, or `UNCERTAIN` with confidence 0.0–1.0. |
| **No combined analysis** | AI detection, watermark verification, SHA-256, and C2PA must remain **independent signals**. |
| **India access required** | API must be accessible from India without geo-restrictions. |
| **Student/demo budget** | Free credits must be verifiable and sufficient for demo. Credit card must not be mandatory just to get started. |

### 1.3 CRITICAL: Current Provider Status (As of October 2026)

> [!WARNING]
> **CRITICAL DISCOVERY 1 — Generation Provider BROKEN**
> The existing `HuggingFaceProvider` uses the legacy `api-inference.huggingface.co` endpoint
> with `black-forest-labs/FLUX.1-schnell`. This endpoint was **deprecated for FLUX models
> around July 2026**. The HuggingFace generation provider is non-functional. Replacement required.

> [!WARNING]
> **CRITICAL DISCOVERY 2 — Free Tier Gone**
> The HuggingFace legacy free tier (hundreds of requests per hour) is **gone**.
> Replaced by a credit system: only **$0.10/month** free credits — sufficient for ~1–2 generations only.

> [!WARNING]
> **CRITICAL DISCOVERY 3 — Detector Model May Be Unavailable**
> The detector model `Nahrawy/AI-Vs-Human-Image-Detection` may be renamed or made private.
> Research indicates only `Nahrawy/AIorNot` is confirmed active from that author.

---

## 2. Existing Architecture Summary

### 2.1 AI Provider Factory

```
backend/app/services/ai_providers/
├── __init__.py             ← Factory: get_ai_provider()
├── base.py                 ← BaseAIProvider (abstract)
│   └── generate_image(prompt) → (bytes, provider_name, model_name)
├── mock_provider.py        ← MockAIProvider (returns synthetic PNG)
└── huggingface_provider.py ← HuggingFaceProvider (BROKEN in 2026)
```

### 2.2 AI Detector Factory

```
backend/app/services/ai_detectors/
├── __init__.py              ← Factory: get_ai_detector()
├── base.py                  ← BaseAIDetector (abstract)
│   └── detect_image(bytes) → {label, confidence, provider, model}
├── mock_detector.py         ← MockAIDetector
└── huggingface_detector.py  ← HuggingFaceDetector (model may be unavailable)
```

### 2.3 Key Config Variables

| Variable | Current Default | Purpose |
|----------|----------------|---------|
| `AI_PROVIDER` | `mock` | Selects generation provider |
| `AI_API_KEY` | `None` | Shared API key |
| `AI_MODEL` | `black-forest-labs/FLUX.1-schnell` | Generation model |
| `AI_DETECTOR_PROVIDER` | `mock` | Selects detection provider |
| `AI_DETECTOR_MODEL` | `Nahrawy/AI-Vs-Human-Image-Detection` | Detection model |
| `AI_DETECTOR_THRESHOLD` | `0.70` | Classification confidence threshold |

### 2.4 Current Robustness Test Results (Phase 5B)

From `docs/ROBUSTNESS_TEST_REPORT.md` (generated 2026-09-22 using FLUX.1-schnell):

| Transform | Verdict | Notes |
|-----------|---------|-------|
| T0 Baseline | AUTHENTIC_UNMODIFIED | ✅ Expected |
| T1 Crop 25% | NO_WATERMARK_FOUND | ✅ Correct |
| T2 Resize 512×512 | AUTHENTIC_UNMODIFIED | ⚠ **FALSE CLAIM** (known issue) |
| T3 Resize 256×256 | NO_WATERMARK_FOUND | ✅ Correct |
| T4 JPEG Q=90 | TRACED_BUT_MODIFIED | ✅ Correct |
| T5–T7 JPEG Q=75–30 | NO_WATERMARK_FOUND | ✅ Correct |
| T8 Screenshot (PNG recopy) | AUTHENTIC_UNMODIFIED | ⚠ **FALSE CLAIM** (known issue) |
| T9–T11 Rotation | NO_WATERMARK_FOUND | ✅ Correct |
| T10 Rotate 180° | WATERMARK_UNRECOVERABLE | ✅ Correct |
| T12–T16 Flip/Brightness/Contrast | WATERMARK_UNRECOVERABLE | ✅ Correct |
| T17–T20 Contrast/Blur | NO_WATERMARK_FOUND | ✅ Correct |

**Known issues**: 2 false authenticity claims (T2, T8). This is a pre-existing characteristic of the watermark engine. It is outside the scope of this research.

---

## 3. Candidate AI Image Generation Providers

### 3.1 Hugging Face Inference API (CURRENT — BROKEN)

**Status: PARTIALLY SUPPORTED (broken for FLUX.1-schnell as of ~July 2026)**

| Property | Detail |
|----------|--------|
| **Free Credits** | ~$0.10/month (new credit system; old unlimited tier gone) |
| **Credit Card Required** | No, for the $0.10 monthly allocation |
| **FLUX via old endpoint** | ❌ DEPRECATED — `api-inference.huggingface.co` no longer routes FLUX |
| **FLUX via new Inference Providers** | Requires individual provider accounts (fal.ai, Replicate, etc.) |
| **512×512 output** | Configurable via PIL resize in existing code |
| **JPEG output** | Not directly; existing code converts to PNG |
| **India access** | ✅ Available |
| **API stability (2026)** | ⚠ Undergoing migration; endpoint URLs changed |

**Verdict**: The existing HuggingFace provider for image generation is **broken** as of ~July 2026. The legacy serverless inference API endpoint no longer supports FLUX models. **Replacement is required.**

AI Generation: BROKEN | AI Detection: N/A | Watermarking: NOT SUPPORTED | C2PA: NOT SUPPORTED

---

### 3.2 Stability AI Developer Platform

**Status: SUPPORTED — RECOMMENDED AS PRIMARY**

| Property | Detail |
|----------|--------|
| **Free Credits** | ✅ **25 credits on signup** (no credit card required, Google login) |
| **Credit Expiry** | Credits do not expire; part of account balance |
| **Monthly Free Quota** | ❌ No recurring free credits after initial 25 |
| **Credit Card Required to Start** | ❌ Not required for initial 25 credits |
| **Pay-as-you-go rate** | $1 USD = 100 credits |
| **SD3.5 Flash cost** | ~2.5 credits/image ≈ **10 images from 25 free credits** |
| **Stable Image Core cost** | ~3 credits/image ≈ 8 images from 25 free credits |
| **SD3.5 Medium cost** | ~3.5 credits/image ≈ 7 images from 25 free credits |
| **Stable Image Ultra cost** | ~8 credits/image ≈ 3 images from 25 free credits |
| **API type** | REST (v2beta), synchronous |
| **Output formats** | JPEG ✅, PNG ✅, WebP ✅ (via `output_format` param) |
| **512×512 output (SD3.5 Flash)** | ✅ Directly supported via `width=512, height=512` params |
| **512×512 output (Stable Image Core)** | ⚠ Min 640×640; requires Pillow resize post-generation |
| **India access** | ✅ No restrictions confirmed |
| **Python SDK** | ❌ No official Python SDK; use `httpx` REST calls |
| **Auth** | API key in `Authorization: Bearer` header |
| **Async support** | ❌ (synchronous) |
| **Typical latency** | 3–8 seconds |
| **Webhook** | Not required |
| **Recommended model** | `sd3.5-flash` (best free-credit efficiency + 512×512 support) |

AI Generation: SUPPORTED ✅ | AI Detection: NOT SUPPORTED | Watermarking: NOT SUPPORTED | C2PA: NOT SUPPORTED

**512×512 Compatibility**: SD3.5 Flash accepts `width=512, height=512` directly. Backend should apply Pillow resize as a safety fallback in provider code (same pattern as existing HuggingFace provider).

**Approx Demo Usage**: 25 credits ÷ 2.5 credits/image (SD3.5 Flash) = **~10 generations free**. At $0.025/image after that.

---

### 3.3 fal.ai

**Status: SUPPORTED (paid only — no confirmed free tier)**

| Property | Detail |
|----------|--------|
| **Free Credits** | Unconfirmed — occasional starter credits on signup; not guaranteed |
| **Recurring Free Tier** | ❌ None — fully prepaid credit model |
| **Credit Card Required** | ✅ Yes, to load credits |
| **FLUX models** | ✅ FLUX.1-dev, FLUX.1-schnell, FLUX Pro available |
| **Output format** | JPEG ✅, PNG ✅ |
| **512×512 output** | ✅ Configurable via `image_size` param |
| **India access** | ✅ Available |
| **API type** | REST, OpenAI-compatible |
| **Python SDK** | ✅ `fal-client` |
| **Async support** | ✅ (polling or webhook) |
| **Typical latency** | 3–10 seconds |

**Verdict**: Good API quality but **no confirmed free tier** as of October 2026. Requires credit card. **Not recommended as primary for student/demo.**

AI Generation: SUPPORTED | AI Detection: NOT SUPPORTED | Watermarking: NOT SUPPORTED | C2PA: NOT SUPPORTED

---

### 3.4 Replicate

**Status: SUPPORTED (paid only — no free tier)**

| Property | Detail |
|----------|--------|
| **Free Credits** | ❌ None — pay-as-you-go only |
| **Recurring Free Tier** | ❌ None |
| **Credit Card Required** | ✅ Yes |
| **FLUX.1-schnell cost** | $3.00 per 1,000 images = **$0.003/image** |
| **FLUX 1.1 Pro cost** | $0.04/image |
| **Output format** | JPEG ✅, PNG ✅ |
| **512×512 output** | ✅ Configurable |
| **India access** | ✅ Available |
| **API type** | REST |
| **Python SDK** | ✅ `replicate` |
| **Async support** | ✅ (polling) |

**Verdict**: Excellent price-to-quality ratio ($0.003/image for FLUX.1-schnell) but **no free tier**. Best backup provider once a small budget is available.

AI Generation: SUPPORTED | AI Detection: NOT SUPPORTED | Watermarking: NOT SUPPORTED | C2PA: NOT SUPPORTED

---

### 3.5 Together AI

**Status: SUPPORTED (paid only — no free tier)**

| Property | Detail |
|----------|--------|
| **Free Credits** | ❌ None — minimum $5 prepaid required |
| **Credit Card Required** | ✅ Yes |
| **FLUX models** | ✅ Available |
| **Output format** | JPEG ✅, PNG ✅ |
| **512×512 output** | ✅ Configurable |
| **India access** | ✅ Available |
| **Python SDK** | ✅ `together` |

**Verdict**: No free tier for students. **Not recommended.**

---

### 3.6 Fireworks AI

**Status: SUPPORTED (minimal trial credits only)**

| Property | Detail |
|----------|--------|
| **Free Credits** | ~$1 signup credit (historically), **not guaranteed** |
| **Recurring Free Tier** | ❌ None (prepaid model since July 2026) |
| **Credit Card Required** | ✅ Yes (for prepaid top-up) |
| **FLUX models** | ✅ Available |
| **512×512 output** | ✅ Configurable |
| **India access** | ✅ Available |

**Verdict**: Marginal trial credits — not sufficient for student demo. **Not recommended.**

---

### 3.7 Google Gemini / Imagen

**Status: PARTIALLY SUPPORTED**

| Property | Detail |
|----------|--------|
| **Free Credits** | Limited via Google AI Studio free tier |
| **API** | Vertex AI (enterprise) or Google AI Gemini API |
| **512×512 output** | Unknown; typically higher resolution |
| **India access** | ✅ |
| **Complexity** | Higher — requires Google Cloud account for Vertex |

**Verdict**: Viable but overcomplicated for a student/demo project. **Not recommended.**

---

## 4. Candidate AI Detection Providers

### 4.1 Hugging Face Detector (CURRENT — POTENTIALLY BROKEN)

**Status: UNCERTAIN**

| Property | Detail |
|----------|--------|
| **Model in use** | `Nahrawy/AI-Vs-Human-Image-Detection` |
| **Model status (2026)** | ⚠ Possibly renamed or private. `Nahrawy/AIorNot` is the known active model |
| **Free tier** | ~$0.10/month credits for inference |
| **Detection quality** | Unknown — community model, unverified accuracy |
| **Pixel-based analysis** | ✅ (image classification model) |
| **Per-generator attribution** | ❌ |
| **India access** | ✅ |

**Verdict**: Specific model `Nahrawy/AI-Vs-Human-Image-Detection` may no longer be available. Community models have unverified quality. **Replacement with Sightengine is required.**

---

### 4.2 Sightengine

**Status: SUPPORTED — RECOMMENDED AS PRIMARY**

| Property | Detail |
|----------|--------|
| **Free Credits** | ✅ **2,000 operations/month permanently** |
| **Daily Limit (Free)** | 500 operations/day |
| **Credit Card Required** | ❌ **Not required for free tier** |
| **Monthly Free Quota** | 2,000 ops/month (renews every month) |
| **Approx Free Detections** | ~2,000 images/month |
| **Pay-as-you-go** | Starter: $29/month for 10,000 ops; $0.002/op overage |
| **India access** | ✅ Confirmed, no restrictions |
| **API type** | REST (synchronous) |
| **Python SDK** | ✅ Official `sightengine` Python client |
| **File upload** | ✅ (multipart) and URL input |
| **JPEG support** | ✅ |
| **PNG support** | ✅ |
| **WebP support** | ✅ |
| **Async support** | ❌ (synchronous for images; async only for video) |
| **Typical latency** | < 1 second (synchronous) |
| **Detection type** | Pixel-based analysis — NOT metadata or watermark |
| **Per-generator attribution** | ✅ Individual scores for 20+ generators |
| **Generators detected** | DALL-E 3, Midjourney, Stable Diffusion, FLUX, Ideogram, Firefly, GPT-4o images, StyleGAN, Sora, Runway, Kling and others |
| **AI probability output** | ✅ (0.0–1.0 score) |
| **Human probability output** | ✅ |
| **Generator model info** | ✅ Per-generator attribution |
| **Documentation quality** | ✅ Excellent, with interactive request builder |
| **Webhook requirement** | ❌ Not required |
| **Auth** | API User + API Secret (two separate credentials) |

**AI Generation: NOT SUPPORTED**
**AI Detection: SUPPORTED** ✅
**C2PA/Provenance: NOT SUPPORTED**
**Watermark Detection: NOT SUPPORTED** (pixel AI detection only — architecturally correct)

**Sightengine API Endpoint (AI-generated image detection):**
```
POST https://api.sightengine.com/1.0/check.json
Params: models=genai, api_user=<user>, api_secret=<secret>
Body: media (multipart file) OR url (image URL)
```

**Example Response:**
```json
{
  "type": {
    "ai_generated": 0.97,
    "human": 0.03
  },
  "ai_generated_details": {
    "dalle": 0.02,
    "midjourney": 0.01,
    "stable_diffusion": 0.91,
    "flux": 0.95
  }
}
```

**Integration fit**: Excellent. A new `SightengineDetector(BaseAIDetector)` wraps this cleanly.
The `ai_generated` score maps to `AI_GENERATED`, `human` maps to `LIKELY_HUMAN`, threshold logic maps to `UNCERTAIN`.

**Note**: Sightengine uses two separate credentials (`SIGHTENGINE_API_USER` + `SIGHTENGINE_API_SECRET`) rather than a single bearer token. The `config.py` must be updated to add these two new optional settings.

---

### 4.3 Hive AI

**Status: PARTIALLY SUPPORTED**

| Property | Detail |
|----------|--------|
| **Free Credits** | $1 initial credit on signup; $100 bonus after adding payment + spending $5 |
| **Recurring Free Tier** | ❌ None (100 req/day rate limit for V3 self-serve) |
| **Credit Card Required** | ✅ Required for $100 bonus; $1 starter does not require CC |
| **India access** | ✅ (V3 self-serve API) |
| **API type** | REST |
| **Python SDK** | ✅ |
| **Detection quality** | Enterprise-grade; per-image scores |
| **Latency** | ~1–2 seconds |

**Verdict**: $1 starter is very minimal. The $100 bonus requires CC. V3 self-serve 100 req/day may be sufficient for a demo but the free offering is weak. **Backup option only.**

---

### 4.4 Illuminarty

**Status: PARTIALLY SUPPORTED**

| Property | Detail |
|----------|--------|
| **Free Credits** | ✅ Permanently free basic detection |
| **API Access on Free Tier** | ⚠ Basic only; 10,000 req/day requires $10/month Basic plan |
| **Credit Card Required** | ❌ Not required for basic free |
| **JPEG/PNG support** | ✅ |
| **Generator attribution** | ✅ (on paid tiers) |
| **India access** | Unknown |
| **API quality** | REST; documented |

**Verdict**: Free basic tier exists but API volume access requires paid plan. Less verified API quality. **Third backup option.**

---

### 4.5 Reality Defender

**Status: PARTIALLY SUPPORTED**

| Property | Detail |
|----------|--------|
| **Free Credits** | ✅ 50 scans/month permanently free |
| **Monthly Free Quota** | 50 scans/month |
| **Credit Card Required** | ❌ Not required for free tier |
| **Business plan** | $399/month for 1,000 scans |
| **API access on free** | ✅ (included) |
| **India access** | Unknown |
| **Detection quality** | Multi-model ensemble; forensic heatmaps |

**Verdict**: 50 scans/month is very restrictive for demo/development. Enterprise tool, not student-suitable. **Not recommended.**

---

### 4.6 Winston AI

**Status: PARTIALLY SUPPORTED (TEXT-FOCUSED)**

| Property | Detail |
|----------|--------|
| **Free Credits** | 14-day trial with 2,000 credits |
| **Recurring Free Tier** | ❌ None |
| **API for image detection** | ⚠ Primarily text AI detection; image/deepfake detection is secondary |
| **Paid plans** | $10–$49/month |

**Verdict**: Primarily a text AI detection tool. Image detection is a secondary feature. **Not recommended for this project.**

---

## 5. Candidate Provenance / Watermark / C2PA Solutions

### 5.1 C2PA Open-Source SDKs (CAI / ContentAuth)

**Status: PARTIALLY SUPPORTED — Best Available Option for C2PA**

| Property | Detail |
|----------|--------|
| **Cost** | ✅ Free / Open source |
| **Python library** | ✅ `c2pa-python` (pip install c2pa-python) |
| **What it does** | Read/verify C2PA manifests; validate cryptographic signatures; extract provenance assertions; embed C2PA manifests |
| **What it does NOT do** | Does not embed invisible pixel watermarks; cannot detect C2PA if metadata was stripped |
| **JPEG support** | ✅ (primary format) |
| **PNG support** | ✅ |
| **WebP support** | ✅ |
| **Robustness to JPEG compression** | ❌ C2PA metadata is stripped by re-encoding |
| **Robustness to resize/crop** | ❌ Metadata stripping is routine |
| **India access** | ✅ Open source, no geo-restriction |
| **Dependency** | Rust bindings (may require special installation) |

**Important Capability Distinction:**

| C2PA CAN | C2PA CANNOT |
|----------|-------------|
| Embed signed provenance into JPEG/PNG at generation time | Detect its own presence if metadata was stripped |
| Verify signature later if manifest is intact | Survive JPEG re-encoding or social media upload |
| Detect tampering if manifest is present | Analyze pixels |
| Create interoperability with Adobe tools and browsers | Supplement our custom watermark for robustness |

**C2PA is metadata, NOT steganographic watermarking.** It does not analyze pixels and does not survive the transformations that matter most for watermark robustness.

**Integration potential**: `c2pa-python` could optionally embed a C2PA manifest during `POST /watermark/embed`. The manifest would cross-reference our provenance UUID, prompt, model, and timestamp — creating a standards-compliant second provenance layer for demo value.

**Conclusion**: C2PA is **optional** for this project. If implemented, it must be purely additive and must not interfere with any existing watermark pipeline code.

---

### 5.2 External Invisible Watermarking APIs

**Research finding**: As of October 2026, there is **no widely available, free, commercial invisible watermarking API** that:
- Embeds steganographic watermarks into arbitrary uploaded images
- Reads/verifies them back
- Survives JPEG compression, cropping, and resizing
- Is accessible without enterprise-level contracts

**SynthID (Google DeepMind)**: State-of-the-art invisible watermark.
- ✅ Available for text watermarking via Vertex AI
- ❌ NOT publicly available as a standalone image watermarking API for arbitrary images
- Only embeds watermarks in Imagen-generated images on Google's own infrastructure

**Verdict**: There is **no external invisible watermarking provider** that can usefully supplement our custom watermark for this project. Our custom DWT/DCT/QIM watermark is the correct and necessary approach.

---

### 5.3 Stability AI / Hugging Face Provider-Native Provenance

**Status: NOT SUPPORTED**

Neither Stability AI nor HuggingFace Inference Providers attach C2PA or proprietary provenance metadata to generated images. Not applicable.

---

## 6. Master Comparison Table

| Provider | Purpose | Free Credits | CC Required | Approx Free Usage | API | JPEG | PNG | AI Detection | Custom WM | C2PA | Recommendation |
|----------|---------|--------------|-------------|-------------------|-----|------|-----|--------------|-----------|------|----------------|
| **HuggingFace (Gen)** | Generation | $0.10/mo | No | ~1–2 imgs/mo | REST+SDK | No (PNG) | ✅ | N/A | N/A | N/A | ❌ BROKEN |
| **Stability AI SD3.5 Flash** | Generation | 25 credits | No | ~10 images | REST | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ **PRIMARY GEN** |
| **Replicate FLUX.1-schnell** | Generation | None | Yes | — | REST+SDK | ✅ | ✅ | ❌ | ❌ | ❌ | 🔵 Backup |
| **fal.ai** | Generation | Unconfirmed | Yes | — | REST+SDK | ✅ | ✅ | ❌ | ❌ | ❌ | 🔵 Backup |
| **Together AI** | Generation | None | Yes | — | REST+SDK | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ Not suitable |
| **Fireworks AI** | Generation | ~$1 | Yes | ~few imgs | REST+SDK | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ Not suitable |
| **Google Gemini/Imagen** | Generation | Limited | No | Limited | REST+SDK | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ Too complex |
| **HuggingFace (Detect)** | Detection | $0.10/mo | No | ~few imgs | REST | ✅ | ✅ | ⚠ Uncertain | ❌ | ❌ | ⚠ Broken/Backup |
| **Sightengine** | Detection | 2,000/mo | No | ~2,000 imgs/mo | REST+SDK | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ **PRIMARY DETECT** |
| **Reality Defender** | Detection | 50/mo | No | ~50 scans/mo | REST | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ Too restrictive |
| **Hive AI** | Detection | $1 + CC | Partial | ~very few | REST+SDK | ✅ | ✅ | ✅ | ❌ | ❌ | 🔵 Backup |
| **Illuminarty** | Detection | Basic free | No | Unknown | REST | ✅ | ✅ | ✅ | ❌ | ❌ | 🔵 Third backup |
| **Winston AI** | Detection | 14-day trial | Unknown | ~2,000 (trial) | REST | ✅ | ✅ | ⚠ Partial | ❌ | ❌ | ❌ Not suitable |
| **c2pa-python** | C2PA/Provenance | Free (OS) | No | Unlimited | Local lib | ✅ | ✅ | ❌ | ❌ | ✅ | 🔵 Optional |
| **SynthID** | Invisible WM | Unavailable | N/A | N/A | Unavailable | — | — | ❌ | — | — | ❌ Not available |

**Legend**: ✅ Supported | ❌ Not Supported | ⚠ Partial/Uncertain | 🔵 Backup | N/A Not applicable

---

## 7. Free Credit Comparison

| Provider | Free Credits | Recurring | No CC to Start | Approx Demo Value |
|----------|-------------|-----------|----------------|-------------------|
| **Stability AI** | 25 credits | ❌ One-time | ✅ Yes | **~10 generations (SD3.5 Flash)** |
| Hugging Face (Gen) | $0.10/month | ✅ Monthly | ✅ Yes | ~1–2 generations (model-dependent) |
| fal.ai | Unconfirmed | ❌ | Possibly | Unknown |
| Replicate | None | ❌ | ❌ CC required | 0 |
| Together AI | None | ❌ | ❌ CC required | 0 |
| Fireworks AI | ~$1 | ❌ | ❌ CC for top-up | ~few images |
| Google Gemini | Limited quota | ✅ | ✅ | Variable |
| **Sightengine** | **2,000/month** | **✅ Monthly** | **✅ No CC** | **~2,000 detections/month** |
| Hive AI | $1 starter | ❌ | ✅ for $1 starter | ~few detections |
| Illuminarty | Basic free | ✅ | ✅ | Limited |
| Reality Defender | 50/month | ✅ | ✅ | 50 scans/month |
| Winston AI | 2,000 (14-day) | ❌ | Unknown | Trial only |
| c2pa-python | Free (OS) | ✅ | ✅ | Unlimited |

> [!NOTE]
> **Sightengine has by far the most generous detection free tier**: 2,000 operations/month
> with **no credit card required** and permanent (not trial) access. This is ideal for a
> student/demo project.
> **Stability AI** is the best generation option: 25 free credits with no CC, ~10 images free.

---

## 8. Pricing Comparison

### AI Image Generation (Pay-as-you-go after free credits)

| Provider | Per Image (Approx) | Notes |
|----------|-------------------|-------|
| Replicate FLUX.1-schnell | $0.003/image | Cheapest quality option |
| fal.ai FLUX.1-schnell | ~$0.003–0.005/image | Model-dependent |
| Stability AI SD3.5 Flash | $0.025/image (2.5 credits) | Best image quality for this project |
| Stability AI Stable Image Core | $0.03/image (3 credits) | |
| Stability AI SD3.5 Medium | $0.035/image (3.5 credits) | |
| Together AI FLUX | ~$0.015–0.025/image | |
| Stability AI Stable Image Ultra | $0.08/image (8 credits) | Highest quality, most expensive |

### AI Detection (Pay-as-you-go after free credits)

| Provider | Per Detection | After Free Credits |
|----------|--------------|-------------------|
| Sightengine | $0 for first 2,000/month | $0.002/op (Starter: $29/mo for 10,000) |
| Illuminarty | $0 basic | $10/month Basic for 10,000/day |
| Hive AI V3 | Usage-based | Custom |
| Reality Defender | $0 for 50/month | $399/month for 1,000 |

---

## 9. API Quality Comparison

### AI Generation Providers

| Provider | REST | Python SDK | Async | File Upload | JPEG Out | PNG Out | 512×512 | Sync/Async | Webhook |
|----------|------|-----------|-------|-------------|----------|---------|---------|------------|---------|
| Stability AI | ✅ | ❌ (httpx) | ❌ | N/A | ✅ | ✅ | ✅ SD3.5 Flash | Sync | No |
| Replicate | ✅ | ✅ | ✅ | N/A | ✅ | ✅ | ✅ | Async (poll) | Optional |
| fal.ai | ✅ | ✅ | ✅ | N/A | ✅ | ✅ | ✅ | Async (poll) | Optional |
| HuggingFace | ✅ | ✅ | ✅ | N/A | ❌ | ✅ | Via resize | BROKEN | N/A |

### AI Detection Providers

| Provider | REST | Python SDK | Async | File Upload | URL Input | JPEG | PNG | WebP | Sync/Async |
|----------|------|-----------|-------|-------------|-----------|------|-----|------|------------|
| Sightengine | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | Sync |
| Hive AI | ✅ | ✅ | Partial | ✅ | ✅ | ✅ | ✅ | ✅ | Sync |
| Illuminarty | ✅ | Unknown | Unknown | ✅ | ✅ | ✅ | ✅ | Unknown | Unknown |
| Reality Defender | ✅ | Unknown | Unknown | ✅ | Unknown | ✅ | ✅ | Unknown | Unknown |
| HuggingFace | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | Sync |

---

## 10. Format and Resolution Compatibility

### 10.1 AI Generation — 512×512 Hard Constraint

| Provider | Native 512×512 | Notes |
|----------|----------------|-------|
| Stability AI SD3.5 Flash | ✅ Yes (width=512, height=512 accepted) | No workaround needed |
| Stability AI Stable Image Core | ❌ Min 640×640 | Must resize post-generation via Pillow |
| Replicate FLUX.1-schnell | ✅ (configurable) | |
| fal.ai FLUX | ✅ (image_size param) | |

**Recommended approach**: Use SD3.5 Flash with explicit `width=512, height=512`. Apply Pillow resize as safety fallback. This is architecturally identical to the current HuggingFace provider pattern.

### 10.2 Existing Pipeline Format Flow

```
Generated image (JPEG/PNG/WebP) 
  → PIL Image.open() 
  → img.convert("RGB") 
  → Resize to 512×512 if needed 
  → save(format="PNG") 
  → watermark embed (PNG in, PNG out) 
  → provenance register
```

This format-agnostic pipeline already exists. Any provider returning JPEG, PNG, or WebP is compatible with zero pipeline changes.

### 10.3 AI Detection — Format Support

The existing `image_validation.py` validates JPEG, PNG, WebP, TIFF, BMP. All detection providers accept JPEG and PNG. **No changes to image validation are needed.**

---

## 11. Watermark Robustness Analysis

### 11.1 Our Custom DWT/DCT/QIM Watermark — Expected Behavior

| Required Scenario | Custom WM Result | Notes |
|-------------------|-----------------|-------|
| Original | AUTHENTIC_UNMODIFIED | ✅ |
| JPEG compression (Q=90) | TRACED_BUT_MODIFIED | ✅ UUID survives |
| JPEG compression (Q=75 or lower) | NO_WATERMARK_FOUND | ✅ Watermark lost |
| PNG→JPEG conversion (high quality) | TRACED_BUT_MODIFIED | ✅ |
| JPEG→PNG conversion (lossless) | AUTHENTIC_UNMODIFIED or TRACED_BUT_MODIFIED | Depends on prior JPEG loss |
| Cropping 25% | NO_WATERMARK_FOUND | ✅ Correct |
| Resizing (downscale 256×256) | NO_WATERMARK_FOUND | ✅ Correct |
| Resizing (same 512×512) | AUTHENTIC_UNMODIFIED | ⚠ FALSE CLAIM — known issue |
| Upscaling | Likely NO_WATERMARK_FOUND | Untested |
| Brightness modification | WATERMARK_UNRECOVERABLE | ✅ Correct |
| Contrast modification | WATERMARK_UNRECOVERABLE | ✅ Correct |
| Re-encoding (lossless) | AUTHENTIC_UNMODIFIED | ✅ |
| Re-encoding (lossy) | TRACED_BUT_MODIFIED | ✅ |
| Screenshot / recompression (lossless) | AUTHENTIC_UNMODIFIED | ✅ (known T8 false claim if bitwise identical) |
| Rotation 90°/270° | NO_WATERMARK_FOUND | ✅ |
| Flip | WATERMARK_UNRECOVERABLE | ✅ |
| Gaussian blur | NO_WATERMARK_FOUND | ✅ |

### 11.2 C2PA Metadata Robustness

| Transformation | C2PA Metadata Survives? |
|----------------|------------------------|
| Original (no editing) | ✅ Yes |
| JPEG compression (any quality) | ❌ Often stripped |
| PNG→JPEG conversion | ❌ Metadata lost |
| Crop, Resize | ❌ Stripped by editing tools |
| Social media upload | ❌ Almost always stripped |
| Screenshot | ❌ No |
| Lossless PNG re-save | ✅ Maybe (tool-dependent) |
| Viewing in browser | ✅ |

**Conclusion**: C2PA survives only in pristine, unmodified file lifecycles. It is NOT a robustness solution. It is a generation-time provenance attestation mechanism. Suitable as a secondary trust signal at generation time only.

---

## 12. C2PA / Provenance Support Analysis

### 12.1 Is External C2PA Useful for This Project?

**Assessment: OPTIONALLY USEFUL, BUT NOT ESSENTIAL**

**What C2PA would add:**
- Standards-compliant manifest linking our provenance UUID, prompt, model, and timestamp at generation time
- Interoperability: images can be verified by external tools (Adobe Creative Suite, content credentials browser extension)
- Educational/demo value: demonstrates awareness of industry standards (C2PA is a W3C-tracked standard)

**What C2PA would NOT add:**
- No additional watermark robustness
- No AI detection capability
- No supplementary tracing after compression/cropping/social media

**Implementation option**: Use `c2pa-python` to optionally embed a C2PA manifest during `POST /watermark/embed` as an additive bonus. The manifest cross-references our provenance UUID.

**Risk**: `c2pa-python` requires Rust bindings. May complicate environment setup. Defer to Phase 7.

**Conclusion**: C2PA is **optional** for this project. If implemented, it must be an additive step that does not interfere with any existing code.

### 12.2 No External Invisible Watermark API Available

As of October 2026, there is no publicly available, free API that:
- Embeds invisible steganographic watermarks into arbitrary images
- Reads/verifies them back
- Survives JPEG compression, cropping, and resizing

**Our custom DWT/DCT/QIM watermark is the only viable invisible watermarking solution for this project.** No external provider can replace or supplement it meaningfully.

---

## 13. Detection Quality Considerations

### 13.1 2026 Industry Reality Check

> [!WARNING]
> Independent 2026 benchmarks show that real-world AI detection accuracy against modern
> generators (FLUX, Midjourney v7) drops to **18–33%** in adversarial conditions.
> Detection must be treated as a **probabilistic signal, not proof**.
> This is already correctly stated in our existing system design and API documentation.

### 13.2 Sightengine vs. HuggingFace Community Model

| Criterion | Sightengine | HuggingFace Community |
|-----------|-------------|----------------------|
| Model size | Enterprise, continuously updated | Community-maintained, static |
| 2026 generator coverage | FLUX, DALL-E 3, Midjourney, Ideogram, Firefly, etc. | Limited to training set |
| Pixel-based analysis | ✅ | ✅ |
| Per-generator attribution | ✅ | ❌ |
| Free tier quality | Production-grade | Variable |
| Reliability | High (commercial SLA) | Low (community model) |
| Update cadence | Continuous | Infrequent |
| India access | ✅ Confirmed | ✅ |
| Monthly free operations | 2,000 | ~1–2 images worth ($0.10) |

**Sightengine is dramatically superior** for a demo that needs to demonstrate AI image detection capability.

### 13.3 AI Detection Independence Principle

The existing codebase correctly keeps detection (`POST /detect-ai`) independent from watermark verification (`POST /verify`). This must be maintained. The Sightengine integration must follow the same principle: it analyzes pixel content and returns a probabilistic verdict without ever examining our watermark.

---

## 14. Integration Complexity

### 14.1 Stability AI — Generation Provider

**Complexity: LOW**

Files to create/modify:
1. `backend/app/services/ai_providers/stability_provider.py` (NEW)
   - Implements `BaseAIProvider`
   - Uses `httpx` (already in requirements.txt) for REST calls
   - Requests SD3.5 Flash at width=512, height=512
   - Returns bytes; converts to PNG via Pillow
   - Full error handling: 401, 402 (no credits), 429, 500, timeout
2. `backend/app/services/ai_providers/__init__.py` (MODIFY)
   - Add `elif provider_name == "stability": return StabilityProvider()`
3. `backend/.env.example` (MODIFY)
   - Add commented Stability AI configuration block
4. `backend/tests/test_stability_provider.py` (NEW)
   - Unit tests with mocked HTTP responses

**No changes to**: watermark pipeline, provenance, verification, routes, database schema, frontend.

New env vars needed (reuse existing keys):
- `AI_PROVIDER=stability`
- `AI_API_KEY=<stability_api_key>`
- `AI_MODEL=sd3.5-flash`

### 14.2 Sightengine — Detection Provider

**Complexity: LOW**

Files to create/modify:
1. `backend/app/services/ai_detectors/sightengine_detector.py` (NEW)
   - Implements `BaseAIDetector`
   - Uses `httpx` for REST calls to `https://api.sightengine.com/1.0/check.json`
   - Maps `ai_generated` → `AI_GENERATED`, `human` → `LIKELY_HUMAN`, threshold → `UNCERTAIN`
   - Full error handling: 401, 402, 429, network errors
2. `backend/app/services/ai_detectors/__init__.py` (MODIFY)
   - Add `elif provider_name == "sightengine": return SightengineDetector()`
3. `backend/app/core/config.py` (MODIFY)
   - Add `SIGHTENGINE_API_USER: str | None = None`
   - Add `SIGHTENGINE_API_SECRET: str | None = None`
4. `backend/.env.example` (MODIFY)
   - Add Sightengine configuration block
5. `backend/tests/test_sightengine_detector.py` (NEW)
   - Unit tests with mocked HTTP responses

**Note**: Sightengine uses API User + API Secret (two separate credentials, not a bearer token). Config must be updated with two new optional fields.

New env vars needed:
- `AI_DETECTOR_PROVIDER=sightengine`
- `SIGHTENGINE_API_USER=<user>`
- `SIGHTENGINE_API_SECRET=<secret>`

### 14.3 c2pa-python — Optional C2PA Layer

**Complexity: MEDIUM**
- New dependency: `c2pa-python` (Rust bindings; may require special installation)
- Additive step in watermark service (does not modify frozen code)
- Requires signing certificate for proper C2PA (self-signed acceptable for demo)
- Risk: Rust compilation may fail in some environments
- **Recommendation: Defer to Phase 7 (optional)**

---

## 15. Reliability and Risks

### Risk 1: Stability AI Free Credits Exhausted Quickly
- **Risk Level**: Medium
- **Mitigation**: 25 credits ≈ 10 demo images. Use MockAIProvider during development/testing. Only use live Stability AI for demo sessions. At $0.025/image, $1 more = 40 images.

### Risk 2: Sightengine 500/day Daily Cap
- **Risk Level**: Low
- **Mitigation**: 500 operations/day is more than sufficient for any student demo. The 2,000/month cap = ~66 detections/day average. Starter plan ($29/month) provides 10,000/month if needed.

### Risk 3: API Key Exposure
- **Risk Level**: Medium (inherited, pre-existing)
- **Mitigation**: API keys stored in `.env` file only (already in `.gitignore`). No frontend exposure.

### Risk 4: Stability AI SD3.5 Flash 512×512 Support Change
- **Risk Level**: Low
- **Mitigation**: SD3.5 Flash currently accepts explicit width/height down to 64px. Add Pillow resize fallback in provider code (same pattern as existing HuggingFace provider). If API rejects 512×512, generate at 768×768 and resize.

### Risk 5: Sightengine Detection Accuracy
- **Risk Level**: Low for demo purposes
- **Mitigation**: AI detection is documented as probabilistic in the system. Demo use is educational, not forensic. Sightengine is continuously updated for FLUX/modern generators.

### Risk 6: c2pa-python Rust Dependency
- **Risk Level**: High (for optional C2PA feature)
- **Mitigation**: Mark C2PA as optional. Test c2pa-python install separately before committing. Do not block core functionality on it.

### Risk 7: HuggingFace Detector Model Unavailable
- **Risk Level**: High (current state)
- **Mitigation**: Sightengine migration resolves this. Keep HuggingFace in factory for backward compatibility but it is no longer primary.

### Risk 8: Stability AI Platform Changes
- **Risk Level**: Low
- **Mitigation**: Stability AI is a well-established company. REST API is versioned (v2beta). Changes would require a new API key or URL update at most.

---

## 16. Proposed Validation Test Plan

This describes the end-to-end test that MUST be run AFTER implementing the new providers.

### 16.1 Full E2E Validation Flow

```
[1] Generate Image
    POST /generate
    Provider: Stability AI SD3.5 Flash
    Prompt: "A serene mountain lake at sunset"
    Expected: HTTP 200, image/png response, 512x512 pixels
    Headers: X-AI-Provider=stability, X-AI-Model=sd3.5-flash

[2] Receive and Validate Image
    Assert: bytes > 0, PIL-decodable, size == (512, 512)
    Expected: PASS

[3] Watermark Embed
    POST /watermark/embed
    Input: generated image PNG
    Expected: HTTP 200, watermarked PNG
    Headers: X-Provenance-UUID=<uuid>, X-Asset-SHA256=<hash>

[4] Baseline Verify
    POST /verify
    Input: watermarked PNG
    Expected: verdict=AUTHENTIC_UNMODIFIED, match_found=true

[5] AI Detection -- Baseline
    POST /detect-ai
    Provider: Sightengine
    Input: watermarked PNG
    Expected: label=AI_GENERATED, confidence >= 0.70

[6] Transform Tests (robustness_test.py)
    For each of 20 transforms, POST /verify + POST /detect-ai:

    JPEG Q=90:    verify=TRACED_BUT_MODIFIED,    detect=AI_GENERATED
    JPEG Q=75:    verify=NO_WATERMARK_FOUND,     detect=AI_GENERATED
    JPEG Q=50:    verify=NO_WATERMARK_FOUND,     detect=AI_GENERATED
    JPEG Q=30:    verify=NO_WATERMARK_FOUND,     detect=AI_GENERATED or UNCERTAIN
    Crop 25%:     verify=NO_WATERMARK_FOUND,     detect=AI_GENERATED or UNCERTAIN
    Resize 512x512: verify=AUTHENTIC_UNMODIFIED  (known false claim, pre-existing)
    Resize 256x256: verify=NO_WATERMARK_FOUND,   detect=AI_GENERATED or UNCERTAIN
    Screenshot:   verify=AUTHENTIC_UNMODIFIED    (known false claim, pre-existing)
    Rotate 90:    verify=NO_WATERMARK_FOUND,     detect=AI_GENERATED or UNCERTAIN
    Rotate 180:   verify=WATERMARK_UNRECOVERABLE, detect=AI_GENERATED
    Rotate 270:   verify=NO_WATERMARK_FOUND,     detect=AI_GENERATED or UNCERTAIN
    Flip H:       verify=WATERMARK_UNRECOVERABLE, detect=AI_GENERATED
    Flip V:       verify=WATERMARK_UNRECOVERABLE, detect=AI_GENERATED
    Brightness+:  verify=WATERMARK_UNRECOVERABLE, detect=AI_GENERATED
    Brightness-:  verify=WATERMARK_UNRECOVERABLE, detect=AI_GENERATED
    Contrast+:    verify=WATERMARK_UNRECOVERABLE, detect=AI_GENERATED
    Contrast-:    verify=NO_WATERMARK_FOUND,     detect=AI_GENERATED or UNCERTAIN
    Blur light:   verify=NO_WATERMARK_FOUND,     detect=AI_GENERATED or UNCERTAIN
    Blur moderate: verify=NO_WATERMARK_FOUND,    detect=UNCERTAIN (blur degrades detection)
    Blur heavy:   verify=NO_WATERMARK_FOUND,     detect=UNCERTAIN (heavy blur degrades detection)

[7] Human Photo Test
    POST /detect-ai
    Input: known real photograph (not AI-generated)
    Expected: label=LIKELY_HUMAN, confidence >= 0.70

[8] Unwatermarked AI Image Test
    POST /verify + POST /detect-ai
    Input: external AI-generated image (no our watermark)
    Expected:
      verify: verdict=NO_WATERMARK_FOUND
      detect: label=AI_GENERATED

[9] Independent Signal Verification
    Confirm that detect-ai result did NOT influence verify result
    Confirm that verify result did NOT influence detect-ai result
    Expected: PASS (fully independent)

[10] Summary
    Expected: 0 false authenticity claims (excluding known T2/T8 issues)
    Expected: All 70+ existing unit tests still passing
```

### 16.2 New Provider Unit Tests Required

1. `test_stability_provider.py` — mock HTTP, test 512×512 output, error handling (401, 402, 429, timeout)
2. `test_sightengine_detector.py` — mock HTTP, test label mapping, threshold behavior, two-credential auth
3. All existing 70+ tests must pass (0 regressions)

---

## 17. Recommended Architecture

### 17.1 Full Signal Architecture (Post-Implementation)

```
Image Input (prompt or upload)
     |
     +-- [A] AI GENERATION (if prompt-based)
     |        Stability AI SD3.5 Flash  [NEW PRIMARY]
     |        512x512 JPEG/PNG output
     |        Falls back to: Mock --> Replicate (backup)
     |
     +-- [B] WATERMARK EMBEDDING  [FROZEN - Phase 0]
     |        DWT/DCT/QIM custom watermark
     |        Provenance UUID embedded in PNG
     |
     +-- [C] PROVENANCE REGISTRATION  [FROZEN - Phase 2A]
     |        PostgreSQL: UUID + prompt + model + SHA-256
     |
     +-- [Analysis on POST /verify and POST /detect-ai]
           |
           +-- [D] CUSTOM WATERMARK EXTRACTION  [FROZEN - Phase 0]
           |        Verdict: AUTHENTIC_UNMODIFIED | TRACED_BUT_MODIFIED |
           |                 NO_WATERMARK_FOUND | WATERMARK_UNRECOVERABLE
           |        Signal: cryptographic
           |
           +-- [E] SHA-256 HASH VERIFICATION  [FROZEN - Phase 2B]
           |        Cross-reference with WatermarkedAsset table
           |        Signal: exact file match
           |
           +-- [F] AI DETECTION (independent signal)  [NEW PRIMARY]
           |        Sightengine genai model
           |        Verdict: AI_GENERATED | LIKELY_HUMAN | UNCERTAIN
           |        Signal: probabilistic (pixel-based)
           |        Falls back to: Mock
           |
           +-- [G] C2PA VERIFICATION (optional secondary - Phase 7)
                    c2pa-python (local, open source)
                    Verdict: C2PA_VALID | C2PA_INVALID | C2PA_NOT_PRESENT
                    Signal: metadata/manifest-based

Signals D, E, F, G are INDEPENDENT. Combined in UI. Never merged in logic.
```

### 17.2 Provider Configuration (Post-Implementation)

```ini
# backend/.env

# AI Generation
AI_PROVIDER=stability
AI_API_KEY=<stability_api_key_here>
AI_MODEL=sd3.5-flash

# AI Detection
AI_DETECTOR_PROVIDER=sightengine
SIGHTENGINE_API_USER=<sightengine_user_here>
SIGHTENGINE_API_SECRET=<sightengine_secret_here>
AI_DETECTOR_THRESHOLD=0.70
```

### 17.3 Provider Factory (Post-Implementation)

```python
# ai_providers/__init__.py
def get_ai_provider():
    if provider_name == "mock":        return MockAIProvider()
    if provider_name == "huggingface": return HuggingFaceProvider()   # keep for legacy
    if provider_name == "stability":   return StabilityProvider()     # NEW PRIMARY
    raise ValueError(...)

# ai_detectors/__init__.py
def get_ai_detector():
    if provider_name == "mock":        return MockAIDetector()
    if provider_name == "huggingface": return HuggingFaceDetector()   # keep for legacy
    if provider_name == "sightengine": return SightengineDetector()   # NEW PRIMARY
    raise ValueError(...)
```

---

## 18. Final Recommendations

### 1. PRIMARY AI IMAGE GENERATION PROVIDER: Stability AI (SD3.5 Flash)

**Rationale:**
- 25 free credits on signup, **no credit card required** — verified from official stability.ai
- No recurring billing until credits exhausted — safe for student demo
- Native JPEG output — preferred by the project spec
- **Supports 512×512 directly** via width=512, height=512 params on SD3.5 Flash
- REST API — fits existing httpx-based provider pattern perfectly
- India accessible — confirmed, no restrictions
- SD3.5 Flash at 2.5 credits/image = 10 images free; $0.025/image thereafter
- High-quality modern model (distilled SD3.5, 4-step generation, fast)
- JPEG/PNG/WebP output format selectable via output_format param

### 2. BACKUP AI IMAGE GENERATION PROVIDER: Replicate (FLUX.1-schnell)

**Rationale:**
- Industry-standard FLUX.1-schnell at $0.003/image — extremely cost-effective
- Excellent Python SDK, stable API
- Configurable 512×512 output
- Requires credit card but very low-cost after that
- Well-documented, stable API

### 3. PRIMARY AI DETECTION PROVIDER: Sightengine

**Rationale:**
- **2,000 free operations/month permanently**, no credit card required — best verified free tier
- Per-generator attribution (FLUX, SD, DALL-E 3, Midjourney, etc.) — superior detection signal
- Synchronous REST API — fits detect_image(bytes) interface perfectly
- Pixel-based analysis — does not examine metadata or watermarks (architecturally correct)
- 500/day free limit — sufficient for any demo
- Official Python SDK + REST
- India accessible with no restrictions
- Continuously updated model recognizing FLUX-generated images
- Dramatically superior to current HuggingFace community model approach

### 4. BACKUP AI DETECTION PROVIDER: Hugging Face (model: Nahrawy/AIorNot)

**Rationale:**
- Keep existing HuggingFaceDetector in the factory (do not delete — backward compatibility)
- Update default model from Nahrawy/AI-Vs-Human-Image-Detection to Nahrawy/AIorNot
- $0.10/month free credits — very limited but zero-cost
- Backup only; not suitable as primary due to model reliability and credit limit

### 5. OPTIONAL EXTERNAL PROVENANCE / C2PA: c2pa-python (Open Source)

**Rationale:**
- Free, open source, no API key required
- pip install c2pa-python
- Can embed a C2PA manifest alongside our custom watermark at generation time
- Adds educational/demo value demonstrating awareness of industry standards
- Does NOT replace our custom watermark — purely additive
- C2PA does NOT survive JPEG compression/social media — must be clearly documented
- Implement in a future optional Phase 7
- Risk: Rust dependency may complicate environment; test separately before committing

---

## 19. Next Implementation Phase

> [!IMPORTANT]
> Implementation must only begin after explicit approval of this research document.
> No frozen code must be modified during implementation.

### Phase 6A: Replace Generation Provider (Stability AI)

**Files to create/modify (NO frozen files touched):**

1. CREATE: `backend/app/services/ai_providers/stability_provider.py`
   - Implements BaseAIProvider
   - Uses httpx.AsyncClient to call Stability AI REST v2beta
   - Requests SD3.5 Flash at width=512, height=512, output_format=jpeg
   - Converts JPEG response bytes to PNG via Pillow for watermark pipeline
   - Full error handling: 401, 402 (insufficient credits), 429, 500, timeout

2. MODIFY: `backend/app/services/ai_providers/__init__.py`
   - Add elif provider_name == "stability": return StabilityProvider()
   - Keep HuggingFace entry for backward compatibility

3. MODIFY: `backend/.env.example`
   - Add commented Stability AI configuration block

4. CREATE: `backend/tests/test_stability_provider.py`
   - Unit tests with mocked HTTP responses
   - Test: 512x512 output, provider/model name, error handling

### Phase 6B: Replace Detection Provider (Sightengine)

**Files to create/modify:**

1. CREATE: `backend/app/services/ai_detectors/sightengine_detector.py`
   - Implements BaseAIDetector
   - Uses httpx.AsyncClient for Sightengine REST API
   - Maps ai_generated score to AI_GENERATED; human score to LIKELY_HUMAN; threshold to UNCERTAIN
   - Full error handling: 401, 402, 429, network errors

2. MODIFY: `backend/app/services/ai_detectors/__init__.py`
   - Add elif provider_name == "sightengine": return SightengineDetector()
   - Keep HuggingFace entry for backward compatibility

3. MODIFY: `backend/app/core/config.py`
   - Add SIGHTENGINE_API_USER: str | None = None
   - Add SIGHTENGINE_API_SECRET: str | None = None

4. MODIFY: `backend/.env.example`
   - Add Sightengine configuration block

5. CREATE: `backend/tests/test_sightengine_detector.py`
   - Unit tests with mocked HTTP responses
   - Test: label mapping, threshold behavior, two-credential auth

### Phase 6C: Robustness Re-Test

After Phase 6A + 6B:
1. Run robustness_test.py with Stability AI images + Sightengine detection
2. Update docs/ROBUSTNESS_TEST_REPORT.md with new results
3. Document any behavior differences from FLUX.1-schnell baseline

### Phase 7 (Optional): C2PA Integration

- Install and test c2pa-python separately
- If viable: optionally embed C2PA manifest in watermark route
- Purely additive; does not affect any existing functionality

---

## 20. Appendix: Official Provider URLs

| Provider | Official Pricing URL |
|----------|---------------------|
| Stability AI | https://platform.stability.ai/pricing |
| fal.ai | https://fal.ai/pricing |
| Replicate | https://replicate.com/pricing |
| Together AI | https://api.together.ai/pricing |
| Fireworks AI | https://fireworks.ai/pricing |
| Sightengine | https://sightengine.com/pricing |
| Hive AI | https://thehive.ai/pricing |
| Illuminarty | https://illuminarty.ai/pricing |
| Reality Defender | https://realitydefender.com/pricing |
| Winston AI | https://gowinston.ai/pricing/ |
| C2PA / CAI | https://opensource.contentauthenticity.org |
| c2pa-python | https://github.com/contentauth/c2pa-python |

---

*Research completed: October 2026. All pricing and availability information sourced from official
provider websites and verified web searches conducted October 8, 2026. Pricing is subject to change;
always verify at official pricing pages before implementation.*
