# PROJECT_REVIEW.md

## Content-Provenance Watermarking for AI-Generated Media

**Reviewed by:** Lead Software Architect  
**Review Date:** September 2026  
**Source Documents:**
- `mutilmedia repo final.pdf` — Original project report (BITE314L, Fall 2026-27)
- `Content_Provenance_Report.docx` — Companion report document
- `Implementation_plan.md.txt` — Finalized implementation plan

---

## 1. Project Understanding

### 1.1 What the Report Proposes

The report (submitted for Multimedia Systems, BITE314L) proposes an end-to-end provenance framework for AI-generated images that:

1. Generates images using Stable Diffusion (and mentions GPT APIs).
2. Embeds an **invisible DWT-DCT watermark** into each generated image.
3. Computes a **SHA-256 hash** of the watermarked image.
4. Stores ownership, hash, and generation metadata in **PostgreSQL**.
5. Allows later verification: extract watermark -> look up provenance -> compare hashes.

The system uses React + Tailwind CSS (frontend), FastAPI + Python (backend), SHA-256 + PostgreSQL (security/DB), and OpenCV + Pillow + DWT-DCT (multimedia processing).

The report also mentions **FFmpeg** and "robust neural watermarking" in its technology table (Section 3.1), which are distinct from classical DWT-DCT watermarking.

Future work listed in the report: video/audio support, C2PA integration, blockchain, browser extensions, mobile apps, cloud-scale verification.

### 1.2 What the Implementation Plan Proposes

The implementation plan translates the report into a concrete engineering roadmap. It:

- Correctly identifies the MVP as **image-only DWT-DCT watermarking** with FastAPI + PostgreSQL + React.
- Correctly defers blockchain, C2PA, video/audio, and mobile apps to "future."
- Adds significant engineering detail: 192-bit payload (32-bit magic + 128-bit UUID + 32-bit CRC), Haar wavelet, HL/LH subband embedding, 8x8 DCT blocks, mid-frequency coefficients, configurable `delta`, repetition error correction, four verification verdict states.
- Correctly prioritizes watermark prototype before building the web application.
- Correctly defines a five-table PostgreSQL schema.

### 1.3 Core Thesis (Preserved Correctly)

> Embed a compact invisible provenance identifier into AI-generated images using DWT-DCT, store full provenance in PostgreSQL, and verify later copies by combining watermark extraction with SHA-256 comparison.

The implementation plan preserves this thesis faithfully. It does **not** add blockchain, C2PA, video, audio, mobile, or neural watermarking to the MVP.

---

## 2. Architecture Review

### 2.1 Alignment with Report

| Report Element | Implementation Plan | Assessment |
|---|---|---|
| React + Tailwind CSS | Present | Aligned |
| FastAPI + Python | Present | Aligned |
| DWT-DCT watermarking | Present, well-detailed | Aligned |
| SHA-256 hashing | Present, dual-hash design | Aligned |
| PostgreSQL provenance | Present, five-table schema | Aligned |
| Stable Diffusion | Recommended as primary API | Aligned |
| GPT APIs | Mentioned in report, plan defers to single API | Minor misalignment -- justified |
| OpenCV + Pillow | Present | Aligned |
| FFmpeg | Not in implementation plan | Intentional omission -- correct for MVP |
| "Neural watermarking" | Not in MVP | Correctly deferred |
| Blind extraction | Present | Aligned |
| PSNR / SSIM | Present | Aligned |

### 2.2 Architecture Soundness

The architecture is sound for an academic MVP:

- **Separation of concerns:** The `watermark/` module is separate from the web application, enabling independent testing. This is an excellent engineering decision.
- **Phase prioritization:** Watermark prototype -> robustness experiments -> web system. This is the correct order for a research-oriented project.
- **Five-table schema:** Logically clean, traceable from `users` -> `generated_media` -> `watermark_records` -> `provenance_records` -> `verification_records`.
- **Four-state verification verdict:** Accurately models real-world outcomes.

---

## 3. Contradictions Between Report and Implementation Plan

### Contradiction 1: FFmpeg

