import random
from typing import Any, Callable, List


PRINTABLE_MIN = 0x20
PRINTABLE_MAX = 0x7E
MAX_BLOCK_SIZE = 16
ARITHMETIC_DELTA = 35

INTERESTING_VALUES = {
    1: [0, 1, 9, 10, 13, 16, 31, 32, 64, 65, 90, 97, 122, 127, 128, 255],
    2: [0, 1, 255, 256, 512, 1024, 4096, 32767, 32768, 65535],
    4: [0, 1, 65535, 65536, 2147483647, 2147483648, 4294967295],
}

DICTIONARY_TOKENS = [
    "0", "1", "-1", "0.0", "1.0", "nan", "inf", ".", "{}", "{Key}",
    "FDU", "LAB", "<html>", "</html>", "<script>", "&lt;", "\n",
]


def _coerce_input(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("latin-1")
    return str(value)


def _to_bytes(value: Any) -> bytearray:
    return bytearray(_coerce_input(value).encode("latin-1", errors="replace"))


def _from_bytes(data: bytearray) -> str:
    return bytes(data).decode("latin-1")


def _random_printable_byte() -> int:
    return random.randint(PRINTABLE_MIN, PRINTABLE_MAX)


def _choose_width(max_len: int) -> int:
    return random.choice([width for width in (1, 2, 4) if width <= max_len])


def _random_block(data: bytearray) -> bytearray:
    if not data:
        return bytearray([_random_printable_byte()])
    block_len = random.randint(1, min(MAX_BLOCK_SIZE, len(data)))
    start = random.randint(0, len(data) - block_len)
    return data[start:start + block_len]


def insert_random_character(s: str) -> str:
    """Insert one printable byte at a random position."""
    data = _to_bytes(s)
    pos = random.randint(0, len(data))
    data[pos:pos] = bytes([_random_printable_byte()])
    return _from_bytes(data)


def delete_random_character(s: str) -> str:
    """Delete one byte without producing an empty candidate."""
    data = _to_bytes(s)
    if len(data) <= 1:
        return insert_random_character(s)
    del data[random.randint(0, len(data) - 1)]
    return _from_bytes(data)


def flip_random_bits(s: str) -> str:
    """Flip 1, 2, or 4 adjacent bits."""
    data = _to_bytes(s)
    if not data:
        return insert_random_character(s)

    total_bits = len(data) * 8
    width = random.choice([width for width in (1, 2, 4) if width <= total_bits])
    bit_index = random.randint(0, total_bits - width)
    for offset in range(width):
        current_bit = bit_index + offset
        data[current_bit // 8] ^= 1 << (current_bit % 8)
    return _from_bytes(data)


def arithmetic_random_bytes(s: str) -> str:
    """Add or subtract a small delta from 1, 2, or 4 adjacent bytes."""
    data = _to_bytes(s)
    if not data:
        return insert_random_character(s)

    width = _choose_width(len(data))
    pos = random.randint(0, len(data) - width)
    for index in range(pos, pos + width):
        delta = random.randint(-ARITHMETIC_DELTA, ARITHMETIC_DELTA) or 1
        data[index] = (data[index] + delta) % 256
    return _from_bytes(data)


def interesting_random_bytes(s: str) -> str:
    """Replace adjacent bytes with boundary-like integer values."""
    data = _to_bytes(s)
    if not data:
        return insert_random_character(s)

    width = _choose_width(len(data))
    pos = random.randint(0, len(data) - width)
    value = random.choice(INTERESTING_VALUES[width])
    data[pos:pos + width] = value.to_bytes(width, byteorder="little", signed=False)
    return _from_bytes(data)


def havoc_random_insert(s: str) -> str:
    """Insert a copied input block or random printable bytes."""
    data = _to_bytes(s)
    if not data:
        return insert_random_character(s)

    pos = random.randint(0, len(data))
    if random.random() < 0.75:
        block = _random_block(data)
    else:
        block_len = random.randint(1, min(MAX_BLOCK_SIZE, len(data)))
        block = bytearray(_random_printable_byte() for _ in range(block_len))
    data[pos:pos] = block
    return _from_bytes(data)


def havoc_random_replace(s: str) -> str:
    """Replace a random block with copied or random bytes."""
    data = _to_bytes(s)
    if not data:
        return insert_random_character(s)

    replace_len = random.randint(1, min(MAX_BLOCK_SIZE, len(data)))
    pos = random.randint(0, len(data) - replace_len)
    if random.random() < 0.75:
        replacement = _random_block(data)
    else:
        replacement = bytearray(_random_printable_byte() for _ in range(replace_len))
    data[pos:pos + replace_len] = replacement
    return _from_bytes(data)


def random_block_swap(s: str) -> str:
    """Swap two adjacent byte blocks."""
    data = _to_bytes(s)
    if len(data) < 2:
        return insert_random_character(s)

    first_len = random.randint(1, min(MAX_BLOCK_SIZE, len(data) - 1))
    second_len = random.randint(1, min(MAX_BLOCK_SIZE, len(data) - first_len))
    start = random.randint(0, len(data) - first_len - second_len)
    first = data[start:start + first_len]
    second = data[start + first_len:start + first_len + second_len]
    data[start:start + first_len + second_len] = second + first
    return _from_bytes(data)


def insert_dictionary_token(s: str) -> str:
    """Insert a token tailored to the provided numeric, format, and HTML samples."""
    data = _to_bytes(s)
    token = random.choice(DICTIONARY_TOKENS).encode("latin-1")
    pos = random.randint(0, len(data))
    data[pos:pos] = token
    return _from_bytes(data)


class Mutator:
    def __init__(self) -> None:
        self.mutators: List[Callable[[str], str]] = [
            insert_random_character,
            delete_random_character,
            flip_random_bits,
            arithmetic_random_bytes,
            interesting_random_bytes,
            havoc_random_insert,
            havoc_random_replace,
            random_block_swap,
            insert_dictionary_token,
        ]

    def mutate(self, inp: Any) -> str:
        original = _coerce_input(inp)
        for _ in range(3):
            candidate = random.choice(self.mutators)(original)
            if candidate and candidate != original:
                return candidate
        return insert_random_character(original)
