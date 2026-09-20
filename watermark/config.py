# watermark/config.py

# Image standard
CANONICAL_WIDTH  = 512
CANONICAL_HEIGHT = 512

# DWT
DWT_WAVELET = 'haar'
DWT_LEVEL   = 1
DWT_SUBBAND = 'HL'

# DCT
DCT_BLOCK_SIZE = 8
DCT_COEFF_POS_1 = (3, 4)   # row, col (zero-indexed in 8x8 block)
DCT_COEFF_POS_2 = (4, 3)   # row, col (zero-indexed in 8x8 block)

# QIM
DELTA_INITIAL = 30          # Starting value; tune experimentally

# Payload
WATERMARK_MAGIC  = 0x574D5031   # b'WMP1'
PAYLOAD_BITS     = 192
PAYLOAD_BYTES    = 24
MAGIC_BYTES      = 4
UUID_BYTES       = 16
CRC_BYTES        = 4

# Reed-Solomon
RS_NSYM        = 24     # number of parity symbols
RS_K           = 24     # number of data symbols
RS_N           = 48     # total codeword symbols

# Repetition
REPETITIONS = 5

# Block allocation
TOTAL_BLOCKS        = 1024
BLOCKS_PER_RS_COPY  = 192    # RS_N * (8 / BITS_PER_BLOCK) = 48 * 4
BLOCKS_USED         = 960    # REPETITIONS * BLOCKS_PER_RS_COPY
BLOCK_SELECT_SEED   = 0x574D5031

# Quality acceptance thresholds
PSNR_MIN_DB  = 35.0
SSIM_MIN     = 0.95
