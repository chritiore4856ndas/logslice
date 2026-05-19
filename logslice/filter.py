"""Keyword and regex filtering for log lines within a time-range slice."""

import re
from typing import Optional, Pattern


class LineFilter:
    """Applies optional keyword or regex filtering to log lines."""

    def __init__(
        self,
        keyword: Optional[str] = None,
        pattern: Optional[str] = None,
        ignore_case: bool = False,
    ) -> None:
        self.keyword = keyword
        self.ignore_case = ignore_case
        self._regex: Optional[Pattern] = None

        if pattern is not None:
            flags = re.IGNORECASE if ignore_case else 0
            try:
                self._regex = re.compile(pattern, flags)
            except re.error as exc:
                raise ValueError(f"Invalid regex pattern: {exc}") from exc

        if keyword is not None and ignore_case:
            self.keyword = keyword.lower()

    @property
    def active(self) -> bool:
        """Return True if any filter criterion is configured."""
        return self.keyword is not None or self._regex is not None

    def matches(self, line: str) -> bool:
        """Return True if the line passes all configured filters."""
        if self._regex is not None:
            if not self._regex.search(line):
                return False

        if self.keyword is not None:
            haystack = line.lower() if self.ignore_case else line
            if self.keyword not in haystack:
                return False

        return True


def make_filter(
    keyword: Optional[str] = None,
    pattern: Optional[str] = None,
    ignore_case: bool = False,
) -> Optional[LineFilter]:
    """Return a LineFilter if any criteria are given, else None."""
    if keyword is None and pattern is None:
        return None
    return LineFilter(keyword=keyword, pattern=pattern, ignore_case=ignore_case)
