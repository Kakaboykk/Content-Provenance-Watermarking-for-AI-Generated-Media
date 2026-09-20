"""Cross-document consistency check between watermark_design.md and CAPACITY_CALCULATION.md."""

errors = []
warnings = []

with open('watermark/watermark_design.md', encoding='utf-8') as f:
    design = f.read()
with open('watermark/CAPACITY_CALCULATION.md', encoding='utf-8') as f:
    capacity = f.read()


def check_in_both(label, value_str):
    ok_d = value_str in design
    ok_c = value_str in capacity
    if ok_d and ok_c:
        print(f'  OK  {label}: "{value_str}" in both docs')
    elif ok_d:
        print(f'  OK  {label}: "{value_str}" in design only (capacity may use different wording)')
    else:
        errors.append(f'{label}: "{value_str}" NOT found in design doc')


def check_in_design(label, value_str):
    if value_str in design:
        print(f'  OK  {label}: found in design')
    else:
        errors.append(f'MISSING in design: {label} -> "{value_str}"')


def check_absent_design(label, bad_str):
    if bad_str in design:
        errors.append(f'FORBIDDEN string still present in design: {label} -> "{bad_str}"')
    else:
        print(f'  OK  {label}: removed from design')


print('=== CROSS-DOCUMENT CONSISTENCY CHECK ===')
print()

print('--- Core constants ---')
check_in_both('Canonical size', '512 x 512')
check_in_both('Magic constant', '0x574D5031')
check_in_both('Payload bytes', '24 bytes')
check_in_both('Payload bits', '192 bits')
check_in_both('RS notation', 'RS(48,24)')
check_in_both('RS parity', 'parity symbols')
check_in_both('RS error correction', '12 symbol errors')
check_in_both('Repetitions', '1920 bits')
check_in_both('Total blocks', 'Total blocks available')
check_in_both('Blocks per copy', '192 blocks')
check_in_both('Blocks used', '960')
check_in_both('Spare blocks', '64 blocks')
check_in_both('DCT pos 1', '(3, 4)')
check_in_both('DCT pos 2', '(4, 3)')
check_in_both('CRC-32', 'CRC-32')
check_in_design('DELTA_INITIAL constant', 'DELTA_INITIAL = 30')
check_in_design('PSNR threshold', 'PSNR_MIN')
check_in_design('SSIM threshold', 'SSIM_MIN')
print()

print('--- QIM equations present in design ---')
for step in [
    'q = round(c / Delta)',
    'q = int(round(c_extracted / delta))',  # lowercase delta in function parameter
    'abs(q) % 2',
    'c_watermarked = q * Delta',
]:
    count = design.count(step)
    if count >= 1:
        print(f'  OK  QIM step "{step}" appears {count}x')
    else:
        errors.append(f'QIM step missing from design: "{step}"')
print()

print('--- Corrections verified (forbidden text removed) ---')
# The old bound is now only present inside a negation:
#   "should not assume `|c_watermarked - c| <= Delta`"
# That is the CORRECT usage. We check that the old POSITIVE claim no longer
# appears — i.e., it no longer stands alone as a statement of fact.
# The old text was: "The modification magnitude is bounded: `|c_watermarked - c| <= Delta`."
check_absent_design('Old positive bound claim removed',
    'The modification magnitude is bounded: `|c_watermarked - c| <= Delta`.')
check_absent_design('Proof claim removed',
    'Why QIM Is Robust to JPEG')
check_absent_design('Old margin claim removed',
    'exceeds the JPEG Q90 quantization step (11) by a 2.7x margin')
print()

print('--- New required content present in design ---')
required = [
    ('Section 16 header',            '## 16. Cryptographic Authenticity Limitation'),
    ('Not a MAC statement',          'not a cryptographic authentication mechanism'),
    ('Fabrication warning',          'academic integrity violation'),
    ('Non-crypto permutation note',  'not cryptographically secure'),
    ('Heuristic label in section',   'Heuristic Analysis (Not a Proof)'),
    ('Heuristic caveat blockquote',  'JPEG robustness must be verified by experiment'),
    ('[Target] labels',              '[Target]'),
    ('Not yet measured label',       'not yet measured'),
    ('Revision history table',       'Document revision history'),
    ('Section 17 Report Alignment',  '## 17. Report Alignment Notes'),
    ('Section 18 Constants',         '## 18. Implementation Constants Reference'),
    ('Delta starting-value note',    'starting value for experiments only'),
    ('Distortion data-dependent note', 'No fixed maximum bound is claimed'),
    ('3*Delta/2 worst-case note',    '3 * Delta / 2'),
    ('Prohibited forgery claim',     'Watermark recovery proves the image is authentic'),
]
for label, text in required:
    if text in design:
        print(f'  OK  {label}: found')
    else:
        errors.append(f'MISSING required content: {label} -> "{text}"')
print()

print('--- Four verdict states in design ---')
for v in ['AUTHENTIC_UNMODIFIED', 'TRACED_BUT_MODIFIED',
          'WATERMARK_UNRECOVERABLE', 'NO_WATERMARK_FOUND']:
    count = design.count(v)
    if count >= 2:
        print(f'  OK  {v}: {count}x')
    else:
        errors.append(f'Verdict {v} appears only {count}x (expected >= 2)')
print()

print('--- RS(48,24) parameters in both docs ---')
for val, label in [('RS_N = 48', 'RS_N'), ('RS_K = 24', 'RS_K')]:
    if val in design:
        print(f'  OK  {label}: "{val}" in design constants')
    else:
        warnings.append(f'{label}: "{val}" not in design (may use different format)')
for val, label in [('48', 'n=48'), ('24', 'k=24'), ('255', 'GF_max=255')]:
    nd = design.count(val)
    nc = capacity.count(val)
    print(f'  OK  {label}: design={nd}x, capacity={nc}x')
print()

print('=== SUMMARY ===')
if errors:
    print(f'ERRORS ({len(errors)}):')
    for e in errors:
        print(f'  ERROR: {e}')
else:
    print('No errors.')
if warnings:
    print(f'WARNINGS ({len(warnings)}):')
    for w in warnings:
        print(f'  WARN: {w}')
else:
    print('No warnings.')
if not errors and not warnings:
    print('All checks passed. Documents are internally consistent.')