**Report (Section 3.1):** Lists FFmpeg as a multimedia technology.  
**Implementation plan:** Does not mention FFmpeg anywhere.

**Assessment:** This is a **correct omission**. FFmpeg is a video/audio processing tool. Since the MVP is image-only, FFmpeg is not needed. However, the report's technology table does not match the actual MVP stack. The team should be aware of this.

> **Recommended action:** Add a brief note in documentation that FFmpeg is listed in the report for future video support and is not part of the image-only MVP.

---

### Contradiction 2: "Robust Neural Watermarking" in Report

**Report (Section 3.1, Slide 8):** Lists "Robust Neural Watermarking" as a multimedia technology alongside DWT-DCT.  
**Implementation plan:** Uses exclusively classical DWT-DCT watermarking. Neural watermarking is explicitly deferred to "future."

**Assessment:** This is a **significant contradiction** if taken literally. Neural watermarking (e.g., HiDDeN, Stable Signature) requires training deep learning models -- an entirely different engineering effort from implementing DWT-DCT. The report's table appears to list both as implemented technologies, but the main text and methodology sections only describe DWT-DCT.

> **Recommended action:** The implementation plan is correct to use only DWT-DCT for the MVP. The team must clarify in documentation that "neural watermarking" in the report's table refers to future work, not the current implementation. Do NOT attempt to implement neural watermarking in the MVP.

---

### Contradiction 3: "Both Stable Diffusion and GPT APIs"

**Report (Abstract, Section 3.1):** States "Stable Diffusion with GPT APIs" as if both are implemented.  
**Implementation plan:** Recommends choosing ONE image generation provider.

**Assessment:** The implementation plan's advice is **correct**. GPT image generation (DALL-E) and Stable Diffusion are two different provider integrations. Building both providers adds scope without demonstrating a new provenance contribution. Choose one.

> **Recommended action:** Use one provider (Stable Diffusion API or OpenAI DALL-E, not both) for the MVP. Document the choice.

---

### Contradiction 4: "Feature Analysis" Step

**Report (Methodology, Step 2):** "The system analyzes image characteristics and identifies suitable embedding regions that maximize robustness while maintaining visual quality."  
**Implementation plan:** No explicit "feature analysis" step. The plan hardcodes embedding into HL/LH subbands.

**Assessment:** The plan's approach (fixed HL/LH subbands + 8x8 DCT + mid-frequency coefficients) IS a form of feature analysis -- subbands are selected by design based on known signal properties. The report's language implies adaptive per-image region selection, which the plan does not perform.

> **Recommended action:** The plan's fixed-subband approach is academically acceptable and technically correct. Do NOT implement dynamic per-image region selection. Document in the watermark design notes that subbands were selected by signal analysis.

---

### Contradiction 5: "Verification = Mismatch Indicates Tampering"

**Report (Methodology, Step 6):** "Any mismatch indicates possible tampering."  
**Implementation plan:** Four states: AUTHENTIC_UNMODIFIED, TRACED_BUT_MODIFIED, WATERMARK_UNRECOVERABLE, NO_WATERMARK_FOUND.

**Assessment:** The implementation plan is **more accurate** than the report. The report's binary "match/mismatch" framing conflates legitimate compression (not tampering), watermark destruction (inconclusive), and absence of registration.

> **Recommended action:** The implementation plan's four-state model is technically correct and must be kept. The report's simplified framing should not drive engineering decisions.

---

## 4. Missing Technical Requirements

### 4.1 Image Format Handling at Verification

**Missing:** The plan does not specify what happens if the submitted image has EXIF rotation metadata.

**Risk:** EXIF rotation can cause a 90-degree orientation shift before normalization, completely destroying DWT-DCT block grid alignment.

**Recommended action:** At ingestion time for verification:
1. Strip/apply EXIF rotation using `PIL.ImageOps.exif_transpose()` before any processing.
2. Convert to RGB (remove alpha channel).
3. Normalize dimensions.
4. Do NOT perform JPEG compression during the verification pre-processing pipeline.

---

### 4.2 PSNR Target Value Not Specified

