from __future__ import annotations
from typing import List, Dict, Any, Tuple


class Configuration:
    """
    A small configuration container for user preferences in the IR system.
    Stores two settings:
      - highlight: whether matches should be highlighted using ANSI colors.
      - search_mode: logical mode for combining multiple search terms ("AND" or "OR").
    """
    def __init__(self) -> None:
        # Default settings used at program startup.
        self.highlight: bool = True
        self.search_mode: str = "AND"

    def copy(self) -> "Configuration":
        """
        Return a *shallow copy* of this configuration object.
        Useful when you want to pass config around without mutating the original.
        """
        copy = Configuration()
        copy.highlight = self.highlight
        copy.search_mode = self.search_mode
        return copy

    def update(self, other: Dict[str, Any]) -> None:
        """
        Update this configuration using values from a (loaded) dictionary.
        Only accepts valid keys and types:
          - "highlight": must be a boolean
          - "search_mode": must be "AND" or "OR"

        Invalid entries are silently ignored, ensuring robustness
        against corrupted or manually edited config files.
        """
        if "highlight" in other and isinstance(other["highlight"], bool):
            self.highlight = other["highlight"]

        if "search_mode" in other and other["search_mode"] in ["AND", "OR"]:
            self.search_mode = other["search_mode"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "highlight": self.highlight,
            "search_mode": self.search_mode,
        }


class Sonnet:
    def __init__(self, sonnet_data: Dict[str, Any]) -> None:
        self.title: str = sonnet_data["title"]
        self.lines: List[str] = sonnet_data["lines"]

    @staticmethod
    def find_spans(text: str, pattern: str) -> List[Tuple[int, int]]:
        """Return [(start, end), ...] for all (possibly overlapping) matches.
        Inputs should already be lowercased by the caller.
        """
        spans: List[Tuple[int, int]] = []
        if not pattern:
            return spans

        for i in range(len(text) - len(pattern) + 1):
            if text[i:i + len(pattern)] == pattern:
                spans.append((i, i + len(pattern)))
        return spans

    def search_for(self, query: str) -> "SearchResult":
        """Search this sonnet for the query and return a SearchResult."""
        q = query.lower()

        # Spans in the title
        title_spans = Sonnet.find_spans(self.title.lower(), q)

        # Spans in the lines
        line_matches: List[LineMatch] = []
        for idx, line_raw in enumerate(self.lines, start=1):
            spans = Sonnet.find_spans(line_raw.lower(), q)
            if spans:
                line_matches.append(
                    LineMatch(line_no=idx, text=line_raw, spans=spans)
                )

        total = len(title_spans) + sum(len(lm.spans) for lm in line_matches)
        return SearchResult(self.title, title_spans, line_matches, total)


class LineMatch:
    def __init__(self, line_no: int, text: str, spans: List[Tuple[int, int]]) -> None:
        self.line_no: int = line_no
        self.text: str = text
        self.spans: List[Tuple[int, int]] = spans

    def copy(self) -> "LineMatch":
        # Copy spans list so we don’t share the same list object
        return LineMatch(self.line_no, self.text, list(self.spans))


class SearchResult:
    def __init__(
        self,
        title: str,
        title_spans: List[Tuple[int, int]],
        line_matches: List["LineMatch"],
        matches: int,
    ) -> None:
        self.title: str = title
        self.title_spans: List[Tuple[int, int]] = title_spans
        self.line_matches: List[LineMatch] = line_matches
        self.matches: int = matches

    def copy(self) -> "SearchResult":
        return SearchResult(
            self.title,
            list(self.title_spans),
            [lm.copy() for lm in self.line_matches],
            self.matches,
        )

    def combine_with(self,other: "SearchResult") -> "SearchResult":
        """Combine two search results."""

        combined = self.copy()  # shallow copy

        # ToDo 0: Use dot notation instead of keys to access the attributes of the search results
        combined.matches = self.matches + other.matches
        combined.title_spans = sorted(
            self.title_spans + other.title_spans
        )

        # Merge line_matches by line number
        # ToDo 0: Instead of using a dictionary, e.g., dict(lm), copy the line match, e.g., lm.copy()!
        lines_by_no = {lm.line_no: lm.copy() for lm in self.line_matches}
        for lm in other.line_matches:
            ln = lm.line_no
            if ln in lines_by_no:
                lines_by_no[ln].spans.extend(lm.spans)
            else:
                lines_by_no[ln] = lm.copy()

        combined.line_matches = sorted(
            lines_by_no.values(), key=lambda lm: lm.line_no
        )

        return combined

    @staticmethod
    def ansi_highlight(text: str, spans: List[Tuple[int, int]]) -> str:
        """Return text with ANSI highlight escape codes inserted."""
        if not spans:
            return text

        spans = sorted(spans)
        merged: List[Tuple[int, int]] = []

        # Merge overlapping spans
        current_start, current_end = spans[0]
        for s, e in spans[1:]:
            if s <= current_end:
                current_end = max(current_end, e)
            else:
                merged.append((current_start, current_end))
                current_start, current_end = s, e
        merged.append((current_start, current_end))

        # Build highlighted string
        out: List[str] = []
        i = 0
        for s, e in merged:

            out.append(text[i:s])
            out.append("\033[43m\033[30m")  # yellow background, black text
            out.append(text[s:e])
            out.append("\033[0m")           # reset
            i = e
        out.append(text[i:])
        return "".join(out)

    def print(self, idx: int, total_docs: int, highlight: bool) -> None:
        """Print this search result to the console."""
        if highlight:
            title_line = SearchResult.ansi_highlight(self.title, self.title_spans)
        else:
            title_line = self.title

        print(f"\n[{idx}/{total_docs}] {title_line}")
        for lm in self.line_matches:
            if highlight:
                line_out = SearchResult.ansi_highlight(lm.text, lm.spans)
            else:
                line_out = lm.text
            print(f"  [{lm.line_no:2}] {line_out}")


