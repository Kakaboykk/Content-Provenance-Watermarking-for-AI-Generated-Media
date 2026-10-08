# Watermark Robustness Test Report

**Generated:** 2026-10-08 23:38:30  
**Baseline UUID:** `35760ebb-04fa-46b0-81cc-2fbb2c9945bd`  
**Baseline SHA-256:** `19a0b40c18e20f6861511e660173b65923ca392603af6c5f0cbee3ee52987655`  
**AI Generation Provider:** stability / sd3.5-flash  

> [!NOTE]
> This report documents the **current implementation's behavior** without any modifications.
> A PASS means the system correctly identified the image as NOT authentic-unmodified.
> A FAIL means the system issued a false AUTHENTIC_UNMODIFIED claim for a transformed image.

## Results Table

| ID | Transformation | Parameters | Watermark Detected | UUID Recovered | Hash Match | Verdict | AI Label | AI Conf | False Authentic | Pass/Fail |
|----|----------------|------------|-------------------|----------------|------------|---------|----------|---------|-----------------|-----------|
| T0 | Baseline | Original baseline | Yes | Yes | Yes | **AUTHENTIC_UNMODIFIED** | UNCERTAIN | 62% | No | ✅ PASS |
| T1 | 1. Transform | 25% crop (right+bottom removed) | No | No | No | **NO_WATERMARK_FOUND** | AI_GENERATED | 98% | No | ✅ PASS |
| T2 | 2. Transform | 512×512 (LANCZOS) | Yes | Yes | Yes | **AUTHENTIC_UNMODIFIED** | UNCERTAIN | 62% | ⚠ YES | ❌ FAIL |
| T3 | 3. Transform | 256×256 (LANCZOS) | No | No | No | **NO_WATERMARK_FOUND** | LIKELY_HUMAN | 96% | No | ✅ PASS |
| T4 | 4. Transform | Quality = 90 | Yes | Yes | No | **TRACED_BUT_MODIFIED** | AI_GENERATED | 78% | No | ✅ PASS |
| T5 | 5. Transform | Quality = 75 | No | No | No | **NO_WATERMARK_FOUND** | UNCERTAIN | 66% | No | ✅ PASS |
| T6 | 6. Transform | Quality = 50 | No | No | No | **NO_WATERMARK_FOUND** | UNCERTAIN | 69% | No | ✅ PASS |
| T7 | 7. Transform | Quality = 30 | No | No | No | **NO_WATERMARK_FOUND** | LIKELY_HUMAN | 95% | No | ✅ PASS |
| T8 | 8. Transform | Re-save via buffer (PNG copy) | Yes | Yes | Yes | **AUTHENTIC_UNMODIFIED** | UNCERTAIN | 62% | ⚠ YES | ❌ FAIL |
| T9 | 9. Transform | 90° CW | No | No | No | **NO_WATERMARK_FOUND** | LIKELY_HUMAN | 99% | No | ✅ PASS |
| T10 | 10. Transform | 180° | Yes (corrupted) | No | No | **WATERMARK_UNRECOVERABLE** | LIKELY_HUMAN | 100% | No | ✅ PASS |
| T11 | 11. Transform | 270° CW | No | No | No | **NO_WATERMARK_FOUND** | LIKELY_HUMAN | 81% | No | ✅ PASS |
| T12 | 12. Transform | Horizontal | Yes (corrupted) | No | No | **WATERMARK_UNRECOVERABLE** | LIKELY_HUMAN | 83% | No | ✅ PASS |
| T13 | 13. Transform | Vertical | Yes (corrupted) | No | No | **WATERMARK_UNRECOVERABLE** | LIKELY_HUMAN | 100% | No | ✅ PASS |
| T14 | 14. Transform | Increased ×1.5 | Yes (corrupted) | No | No | **WATERMARK_UNRECOVERABLE** | LIKELY_HUMAN | 71% | No | ✅ PASS |
| T15 | 15. Transform | Decreased ×0.5 | Yes (corrupted) | No | No | **WATERMARK_UNRECOVERABLE** | UNCERTAIN | 57% | No | ✅ PASS |
| T16 | 16. Transform | Increased ×2.0 | Yes (corrupted) | No | No | **WATERMARK_UNRECOVERABLE** | UNCERTAIN | 56% | No | ✅ PASS |
| T17 | 17. Transform | Decreased ×0.4 | No | No | No | **NO_WATERMARK_FOUND** | AI_GENERATED | 71% | No | ✅ PASS |
| T18 | 18. Transform | Light (Gaussian r=1) | No | No | No | **NO_WATERMARK_FOUND** | AI_GENERATED | 99% | No | ✅ PASS |
| T19 | 19. Transform | Moderate (Gaussian r=3) | No | No | No | **NO_WATERMARK_FOUND** | UNCERTAIN | 68% | No | ✅ PASS |
| T20 | 20. Transform | Heavy (Gaussian r=7) | No | No | No | **NO_WATERMARK_FOUND** | UNCERTAIN | 50% | No | ✅ PASS |

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total tests | 21 |
| AUTHENTIC_UNMODIFIED | 3 (expected: 1) |
| TRACED_BUT_MODIFIED | 1 |
| WATERMARK_UNRECOVERABLE | 6 |
| NO_WATERMARK_FOUND | 11 |
| ERROR | 0 |
| **False Authenticity Claims** | **2** |

## Observations

### False Authenticity Risk
⚠ **2 false AUTHENTIC_UNMODIFIED claim(s) detected.** See flagged rows above.

### Verdict Distribution
- **TRACED_BUT_MODIFIED**: 1 — Watermark payload survived, UUID recovered, hash differed.
- **WATERMARK_UNRECOVERABLE**: 6 — Watermark signal present but undecodable.
- **NO_WATERMARK_FOUND**: 11 — No recognizable watermark payload detected.

## Integrity Statement
No implementation changes were made during this test. The watermark algorithm, verification logic, and
provenance database remain in their original state. Results reflect actual system behavior.