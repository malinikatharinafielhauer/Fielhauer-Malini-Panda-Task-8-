#!/usr/bin/env python3
"""
Part 8 starter CLI.

WHAT'S NEW IN PART 8
Encapsulation 😊. Now we're moving behavior where it belongs.

We are not adding any new functionality, we simply move functions or parts of
functions into classes (making them methods).
"""
from typing import List
import json
import os
import time
import urllib.request
import urllib.error

from .constants import BANNER, HELP, POETRYDB_URL, CACHE_FILENAME
from .models import Sonnet, SearchResult, Configuration


def print_results(
    query: str,
    results: List[SearchResult],
    highlight: bool,
    query_time_ms: float | None = None,
) -> None:
    total_docs = len(results)
    matched = [r for r in results if r.matches > 0]

    line = f'{len(matched)} out of {total_docs} sonnets contain "{query}".'
    if query_time_ms is not None:
        line += f" Your query took {query_time_ms:.2f}ms."
    print(line)

    for idx, r in enumerate(matched, start=1):
        r.print(idx=idx, total_docs=total_docs, highlight=highlight)


# ---------- Paths & data loading ----------

def module_relative_path(name: str) -> str:
    """Return absolute path for a file next to this module."""
    return os.path.join(os.path.dirname(__file__), name)


def fetch_sonnets_from_api() -> List[Sonnet]:
    """
    Call the PoetryDB API (POETRYDB_URL), decode the JSON response and
    convert it into a list of dicts.
    """
    try:
        with urllib.request.urlopen(POETRYDB_URL, timeout=10) as response:
            status = getattr(response, "status", None)
            if status not in (None, 200):
                raise RuntimeError(f"Request failed with HTTP status {status}")

            try:
                return json.load(response)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Failed to decode JSON: {exc}") from exc

    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Network-related error occurred: {exc}") from exc


def load_sonnets() -> List[Sonnet]:
    """
    Load Shakespeare's sonnets with caching.
    """
    sonnets_path = module_relative_path(CACHE_FILENAME)

    if os.path.exists(sonnets_path):
        try:
            with open(sonnets_path, "r", encoding="utf-8") as f:
                sonnets = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Failed to read cache file: {exc}") from exc

        print("Loaded sonnets from the cache.")
    else:
        sonnets = fetch_sonnets_from_api()
        try:
            with open(sonnets_path, "w", encoding="utf-8") as f:
                json.dump(sonnets, f, indent=2, ensure_ascii=False)
        except OSError as exc:
            raise RuntimeError(f"Failed to write cache file: {exc}") from exc

        print("Downloaded sonnets from PoetryDB.")

    # Convert dicts into Sonnet objects
    return [Sonnet(item) for item in sonnets]


# ---------- Config handling ----------

DEFAULT_CONFIG = Configuration()


def load_config() -> Configuration:
    config_file_path = module_relative_path("config.json")
    cfg = DEFAULT_CONFIG.copy()

    try:
        with open(config_file_path) as config_file:
            cfg.update(json.load(config_file))
    except FileNotFoundError:
        print("No config.json found. Using default configuration.")
    except (json.JSONDecodeError, OSError):
        print("Invalid config.json. Using default configuration.")

    return cfg


def save_config(cfg: Configuration) -> None:
    config_file_path = module_relative_path("config.json")
    try:
        with open(config_file_path, "w") as config_file:
            json.dump(cfg.to_dict(), config_file, indent=4)
    except OSError:
        print("Writing config.json failed.")


# ---------- CLI loop ----------

def main() -> None:
    print(BANNER)
    config = load_config()

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
        combined_results: List[SearchResult] = []

        for word in words:
            results = [s.search_for(word) for s in sonnets]

            if not combined_results:
                combined_results = results
            else:
                for i in range(len(combined_results)):
                    combined_result = combined_results[i]
                    result = results[i]

                    if config.search_mode == "AND":
                        if combined_result.matches > 0 and result.matches > 0:
                            combined_results[i] = combined_result.combine_with(result)
                        else:
                            combined_result.matches = 0
                    elif config.search_mode == "OR":
                        combined_results[i] = combined_result.combine_with(result)
                    else:
                        raise ValueError(f"Unknown search mode: {config.search_mode}")

        elapsed_ms = (time.perf_counter() - start) * 1000
        print_results(raw, combined_results, config.highlight, elapsed_ms)

if __name__ == "__main__":
    main()
