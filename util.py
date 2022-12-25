import re
from typing import List, Tuple, Union

REGEX_PREFIX = {"RJ": r"[Rr][Jj][0-9]{8}", "RG": r"[Rr][Gg][0-9]{5}"}


def get_id_code(text: str, id_prefix: str) -> Union[str, None]:
    """
    Return last non-overlapping `id_code` of a provided `id_prefix` in `text`, or `None` if not found.
    """
    id_prefix = id_prefix.upper()
    if id_prefix not in REGEX_PREFIX:
        _SEP = '", "'
        raise ValueError(
            f'Supported id prefix is "{_SEP.join([p for p in REGEX_PREFIX])}", but got {id_prefix}'
        )
    pattern = REGEX_PREFIX[id_prefix]
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
    for pattern in REGEX_PREFIX.values():
        if re.match(r"^" + pattern + r"$", id_code):
            return True
    return False


def is_id_code_prefix(id_code: str, id_prefix: str) -> bool:
    """
    Check `id_code` is proper format of provided `id_perfix`
    """
    id_prefix = id_prefix.upper()
    if id_prefix not in REGEX_PREFIX:
        _SEP = '", "'
        raise ValueError(
            f'Supported id prefix is "{_SEP.join([p for p in REGEX_PREFIX])}", but got {id_prefix}'
        )
    return True if re.match(r"^" + REGEX_PREFIX[id_prefix] + r"$", id_code) else False


def get_humanread_byte(
    byte: int,
    step: int = 1024,
    subfix_list: List[str] = ["B", "KiB", "MiB", "GiB", "TiB"],
) -> Tuple[float, str]:
    size = byte
    subfix = subfix_list[0]
    for i, _subfix in enumerate(subfix_list):
        _size = size / step
        if _size < 1 or i == len(subfix_list) - 1:
            subfix = _subfix
            break
        size = _size

    return size, subfix


def get_humanread_str_byte(
    byte: int,
    step: int = 1024,
    subfix_list: List[str] = ["B", "KiB", "MiB", "GiB", "TiB"],
):
    size, subfix = get_humanread_byte(byte, step, subfix_list)
    return f"{size} {subfix}"


def get_byte_humanread_str(
    humanread_str: str, step: int = 1024, step_prefix: List[str] = ["K", "M", "G", "T"]
) -> int:
    REGEX_HUMAN_SIZE = r"([\d]+\.?[\d]*) ?([{}]I?B?)".format(
        "".join(["K", "M", "G", "T"])
    )
    match = re.findall(REGEX_HUMAN_SIZE, humanread_str.upper())
    if not match:
        return -1

    size, subfix = match[-1]
    size = float(size)
    subfix = str(subfix)
    for power, prefix in enumerate(step_prefix, start=1):
        if subfix.find(prefix) >= 0:
            return round(size * (step ** power))

    return round(size)
