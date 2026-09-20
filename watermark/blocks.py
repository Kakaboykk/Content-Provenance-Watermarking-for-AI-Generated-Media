import random
from typing import List
from watermark.config import BLOCK_SELECT_SEED, TOTAL_BLOCKS, BLOCKS_PER_RS_COPY, REPETITIONS

def get_block_permutation() -> List[int]:
    """
    Generate the deterministic public block permutation of 1024 blocks.
    Uses the fixed magic seed.
    """
    rng = random.Random(BLOCK_SELECT_SEED)
    indices = list(range(TOTAL_BLOCKS))
    rng.shuffle(indices)
    return indices

def get_copy_blocks(copy_index: int) -> List[int]:
    """
    Get the block indices assigned to a specific repetition copy (0-4).
    Each copy gets 192 blocks.
    """
    if not (0 <= copy_index < REPETITIONS):
        raise ValueError(f"Copy index must be between 0 and {REPETITIONS - 1}")
        
    indices = get_block_permutation()
    start = copy_index * BLOCKS_PER_RS_COPY
    end = start + BLOCKS_PER_RS_COPY
    return indices[start:end]
