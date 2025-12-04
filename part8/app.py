#!/usr/bin/env python3
"""
Part 8 starter CLI.

WHAT'S NEW IN PART 8
Encapsulation 😊. Now we're moving behavior where it belongs.

We are not adding any new functionality, we simply move functions or parts of functions into classes (making them methods).
"""

from typing import List
import json
import os
import time
import urllib.request
import urllib.error

from .constants import BANNER, HELP, POETRYDB_URL, CACHE_FILENAME
from .models import Sonnet, SearchResult, Configuration

# ToDo 3: Move find_spans to Sonnet to make this work.
def find_spans(text: str, pattern: str):
    """Return [(start, end), ...] for all (possibly overlapping) matches.
    Inputs should already be lowercased by the caller."""
    spans = []
    if not pattern:
        return spans

    for i in range(len(text) - len(pattern) + 1):
        if text[i:i + len(pattern)] == pattern:
            spans.append((i, i + len(pattern)))
    return spans


# ToDo 2: You will need to move ansi_highlight to SearchResult as well.
def ansi_highlight(text: str, spans):
    """Return text with ANSI highlight escape codes inserted."""
    if not spans:
        return text

    spans = sorted(spans)
    merged = []

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
    out = []
    i = 0
    for s, e in merged:
        out.append(text[i:s])
        out.append("\033[43m\033[30m")  # yellow background, black text
        out.append(text[s:e])
        out.append("\033[0m")           # reset
        i = e
    out.append(text[i:])
    return "".join(out)


# ToDo 3: Move search_sonnet to the Sonnet class and rename it to 'search_for'
def search_sonnet(sonnet: Sonnet, query: str) -> SearchResult:
    title_raw = str(sonnet["title"])
    lines_raw = sonnet["lines"]  # list[str]

    q = query.lower()
    title_spans = find_spans(title_raw.lower(), q)

    line_matches = []
    for idx, line_raw in enumerate(lines_raw, start=1):  # 1-based line numbers
        spans = find_spans(line_raw.lower(), q)
        if spans:
            line_matches.append(
                # ToDo 0: Use an instance of class LineMatch
                {"line_no": idx, "text": line_raw, "spans": spans}
            )

    total = len(title_spans) + sum(len(lm["spans"]) for lm in line_matches)
    # ToDo 0: Use an instance of class SearchResult
    return {
        "title": title_raw,
        "title_spans": title_spans,
        "line_matches": line_matches,
        "matches": total,
    }


# ToDo 1: Move combine_results to SearchResult. Rename the parameters (use a refactoring of your IDE 😉)!
def combine_results(result1: SearchResult, result2: SearchResult) -> SearchResult:
    """Combine two search results."""

    combined = result1.copy()  # shallow copy

    # ToDo 0: Use dot notation instead of keys to access the attributes of the search results

    combined["matches"] = result1["matches"] + result2["matches"]
    combined["title_spans"] = sorted(
        result1["title_spans"] + result2["title_spans"]
    )

    # Merge line_matches by line number

    # ToDo 0: Instead of using a dictionary, e.g., dict(lm), copy the line match, e.g., lm.copy()!
    lines_by_no = {lm["line_no"]: dict(lm) for lm in result1["line_matches"]}
    for lm in result2["line_matches"]:
        ln = lm["line_no"]
        if ln in lines_by_no:
            # extend spans & keep original text
            lines_by_no[ln]["spans"].extend(lm["spans"])
        else:
            lines_by_no[ln] = dict(lm)

    combined["line_matches"] = sorted(
        lines_by_no.values(), key=lambda lm: lm["line_no"]
    )

    return combined


def print_results(
    query: str,
    results: List[SearchResult],
    highlight: bool,
    query_time_ms: float | None = None,
) -> None:
    total_docs = len(results)
    matched = [r for r in results if r["matches"] > 0]

    line = f'{len(matched)} out of {total_docs} sonnets contain "{query}".'
    if query_time_ms is not None:
        line += f" Your query took {query_time_ms:.2f}ms."
    print(line)

    for idx, r in enumerate(matched, start=1):
        # ToDo 0: Use dot notation instead of key access of the search result

        # ToDo 2: From here on move the printing code to SearchResult.print(...)
        #         You should then be able to call r.print(idx, highlight)
        title_line = (
            ansi_highlight(r["title"], r["title_spans"])
            if highlight
            else r["title"]
        )
        print(f"\n[{idx}/{total_docs}] {title_line}")
        for lm in r["line_matches"]:
            line_out = (
                ansi_highlight(lm["text"], lm["spans"])
                if highlight
                else lm["text"]
            )
            print(f"  [{lm['line_no']:2}] {line_out}")


# ---------- Paths & data loading ----------

def module_relative_path(name: str) -> str:
    """Return absolute path for a file next to this module."""
    return os.path.join(os.path.dirname(__file__), name)


def fetch_sonnets_from_api() -> List[Sonnet]:
    """
    Call the PoetryDB API (POETRYDB_URL), decode the JSON response and
    convert it into a list of dicts.

    - Use only the standard library (urllib.request).
    - PoetryDB returns a list of poems.
    - You can add error handling: raise a RuntimeError (or print a helpful message) if something goes wrong.
    """
    sonnets = []

    try:
        with urllib.request.urlopen(POETRYDB_URL, timeout=10) as response:
            status = getattr(response, "status", None)
            if status not in (None, 200):
                raise RuntimeError(f"Request failed with HTTP status {status}")

            try:
                sonnets = json.load(response)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Failed to decode JSON: {exc}") from exc

    except (urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError) as exc:
        raise RuntimeError(f"Network-related error occurred: {exc}") from exc

    return sonnets


