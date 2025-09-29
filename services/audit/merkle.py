import hashlib
from typing import Iterable, Sequence

def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def merkle_root(leaves: Sequence[bytes]) -> bytes:
    if not leaves:
        return sha256(b'') # empty tree convention
    level = [sha256(x) for x in leaves] # hash leaves once
    while len(level) > 1:
        it = iter(level)
        next_level = []
        for a in it:
            b = next(it, a) # duplicate last if odd
            next_level.append(sha256(a + b))
        level = next_level
    return level[0]