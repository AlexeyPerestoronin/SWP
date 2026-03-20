import difflib
import functools

from typing import List


def longest_common_substring(strings: List[str]) -> str:
    """
    Returns longest common substring for all strings in the list using difflib.
    """
    if not strings:
        return ""
    if len(strings) == 1:
        return strings[0]

    def lcs_pair(a: str, b: str) -> str:
        matcher = difflib.SequenceMatcher(None, a, b)
        match = matcher.find_longest_match(0, len(a), 0, len(b))
        return a[match.a:match.a + match.size]

    return functools.reduce(lcs_pair, strings)


from .logger import SUCCESS, STATUS, INFO, WARNING, ERROR