Industry standard for imperceptible watermarking: **PSNR >= 35 dB**.  
Typical target for DWT-DCT watermarking: PSNR >= 38-42 dB.

> **Recommended action:** Define MVP acceptance criterion: PSNR >= 35 dB for the watermarked image vs. original.

---

### 4.3 SSIM Target Value Not Specified

SSIM >= 0.95 is a commonly accepted minimum for invisible watermarking.

> **Recommended action:** Add SSIM >= 0.95 as an acceptance criterion.

---

### 4.4 Minimum Extraction Accuracy Threshold Not Defined

> **Recommended action:** The watermark "works" only when extraction accuracy on an uncompressed copy is 100%. For JPEG 90, a minimum of 95% bit accuracy after majority-vote error correction is a reasonable MVP threshold.

---

### 4.5 Subband Capacity Constraint Not Documented

For a 512x512 image: DWT level 1 produces subbands of 256x256. Divided into 8x8 blocks = 1024 blocks. With 192 bits x 5 repetitions = 960 encoded bits. 960 < 1024 -- fits with room to spare.

**Warning:** If 256x256 canonical size is used: 128x128 subband = 256 blocks total. INSUFFICIENT for 192-bit payload with 5x repetition (960 bits needed).

> **Required action:** Document clearly that 512x512 is the minimum canonical resolution for this payload size and repetition factor.

---

### 4.6 Repetition Factor Not Specified

> **Recommended action:** Set N = 5 as the default. This provides majority-vote correction for up to 2-bit errors per payload bit. Document this as a tunable parameter.

---

### 4.7 DCT Coefficient Index Not Specified

The plan says "mid-frequency coefficients" but does not specify which exact position in the 8x8 DCT block.

Standard choice: Zig-zag positions 5-15 (mid-band). Common specific choices: (3,4) or (4,3) in the 8x8 block (0-indexed).

> **Required action (BLOCKING):** Before beginning Phase 1 implementation, select and fix 1-2 specific mid-frequency DCT coefficient positions.

---

### 4.8 CRC Algorithm Not Specified

> **Recommended action:** Use CRC-32 (Python: `binascii.crc32()`). Apply it over the concatenation of the 32-bit magic header + 128-bit UUID.

---

### 4.9 Magic Number Not Defined

> **Recommended action:** Define a fixed 4-byte magic sequence. Example: 0xC0D3PROV. Document this constant in `watermark/config.py`.

---

### 4.10 File Storage Strategy Underspecified

> **Critical requirement:** The canonical watermarked file registered in PostgreSQL must be stored as **lossless PNG**. The `registered_hash_sha256` must be computed from the PNG bytes. If the user downloads a JPEG, that is a "transformed" copy and will produce TRACED_BUT_MODIFIED, not AUTHENTIC_UNMODIFIED.

---

## 5. Technical Risks

### Risk 1: JPEG Compression Destroys DCT Coefficients -- CRITICAL

**Severity:** High | **Likelihood:** High

JPEG re-applies its own DCT quantization, which can destroy embedded data:
- JPEG quality 90: mid-band quantization steps ~4-12. Delta must be >= 10-15 to survive.
- JPEG quality 50: mid-band quantization steps 20-40. With delta = 15, extraction will likely fail.

> **Implication:** The plan's ambition to support JPEG quality 50 as a mandatory MVP test is likely unrealistic with a simple single-delta scheme. Move JPEG quality 50 to "experimental." Keep JPEG 75 and JPEG 90 as mandatory MVP tests.

---

### Risk 2: Resize Normalization -- Moderate

**Severity:** Medium | **Likelihood:** Medium

Resize down to 256x256 then back up to 512x512 introduces significant blurring, altering DCT coefficient values. Majority-vote ECC must be robust enough to handle this. Calibration of delta at N=5 repetition is required before claiming resize robustness.

---

### Risk 3: Blind Extraction Rule Undefined -- HIGH RISK

**Severity:** High | **Likelihood:** High (if not resolved before coding)

The implementation plan describes blind extraction but does not specify the exact extraction rule. This is the most critical missing detail in the watermarking design.

