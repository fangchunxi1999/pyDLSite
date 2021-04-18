import re
from typing import List, Union

REGEX_SET = {"RJ": r"[Rr][Jj][0-9]{6}", "RG": r"[Rr][Gg][0-9]{5}"}


def get_id_code(text: str, id_prefix: str) -> Union[str, None]:
    """
    Return last non-overlapping `id_code` of a provided `id_prefix` in `text`, or `None` if not found.
    """
    id_prefix = id_prefix.upper()
    if id_prefix not in REGEX_SET:
        raise ValueError(
            f"Supported id prefix is \"{'\", \"'.join([p for p in REGEX_SET])}\", but got {id_prefix}"
        )
    pattern = REGEX_SET[id_prefix]
    id_code: List[str] = re.findall(pattern, text)
    if id_code:
        return id_code[-1].upper()


def get_id_num(text: str, id_prefix: str) -> Union[int, None]:
    """
    Return last non-overlapping `id` of a provided `id_prefix` with out `id_prefix` in `text`, or `None` if not found.
    """
    id_prefix = id_prefix.upper()
    id_code = get_id_code(text, id_prefix)
    if id_code:
        return int(id_code.replace(id_prefix, ""))


def is_id_code(id_code: str, id_prefix: str = None) -> bool:
    """
    Check `id_code` is proper format of all supported format or specific format if `id_perfix` is provided
    """
    if id_prefix:
        return is_id_code_prefix(id_code, id_prefix)
    for pattern in REGEX_SET.values():
        if re.match(r"^" + pattern + r"$", id_code):
            return True
    return False


def is_id_code_prefix(id_code: str, id_prefix: str) -> bool:
    """
    Check `id_code` is proper format of provided `id_perfix`
    """
    id_prefix = id_prefix.upper()
    if id_prefix not in REGEX_SET:
        raise ValueError(
            f"Supported id prefix is \"{'\", \"'.join([p for p in REGEX_SET])}\", but got {id_prefix}"
        )
    return True if re.match(r"^" + REGEX_SET[id_prefix] + r"$", id_code) else False
