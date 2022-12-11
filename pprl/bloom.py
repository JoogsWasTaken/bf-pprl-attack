import base64
import hashlib
import struct

from bitarray import bitarray


def new_bf(m: int) -> bitarray:
    """Creates a new Bloom filter of size m."""
    ba = bitarray(m)
    ba.setall(0)
    return ba


def encode_bf(bf: bitarray) -> str:
    """Encodes the contents of a Bloom filter using Base64."""
    return base64.b64encode(bf.tobytes()).decode("utf-8")


def decode_bf(s: str) -> bitarray:
    """Decodes a Base64 string into a Bloom filter."""
    ba = bitarray()
    ba.frombytes(base64.b64decode(s.encode("utf-8")))
    return ba


def compute_hash_values(k: int, value: bytes) -> list[int]:
    """Computes k hash values from bytes using the SHA-256 double hashing scheme."""
    value_hash = hashlib.sha256(value).digest()

    h1 = struct.unpack("Q", value_hash[0:8])[0]
    h2 = struct.unpack("Q", value_hash[8:16])[0]

    return [h1 + (i + 1) * h2 for i in range(k)]


def populate_bf(bf: bitarray, k: int, value: bytes):
    """Sets k bits in a Bloom filter after hashing the specified bytes."""
    m = len(bf)

    for h in compute_hash_values(k, value):
        if h < 0:  # little hack
            h = -h

        bf[h % m] = 1


def tokenize(s: str, q: int) -> set[str]:
    """Splits a string into text tokens of size q."""
    tokens = set()

    # surround string by padding characters
    pad = "_" * (q-1)
    s = pad + s + pad

    for i in range(len(s) - q + 1):
        tokens.add(s[i:i + q].upper())

    return tokens