**Required decision (QIM recommended):**

```
Embed bit b into coefficient c:
  q = round(c / delta)
  if b == 1 and q % 2 == 0: q += 1  (make odd)
  if b == 0 and q % 2 == 1: q += 1  (make even)
  c_watermarked = q * delta

Extract bit from c_extracted:
  q = round(c_extracted / delta)
  bit = q % 2
```

QIM (Quantization Index Modulation) is robust because JPEG quantization preserves the parity of modified coefficients.

---

### Risk 4: Image Content Interference -- Low-Moderate

Some images have near-zero values in HL/LH subbands (solid color, smooth gradients), which makes coefficient modification visible and may cause inconsistent extraction.

> **Recommendation:** Test on 5+ diverse images before claiming the system works generally.

---

### Risk 5: AI API Access -- Low-Moderate

The project depends on a third-party AI API. API keys cost money; rate limits may affect demo reliability.

> **Recommendation:** Implement a local fallback allowing users to upload a provided image instead of AI generation.

---

## 6. Watermarking Technical Risks -- Deep Dive

### 6.1 DWT Subband Selection

Plan correctly identifies HL/LH as target subbands:
- LL: too visible, avoid.
- HH: fragile under JPEG, avoid as primary (plan correctly notes this).
- LH/HL: good balance. Use BOTH for redundancy. Ensure code embeds in both.

### 6.2 Payload Design Assessment

192-bit payload (32-bit magic + 128-bit UUID + 32-bit CRC) is well-designed. With 5x repetition (960 total encoded bits) and 1024 available blocks, this is feasible for 512x512 canonical resolution.

**Concern:** With majority voting only, correcting 2 errors per bit (out of 5) may be insufficient at JPEG 75 where bit error rate can be 10-20%.

> **Recommendation:** Implement Reed-Solomon ECC (`reedsolo` Python library) before JPEG robustness tests. This is the most impactful improvement from the current plan.

### 6.3 Cropping Limitation -- Correctly Identified

The plan correctly classifies cropping as "experimental." Cropping shifts the spatial grid; 8x8 block boundaries no longer align with embedded positions. The watermark will be unrecoverable from a significantly cropped image. Do not claim cropping robustness.

### 6.4 PSNR/SSIM Measurement Details

- Compare the original AI-generated image (before watermarking) vs. the watermarked PNG.
- Use `cv2.PSNR()` or compute manually: PSNR = 10 * log10(255^2 / MSE).
- Use `skimage.metrics.structural_similarity()` for SSIM.
- Do NOT compare the watermarked image against a JPEG-compressed version.

---

## 7. Database / API Risks

### 7.1 Dual-Hash Design Is Correct

- `original_hash`: hash of raw AI-generated image (internal auditing).
- `registered_hash`: hash of final watermarked PNG (verification).

Correct. The verification comparison uses `registered_hash` against the hash of the submitted file.

**Important:** SHA-256 is a file-integrity check, not an authorship proof. A JPEG save will produce a different hash than the registered PNG. The UI must display this clearly.

### 7.2 UUID Collision Risk

Not a real risk. UUID4 has ~10^38 possible values.

### 7.3 Path Traversal

- Store only relative paths in PostgreSQL under `storage/`.
- Never concatenate user input into file paths.
- Use UUID-based filenames only.

### 7.4 Rate Limiting Not Defined

> **Recommendation:** Add rate limiting on `/api/verify` using `slowapi`. Limit to ~10 requests per minute per IP.

### 7.5 Duplicate Provenance Records

The schema does not prevent the same `media_id` from being registered multiple times.

> **Recommendation:** Add a database constraint to prevent duplicate provenance registrations for the same `media_id`.

### 7.6 FastAPI Architecture -- Sound

Router structure (`auth.py`, `media.py`, `verify.py`, `provenance.py`) is clean. No concerns.

### 7.7 JWT Expiry Not Specified

> **Recommendation:** Access token: 30 minutes. Refresh token: 7 days (if implemented).

---

## 8. Recommended Corrections

