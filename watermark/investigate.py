with open('watermark/watermark_design.md', encoding='utf-8') as f:
    design = f.read()

# 1. Check for the old bound
print('=== 1. Search for c_watermarked - c ===')
idx = design.find('c_watermarked - c')
if idx >= 0:
    snippet = design[max(0, idx-60):idx+120]
    print(repr(snippet))
else:
    print('Not found')
print()

# 2. Check RS_2T / parity line
print('=== 2. RS parity lines ===')
for term in ['RS_2T', '24 parity', 'parity symbols']:
    idx2 = design.find(term)
    if idx2 >= 0:
        print(f'  Found "{term}" at {idx2}: {repr(design[idx2:idx2+80])}')
    else:
        print(f'  NOT FOUND: "{term}"')
print()

# 3. Check 1024 blocks wording
print('=== 3. 1024 + blocks wording ===')
idx3 = design.find('Total blocks available')
if idx3 >= 0:
    print(repr(design[idx3:idx3+60]))
else:
    print('Total blocks available: NOT FOUND')
idx4 = design.find('Total blocks        = 1024')
if idx4 >= 0:
    print(repr(design[idx4:idx4+40]))
else:
    print('Total blocks = 1024: NOT FOUND')
print()

# 4. Check qim_extract function
print('=== 4. qim_extract function ===')
idx5 = design.find('def qim_extract')
if idx5 >= 0:
    print(repr(design[idx5:idx5+200]))
else:
    print('def qim_extract: NOT FOUND')
