"""
robustness_test.py
==================
Phase 5B Manual Robustness Testing Script.

Performs 21 automated end-to-end verification tests (T0–T20) against the
live backend at http://localhost:8000.

HOW IT WORKS
------------
1. Generates a fresh AI image via POST /generate.
2. Embeds a watermark via POST /watermark/embed.
3. Verifies the baseline (T0) — must be AUTHENTIC_UNMODIFIED.
4. Creates 20 transformed copies of the baseline image in-memory.
5. Submits each copy to POST /verify and POST /detect-ai independently.
6. Records and prints a full results table.
7. Writes a Markdown report to robustness_test_report.md.

USAGE
-----
Activate the .venv first, then run from the backend/ directory:

    .venv/Scripts/python robustness_test.py

The backend server must be running at http://localhost:8000.
"""

import io
import json
import sys
import datetime
import traceback
from pathlib import Path

import httpx
from PIL import Image, ImageEnhance, ImageFilter

# Force UTF-8 stdout on Windows to avoid cp1252 encoding errors
if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = _io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_URL = "http://localhost:8000"
REPORT_PATH = Path(__file__).parent.parent / "docs" / "ROBUSTNESS_TEST_REPORT.md"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _post_multipart(client: httpx.Client, url: str, filename: str, data: bytes, content_type: str = "image/png"):
    return client.post(
        url,
        files={"file": (filename, data, content_type)},
        timeout=90,
    )


def _img_to_bytes(img: Image.Image, fmt: str = "PNG", **kwargs) -> bytes:
    buf = io.BytesIO()
    if fmt.upper() == "PNG":
        img.save(buf, format="PNG")
    else:
        rgb = img.convert("RGB")
        rgb.save(buf, format=fmt.upper(), **kwargs)
    return buf.getvalue()


def _verify(client: httpx.Client, data: bytes, label: str):
    r = _post_multipart(client, f"{BASE_URL}/verify", "test.png", data)
    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
    return r.json()