| Priority | Correction |
|---|---|
| CRITICAL | Define the exact blind extraction rule (QIM strongly recommended) before Phase 0 |
| CRITICAL | Choose and fix specific DCT coefficient position(s) before Phase 0 |
| CRITICAL | Define the magic constant value (e.g., 0xC0D3PROV) |
| CRITICAL | Set N=5 and document the capacity math confirming 512x512 is sufficient |
| HIGH | Implement Reed-Solomon ECC (reedsolo library) before JPEG robustness tests |
| HIGH | Add PSNR >= 35 dB and SSIM >= 0.95 as hard acceptance criteria |
| HIGH | Specify that watermarked images must always be stored as lossless PNG |
| MEDIUM | Move JPEG quality 50 from mandatory to experimental |
| MEDIUM | Add EXIF rotation handling at verification ingestion |
| MEDIUM | Document FFmpeg and neural watermarking as future-only |
| LOW | Add rate limiting to /api/verify endpoint |
| LOW | Document single AI provider choice; add fallback upload capability |

---

## 9. Final MVP Definition

### Must Work

| # | Requirement |
|---|---|
| 1 | DWT-DCT watermark embeds a 192-bit payload into a 512x512 PNG image with PSNR >= 35 dB |
| 2 | Blind extraction recovers the correct payload from an uncompressed copy (100% accuracy) |
| 3 | Extraction succeeds at JPEG quality 90 and JPEG quality 75 (>= 95% bit accuracy post-ECC) |
| 4 | Extraction succeeds after 50% and 75% resize with normalization back to 512x512 |
| 5 | Magic header + CRC validation rejects ~99.9% of false positives from random images |
| 6 | SHA-256 dual-hash design correctly identifies unmodified vs. modified copies |
| 7 | Four-state verdict: AUTHENTIC_UNMODIFIED, TRACED_BUT_MODIFIED, WATERMARK_UNRECOVERABLE, NO_WATERMARK_FOUND |
| 8 | PostgreSQL five-table schema: users, generated_media, watermark_records, provenance_records, verification_records |
| 9 | FastAPI endpoints: auth, generate/upload, watermark, register, verify, history |
| 10 | React frontend: login, dashboard, generate, register, verify, results, history |
| 11 | JWT authentication with protected routes |
| 12 | End-to-end demo: generate -> watermark -> register -> download -> verify -> result |

### Must NOT Be Included in MVP

| Feature | Reason |
|---|---|
| Video watermarking | Future work per report |
| Audio watermarking | Future work per report |
| Blockchain integration | Future work per report |
| C2PA standard | Future work per report |
| Neural watermarking | Future work; entirely different engineering effort |
| Browser extension | Future work per report |
| Mobile application | Future work per report |
| FFmpeg | Video tool, not needed for image MVP |
| Multiple AI providers | Not required for provenance demonstration |

---

## 10. Development Order

```
Phase 0: DWT-DCT Prototype (1-bit embed/extract with QIM)
    |
Phase 1: Full Payload Engine (192-bit, QIM, ECC, magic, CRC)
    |
Phase 2: Robustness Experiments (JPEG 90, JPEG 75, Resize 50/75/150, Brightness, Noise)
    |
Phase 2.5: PSNR/SSIM Measurement + delta Tuning
    |
GATE: Watermark works? If NO -> fix before proceeding.
    |
Phase 3: Project Setup (Git, Docker Compose, FastAPI skeleton, React skeleton, PostgreSQL)
    |
Phase 4: Authentication (register, login, JWT)
    |
Phase 5: AI Generation + Image Upload
    |
Phase 6: Provenance Registration (integrate watermark engine into FastAPI)
    |
Phase 7: Verification Engine (integrate blind extraction into FastAPI)
    |
Phase 8: Frontend (connect all pages to APIs)
    |
Phase 9: Complete Testing (unit, integration, security, end-to-end)
    |
Phase 10: Deployment
```

**The single most important rule:**
> Do NOT begin building the web system until the watermark engine passes Phase 2 tests on at least 5 diverse images.

---

## 11. Dependencies Between Phases

