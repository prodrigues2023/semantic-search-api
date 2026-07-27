import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://search:search@localhost:5432/search",
)

EMBEDDING_DIM = 128

# Reciprocal Rank Fusion constant. 60 is the value used in the original RRF
# paper (Cormack et al.) and is not sensitive to the exact rank distribution.
RRF_K = 60

# How many candidates each retrieval leg pulls before fusion. Wide enough
# that fusion has real lists to combine, small enough to stay O(1) for a
# demo-sized corpus.
CANDIDATE_POOL_MULTIPLIER = 5
CANDIDATE_POOL_MIN = 50