def _detect(client: httpx.Client, data: bytes):
    try:
        r = _post_multipart(client, f"{BASE_URL}/detect-ai", "test.png", data)
        if r.status_code == 200:
            return r.json()
        return {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Transform functions  (never mutates baseline)
# ---------------------------------------------------------------------------

def t1_crop(img: Image.Image) -> bytes:
    w, h = img.size
    # Remove 25% from right and bottom
    return _img_to_bytes(img.crop((0, 0, int(w * 0.75), int(h * 0.75))))


def t2_resize_512(img: Image.Image) -> bytes:
    return _img_to_bytes(img.resize((512, 512), Image.LANCZOS))


def t3_resize_256(img: Image.Image) -> bytes:
    return _img_to_bytes(img.resize((256, 256), Image.LANCZOS))


def t4_jpeg_q90(img: Image.Image) -> bytes:
    return _img_to_bytes(img, fmt="JPEG", quality=90)


def t5_jpeg_q75(img: Image.Image) -> bytes:
    return _img_to_bytes(img, fmt="JPEG", quality=75)


def t6_jpeg_q50(img: Image.Image) -> bytes:
    return _img_to_bytes(img, fmt="JPEG", quality=50)


def t7_jpeg_q30(img: Image.Image) -> bytes:
    return _img_to_bytes(img, fmt="JPEG", quality=30)


def t8_screenshot(img: Image.Image) -> bytes:
    # Simulate screenshot by re-saving via a copy buffer
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    screenshot = Image.open(buf).copy()
    return _img_to_bytes(screenshot)


def t9_rotate_90(img: Image.Image) -> bytes:
    return _img_to_bytes(img.rotate(90, expand=True))


def t10_rotate_180(img: Image.Image) -> bytes:
    return _img_to_bytes(img.rotate(180))


def t11_rotate_270(img: Image.Image) -> bytes:
    return _img_to_bytes(img.rotate(270, expand=True))


def t12_flip_h(img: Image.Image) -> bytes:
    return _img_to_bytes(img.transpose(Image.FLIP_LEFT_RIGHT))


def t13_flip_v(img: Image.Image) -> bytes:
    return _img_to_bytes(img.transpose(Image.FLIP_TOP_BOTTOM))


def t14_brightness_up(img: Image.Image) -> bytes:
    return _img_to_bytes(ImageEnhance.Brightness(img).enhance(1.5))


def t15_brightness_down(img: Image.Image) -> bytes:
    return _img_to_bytes(ImageEnhance.Brightness(img).enhance(0.5))


def t16_contrast_up(img: Image.Image) -> bytes:
    return _img_to_bytes(ImageEnhance.Contrast(img).enhance(2.0))


def t17_contrast_down(img: Image.Image) -> bytes:
    return _img_to_bytes(ImageEnhance.Contrast(img).enhance(0.4))


def t18_blur_light(img: Image.Image) -> bytes:
    return _img_to_bytes(img.filter(ImageFilter.GaussianBlur(radius=1)))


def t19_blur_moderate(img: Image.Image) -> bytes:
    return _img_to_bytes(img.filter(ImageFilter.GaussianBlur(radius=3)))


def t20_blur_heavy(img: Image.Image) -> bytes:
    return _img_to_bytes(img.filter(ImageFilter.GaussianBlur(radius=7)))


# ---------------------------------------------------------------------------
# Test definitions
# ---------------------------------------------------------------------------

TRANSFORMS = [
    ("T1",  "Crop",       "25% crop (right+bottom removed)",  t1_crop),
    ("T2",  "Resize",     "512×512 (LANCZOS)",                t2_resize_512),
    ("T3",  "Resize",     "256×256 (LANCZOS)",                t3_resize_256),
    ("T4",  "JPEG",       "Quality = 90",                     t4_jpeg_q90),
    ("T5",  "JPEG",       "Quality = 75",                     t5_jpeg_q75),
    ("T6",  "JPEG",       "Quality = 50",                     t6_jpeg_q50),
    ("T7",  "JPEG",       "Quality = 30",                     t7_jpeg_q30),
    ("T8",  "Screenshot", "Re-save via buffer (PNG copy)",    t8_screenshot),
    ("T9",  "Rotate",     "90° CW",                           t9_rotate_90),
    ("T10", "Rotate",     "180°",                             t10_rotate_180),
    ("T11", "Rotate",     "270° CW",                          t11_rotate_270),
    ("T12", "Flip",       "Horizontal",                       t12_flip_h),
    ("T13", "Flip",       "Vertical",                         t13_flip_v),
    ("T14", "Brightness", "Increased ×1.5",                   t14_brightness_up),
    ("T15", "Brightness", "Decreased ×0.5",                   t15_brightness_down),
    ("T16", "Contrast",   "Increased ×2.0",                   t16_contrast_up),
    ("T17", "Contrast",   "Decreased ×0.4",                   t17_contrast_down),
    ("T18", "Blur",       "Light (Gaussian r=1)",             t18_blur_light),
    ("T19", "Blur",       "Moderate (Gaussian r=3)",          t19_blur_moderate),
    ("T20", "Blur",       "Heavy (Gaussian r=7)",             t20_blur_heavy),
]


def _parse_result(test_id, params, verify_resp, detect_resp):
    """Parse API responses into a flat result dict."""
    r = {
        "id": test_id,
        "params": params,
        "error": None,
        "verdict": None,
        "watermark_detected": "No",
        "uuid_recovered": "No",
        "hash_match": "No",
        "false_authentic": "No",
        "ai_label": "N/A",
        "ai_confidence": "N/A",
        "pass_fail": "FAIL",
        "notes": "",
    }

    if "error" in verify_resp:
        r["error"] = verify_resp["error"]
        r["verdict"] = "ERROR"
        r["notes"] = verify_resp["error"]
        return r

    verdict = verify_resp.get("verdict", "UNKNOWN")
    r["verdict"] = verdict
    rec = verify_resp.get("verification_record", {})
    extracted_uuid = rec.get("extracted_provenance_uuid") if rec else verify_resp.get("extracted_provenance_uuid")

    if verdict == "AUTHENTIC_UNMODIFIED":
        r["watermark_detected"] = "Yes"
        r["uuid_recovered"] = "Yes"
        r["hash_match"] = "Yes"
        r["false_authentic"] = "*** CHECK ***"  # flag for baseline only when expected
    elif verdict == "TRACED_BUT_MODIFIED":
        r["watermark_detected"] = "Yes"
        r["uuid_recovered"] = "Yes" if extracted_uuid else "No"
        r["hash_match"] = "No"
    elif verdict == "WATERMARK_UNRECOVERABLE":
        r["watermark_detected"] = "Yes (corrupted)"
        r["uuid_recovered"] = "No"
        r["hash_match"] = "No"
    elif verdict == "NO_WATERMARK_FOUND":
        r["watermark_detected"] = "No"
        r["uuid_recovered"] = "No"
        r["hash_match"] = "No"

    # AI detection
    if "error" in detect_resp:
        r["ai_label"] = "Unavailable"
        r["ai_confidence"] = "N/A"
    else:
        r["ai_label"] = detect_resp.get("label", "N/A")
        conf = detect_resp.get("confidence", None)
        r["ai_confidence"] = f"{round(conf * 100)}%" if conf is not None else "N/A"

    # Pass/Fail for transformations (T1-T20):
    # PASS = system did NOT falsely claim AUTHENTIC_UNMODIFIED
    # (TRACED_BUT_MODIFIED, WATERMARK_UNRECOVERABLE, NO_WATERMARK_FOUND are all acceptable)
    r["false_authentic"] = "YES ⚠" if verdict == "AUTHENTIC_UNMODIFIED" else "No"
    r["pass_fail"] = "FAIL ⚠" if verdict == "AUTHENTIC_UNMODIFIED" else "PASS"

    return r


def _print_row(r):
    fa = r.get("false_authentic", "")
    print(
        f"  {r['id']:<5} | {r['verdict']:<25} | WM={r['watermark_detected']:<20} "
        f"| UUID={r['uuid_recovered']:<4} | Hash={r['hash_match']:<4} "
        f"| AI={r['ai_label']:<15} ({r['ai_confidence']}) | {r['pass_fail']}"
        + ("  ** FALSE AUTHENTIC! **" if str(fa).startswith("YES") else "")
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 78)
    print("  WATERMARK ROBUSTNESS TEST SUITE  —  Phase 5B Manual Testing")
    print(f"  Timestamp: {datetime.datetime.now().isoformat()}")
    print("=" * 78)

    results = []

    with httpx.Client(timeout=120) as client:
        # ------------------------------------------------------------------
        # STEP 1: Health check
        # ------------------------------------------------------------------
        print("\n[SETUP] Checking backend connectivity...")
        try:
            r = client.get(f"{BASE_URL}/health")
            if r.status_code != 200:
                print(f"  ERROR: Backend health check failed: {r.status_code}")
                sys.exit(1)
            print(f"  OK: Backend is running.")
        except Exception as e:
            print(f"  ERROR: Cannot connect to backend at {BASE_URL}: {e}")
            sys.exit(1)

        # ------------------------------------------------------------------
        # STEP 2: Generate AI image -> Changed to load local image
        # ------------------------------------------------------------------
        print("\n[SETUP] Loading baseline AI image ...")
        try:
            image_path = "C:\\Users\\priti\\.gemini\\antigravity-ide\\brain\\184bccdd-b78f-4283-aaaa-9aed5aaade9a\\.user_uploaded\\media_1791481304385.png"
            with open(image_path, "rb") as f:
                raw_generated = f.read()
            ai_provider = "stability"
            ai_model = "sd3.5-flash"
            print(f"  OK: Image loaded ({len(raw_generated):,} bytes) from {image_path}")
        except Exception as e:
            print(f"  ERROR: Loading image failed: {e}")
            sys.exit(1)

        # ------------------------------------------------------------------
        # STEP 3: Watermark embed
        # ------------------------------------------------------------------
        print("\n[SETUP] Embedding watermark via POST /watermark/embed ...")
        try:
            r = client.post(
                f"{BASE_URL}/watermark/embed",
                files={"file": ("generated.png", raw_generated, "image/png")},
                data={
                    "source_type": "ai_generated",
                    "generation_provider": ai_provider,
                    "model_name": ai_model,
                    "prompt": "A serene mountain lake at sunset",
                },
                timeout=120,
            )
            if r.status_code != 200:
                print(f"  ERROR: /watermark/embed returned {r.status_code}: {r.text[:300]}")
                sys.exit(1)
            baseline_bytes = r.content
            baseline_uuid = r.headers.get("x-provenance-uuid", "unknown")
            baseline_sha = r.headers.get("x-asset-sha256", "unknown")
            print(f"  OK: Watermarked image ({len(baseline_bytes):,} bytes)")
            print(f"  UUID: {baseline_uuid}")
            print(f"  SHA-256: {baseline_sha[:32]}...")
        except Exception as e:
            print(f"  ERROR: /watermark/embed failed: {e}")
            sys.exit(1)

        # Load baseline as PIL image (never modified)
        baseline_img = Image.open(io.BytesIO(baseline_bytes)).copy()

        # ------------------------------------------------------------------
        # T0 — BASELINE
        # ------------------------------------------------------------------
        print("\n[T0] Baseline verification ...")
        vr0 = _verify(client, baseline_bytes, "baseline")
        dr0 = _detect(client, baseline_bytes)
        verdict0 = vr0.get("verdict", "ERROR")
        if verdict0 != "AUTHENTIC_UNMODIFIED":
            print(f"  FATAL: Baseline did not verify as AUTHENTIC_UNMODIFIED (got: {verdict0})")
            print(f"  Raw verify response: {json.dumps(vr0, indent=2)}")
            sys.exit(1)
        ai_label0 = dr0.get("label", "N/A")
        ai_conf0 = f"{round(dr0.get('confidence', 0) * 100)}%" if "confidence" in dr0 else "N/A"
        t0 = {
            "id": "T0",
            "params": "Original baseline",
            "error": None,
            "verdict": verdict0,
            "watermark_detected": "Yes",
            "uuid_recovered": "Yes",
            "hash_match": "Yes",
            "false_authentic": "N/A (expected)",
            "ai_label": ai_label0,
            "ai_confidence": ai_conf0,
            "pass_fail": "PASS",
            "notes": f"UUID={baseline_uuid[:16]}...",
        }
        results.append(t0)
        print(f"  PASS: Baseline verified as AUTHENTIC_UNMODIFIED. AI: {ai_label0} ({ai_conf0})")

        # ------------------------------------------------------------------
        # T1–T20
        # ------------------------------------------------------------------
        print(f"\n[TESTS] Running {len(TRANSFORMS)} transformation tests...\n")

        for test_id, category, params, transform_fn in TRANSFORMS:
            print(f"  [{test_id}] {category}: {params}")
            try:
                transformed_bytes = transform_fn(baseline_img)
            except Exception as e:
                results.append({
                    "id": test_id, "params": params, "error": f"Transform failed: {e}",
                    "verdict": "ERROR", "watermark_detected": "N/A", "uuid_recovered": "N/A",
                    "hash_match": "N/A", "false_authentic": "N/A", "ai_label": "N/A",
                    "ai_confidence": "N/A", "pass_fail": "ERROR", "notes": traceback.format_exc()[:200],
                })
                print(f"      ERROR: transform failed: {e}")
                continue

            vr = _verify(client, transformed_bytes, f"{test_id}.png")
            dr = _detect(client, transformed_bytes)

            res = _parse_result(test_id, params, vr, dr)
            results.append(res)
            _print_row(res)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("  SUMMARY")
    print("=" * 78)

    total = len(results)
    authentic = sum(1 for r in results if r["verdict"] == "AUTHENTIC_UNMODIFIED")
    traced    = sum(1 for r in results if r["verdict"] == "TRACED_BUT_MODIFIED")
    corrupt   = sum(1 for r in results if r["verdict"] == "WATERMARK_UNRECOVERABLE")
    no_wm     = sum(1 for r in results if r["verdict"] == "NO_WATERMARK_FOUND")
    errors    = sum(1 for r in results if r["verdict"] == "ERROR")
    # T0 is the only one that SHOULD be AUTHENTIC_UNMODIFIED
    false_authentic = sum(
        1 for r in results
        if r["id"] != "T0" and r["verdict"] == "AUTHENTIC_UNMODIFIED"
    )

    print(f"  Total tests:               {total}")
    print(f"  Baseline:                  T0=AUTHENTIC_UNMODIFIED (expected)")
    print(f"  AUTHENTIC_UNMODIFIED:      {authentic}  (expected: 1 — baseline only)")
    print(f"  TRACED_BUT_MODIFIED:       {traced}")
    print(f"  WATERMARK_UNRECOVERABLE:   {corrupt}")
    print(f"  NO_WATERMARK_FOUND:        {no_wm}")
    print(f"  ERROR:                     {errors}")
    print(f"  False authenticity claims: {false_authentic}  ({'NONE — GOOD' if false_authentic == 0 else 'WARNING: BUGS FOUND'})")

    # ------------------------------------------------------------------
    # Write Markdown report
    # ------------------------------------------------------------------
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _write_markdown_report(results, baseline_uuid, baseline_sha, ai_provider, ai_model,
                           authentic, traced, corrupt, no_wm, errors, false_authentic)
    print(f"\n  Report written to: {REPORT_PATH}")
    print("=" * 78)


def _write_markdown_report(results, baseline_uuid, baseline_sha, ai_provider, ai_model,
                            authentic, traced, corrupt, no_wm, errors, false_authentic):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append(f"# Watermark Robustness Test Report")
    lines.append(f"\n**Generated:** {now}  ")
    lines.append(f"**Baseline UUID:** `{baseline_uuid}`  ")
    lines.append(f"**Baseline SHA-256:** `{baseline_sha}`  ")
    lines.append(f"**AI Generation Provider:** {ai_provider} / {ai_model}  ")
    lines.append(f"\n> [!NOTE]")
    lines.append(f"> This report documents the **current implementation's behavior** without any modifications.")
    lines.append(f"> A PASS means the system correctly identified the image as NOT authentic-unmodified.")
    lines.append(f"> A FAIL means the system issued a false AUTHENTIC_UNMODIFIED claim for a transformed image.")
    lines.append(f"\n## Results Table\n")
    lines.append("| ID | Transformation | Parameters | Watermark Detected | UUID Recovered | Hash Match | Verdict | AI Label | AI Conf | False Authentic | Pass/Fail |")
    lines.append("|----|----------------|------------|-------------------|----------------|------------|---------|----------|---------|-----------------|-----------|")

    for r in results:
        fa = r.get("false_authentic", "")
        lines.append(
            f"| {r['id']} | "
            f"{'Baseline' if r['id'] == 'T0' else r['id'].replace('T', '')+'. Transform'} | "
            f"{r['params']} | "
            f"{r['watermark_detected']} | "
            f"{r['uuid_recovered']} | "
            f"{r['hash_match']} | "
            f"**{r['verdict']}** | "
            f"{r['ai_label']} | "
            f"{r['ai_confidence']} | "
            f"{'⚠ YES' if fa.startswith('YES') else 'No'} | "
            f"{'✅ PASS' if r['pass_fail'] == 'PASS' else '❌ FAIL'} |"
        )

    lines.append(f"\n## Summary Statistics\n")
    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total tests | {len(results)} |")
    lines.append(f"| AUTHENTIC_UNMODIFIED | {authentic} (expected: 1) |")
    lines.append(f"| TRACED_BUT_MODIFIED | {traced} |")
    lines.append(f"| WATERMARK_UNRECOVERABLE | {corrupt} |")
    lines.append(f"| NO_WATERMARK_FOUND | {no_wm} |")
    lines.append(f"| ERROR | {errors} |")
    lines.append(f"| **False Authenticity Claims** | **{false_authentic}** |")

    lines.append(f"\n## Observations\n")
    lines.append(f"### False Authenticity Risk")
    if false_authentic == 0:
        lines.append(f"✅ No false AUTHENTIC_UNMODIFIED claims were observed across any transformation.")
    else:
        lines.append(f"⚠ **{false_authentic} false AUTHENTIC_UNMODIFIED claim(s) detected.** See flagged rows above.")

    lines.append(f"\n### Verdict Distribution")
    lines.append(f"- **TRACED_BUT_MODIFIED**: {traced} — Watermark payload survived, UUID recovered, hash differed.")
    lines.append(f"- **WATERMARK_UNRECOVERABLE**: {corrupt} — Watermark signal present but undecodable.")
    lines.append(f"- **NO_WATERMARK_FOUND**: {no_wm} — No recognizable watermark payload detected.")

    lines.append(f"\n## Integrity Statement")
    lines.append(f"No implementation changes were made during this test. The watermark algorithm, verification logic, and")
    lines.append(f"provenance database remain in their original state. Results reflect actual system behavior.")

    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