def load_sonnets() -> List[Sonnet]:
    """
    Load Shakespeare's sonnets with caching.

    Behaviour:
      1. If 'sonnets.json' already exists:
           - Print: "Loaded sonnets from cache."
           - Return the data.
      2. Otherwise:
           - Call fetch_sonnets_from_api() to load the data.
           - Print: "Downloaded sonnets from PoetryDB."
           - Save the data (pretty-printed) to CACHE_FILENAME.
           - Return the data.
    """
    sonnets_path = module_relative_path(CACHE_FILENAME)

    if os.path.exists(sonnets_path):
        try:
            with open(sonnets_path, "r", encoding="utf-8") as f:
                try:
                    sonnets = json.load(f)
                except json.JSONDecodeError as exc:
                    raise RuntimeError(f"Corrupt cache file (invalid JSON): {exc}") from exc
        except (OSError, IOError) as exc:
            raise RuntimeError(f"Failed to read cache file: {exc}") from exc

        print("Loaded sonnets from the cache.")
    else:
        sonnets = fetch_sonnets_from_api()
        try:
            with open(sonnets_path, "w", encoding="utf-8") as f:
                try:
                    json.dump(sonnets, f, indent=2, ensure_ascii=False)
                except (TypeError, ValueError) as exc:
                    raise RuntimeError(f"Failed to serialize JSON for cache: {exc}") from exc
        except (OSError, IOError) as exc:
            raise RuntimeError(f"Failed to write cache file: {exc}") from exc

        print("Downloaded sonnets from PoetryDB.")

    # ToDo 0: Convert the sonnets that are represented as dictionaries into instances of the Sonnet class.

    return sonnets
# ---------- Config handling (carry over from Part 5) ----------

DEFAULT_CONFIG = Configuration()

def load_config() -> Configuration:
    config_file_path = module_relative_path("config.json")

    cfg = DEFAULT_CONFIG.copy()
    try:
        with open(config_file_path) as config_file:
            cfg.update(json.load(config_file))
    except FileNotFoundError:
        # File simply doesn't exist yet → quiet, just use defaults
        print("No config.json found. Using default configuration.")
        return cfg
    except json.JSONDecodeError:
        # File exists but is not valid JSON
        print("config.json is invalid. Using default configuration.")
        return cfg
    except OSError:
        # Any other OS / IO problem (permissions, disk issues, etc.)
        print("Could not read config.json. Using default configuration.")
        return cfg

    return cfg

def save_config(cfg: Configuration) -> None:
    config_file_path = module_relative_path("config.json")

    try:
        with open(config_file_path, "w") as config_file:
            json.dump(cfg.to_dict(), config_file, indent=4)
    except OSError:
        print(f"Writing config.json failed.")

# ---------- CLI loop ----------

def main() -> None:
    print(BANNER)
    config = load_config()

    # Load sonnets (from cache or API)
    start = time.perf_counter()
    sonnets = load_sonnets()

    elapsed = (time.perf_counter() - start) * 1000
    print(f"Loading sonnets took: {elapsed:.3f} [ms]")

    print(f"Loaded {len(sonnets)} sonnets.")

    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not raw:
            continue

        # commands
        if raw.startswith(":"):
            if raw == ":quit":
                print("Bye.")
                break

            if raw == ":help":
                print(HELP)
                continue

            if raw.startswith(":highlight"):
                parts = raw.split()
                if len(parts) == 2 and parts[1].lower() in ("on", "off"):
                    config.highlight = parts[1].lower() == "on"
                    print("Highlighting", "ON" if config.highlight else "OFF")
                    save_config(config)
                else:
                    print("Usage: :highlight on|off")
                continue

            if raw.startswith(":search-mode"):
                parts = raw.split()
                if len(parts) == 2 and parts[1].upper() in ("AND", "OR"):
                    config.search_mode = parts[1].upper()
                    print("Search mode set to", config.search_mode)
                    save_config(config)
                else:
                    print("Usage: :search-mode AND|OR")
                continue

            print("Unknown command. Type :help for commands.")
            continue

        # ---------- Query evaluation ----------
        words = raw.split()
        if not words:
            continue

        start = time.perf_counter()

        # query
        combined_results = []

        words = raw.split()

        for word in words:
            # Searching for the word in all sonnets
            # ToDo 3:You will need to adapt the call to search_sonnet
            results = [search_sonnet(s, word) for s in sonnets]

            if not combined_results:
                # No results yet. We store the first list of results in combined_results
                combined_results = results
            else:
                # We have an additional result, we have to merge the two results: loop all sonnets
                for i in range(len(combined_results)):
                    # Checking each sonnet individually
                    combined_result = combined_results[i]
                    result = results[i]

                    # ToDo 0: Use dot notation instead of key access of the search result

                    if config.search_mode == "AND":
                        if combined_result["matches"] > 0 and result["matches"] > 0:
                            # Only if we have matches in both results, we consider the sonnet (logical AND!)
                            # ToDo 1:You will need to adapt the call to combine_results
                            combined_results[i] = combine_results(combined_result, result)
                        else:
                            # Not in both. No match!
                            combined_result["matches"] = 0
                    elif config.search_mode == "OR":
                        # ToDo 1:You will need to adapt the call to combine_results
                        combined_results[i] = combine_results(combined_result, result)

        # Initialize elapsed_ms to contain the number of milliseconds the query evaluation took
        elapsed_ms = (time.perf_counter() - start) * 1000

        print_results(raw, combined_results, config.highlight, elapsed_ms)


if __name__ == "__main__":
    main()
