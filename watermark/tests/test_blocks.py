import pytest
from watermark.blocks import get_block_permutation, get_copy_blocks

def test_block_permutation():
    perm = get_block_permutation()
    assert len(perm) == 1024
    assert len(set(perm)) == 1024 # unique
    
def test_copy_blocks():
    all_used_blocks = []
    for i in range(5):
        blocks = get_copy_blocks(i)
        assert len(blocks) == 192
        all_used_blocks.extend(blocks)
        
    assert len(all_used_blocks) == 960
    assert len(set(all_used_blocks)) == 960 # unique across copies