```
Phase 0 -> Phase 1       (prototype proves QIM extraction works before full payload)
Phase 1 -> Phase 2       (full payload must be stable before testing robustness)
Phase 2 -> Phase 3       (watermark engine must be proven before web integration)

Phase 3 enables:
    Phase 4              (auth requires DB + FastAPI)
    Phase 5              (AI gen requires FastAPI + storage)

Phase 4 + Phase 5 -> Phase 6    (registration requires auth + media + watermark engine)
Phase 6 -> Phase 7              (verification requires provenance records from registration)
Phase 6 + Phase 7 -> Phase 8    (frontend requires all backend endpoints to exist)
Phase 8 -> Phase 9              (testing requires the complete system)
Phase 9 -> Phase 10             (deployment only after tests pass)
```

### Parallel Work Possible After Phase 2 Gate

| Team Member | Parallel Track |
|---|---|
| Person 1 (Watermarking) | Finalize ECC, write unit tests for embed/extract, produce robustness report |
| Person 2 (Backend) | Phase 3 setup, Phase 4 auth, schema, FastAPI structure |
| Person 3 (Frontend/AI) | Phase 5 AI generation, React scaffolding, component design |

Phases 3, 4, and 5 can proceed in parallel once Phase 2 is complete.

---

## 12. Implementation Readiness Assessment

### Summary Scorecard

| Domain | Status | Notes |
|---|---|---|
| Project objective | PASS | Clearly defined, faithful to report |
| Architecture design | PASS | Sound and appropriate for MVP |
| Database schema | PASS | Well-designed, logically complete |
| API design | PASS | RESTful, adequate endpoints defined |
| Frontend plan | PASS | Pages and flows defined |
| Development order | PASS | Watermark-first approach is correct |
| DWT subband selection | PASS | HL/LH correctly chosen |
| Scope control | PASS | No blockchain, C2PA, video, mobile in MVP |
| DCT coefficient selection | FAIL | Not specified -- blocking, must be decided first |
| Blind extraction rule | FAIL | Not specified -- QIM must be chosen and documented |
| EXIF rotation handling | FAIL | Not mentioned -- must add |
| Error correction | WARN | Repetition only may be insufficient; RS recommended |
| PSNR/SSIM targets | WARN | Not specified -- must add explicit thresholds |
| Lossless PNG storage | WARN | Implied but not explicitly required |
| JPEG 50 robustness | WARN | Likely unrealistic with simple ECC |
| FFmpeg/neural contradictions | WARN | Must be documented as future-only |

---

## Final Statement

> **The project is NOT yet ready to begin full implementation.**

However, it is very close. The architectural foundation, development philosophy, and scope boundaries are excellent. The plan correctly identifies the highest-risk component (DWT-DCT watermarking) and correctly places it first.

**Blocking issues that must be resolved before writing any watermarking code:**

1. **[BLOCKING]** Choose and document the exact blind extraction rule. Recommended: QIM (Quantization Index Modulation).
2. **[BLOCKING]** Choose and fix the specific DCT coefficient position(s). Recommended: zig-zag indices 5-6 (block positions (1,3) and (2,2) in 0-indexed 8x8 block).
3. **[BLOCKING]** Define the magic constant value. Example: 0xC0D3PROV.
4. **[BLOCKING]** Set repetition factor N=5 and document the capacity calculation confirming 512x512 is sufficient.
5. **[HIGH]** Decide to implement Reed-Solomon ECC alongside repetition before JPEG robustness tests.
6. **[HIGH]** Add PSNR >= 35 dB and SSIM >= 0.95 as explicit, measurable acceptance criteria.
7. **[HIGH]** Explicitly specify that watermarked images are stored as lossless PNG and that the registered hash is computed from PNG bytes.

Once these blocking decisions are documented in `watermark/watermark_design.md`, **Phase 0 can begin immediately.**

The backend and frontend engineers can begin Phase 3 project setup (Git, Docker Compose, FastAPI skeleton, React scaffolding) in parallel -- they do not need the watermark engine to be complete to set up infrastructure.

---

*End of PROJECT_REVIEW.md*
