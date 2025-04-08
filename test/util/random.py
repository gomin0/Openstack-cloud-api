import random
import string


def random_int(min_val: int = 1, max_val: int = 1_000_000) -> int:
    return random.randint(min_val, max_val)


def random_string(length: int = 10) -> str:
    all_characters = string.ascii_letters + string.digits
    return "".join(random.choices(all_characters, k=length))
