from __future__ import annotations

import sys

_COLOR = sys.stdout.isatty()

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_CYAN = "\033[36m"


def _wrap(code: str, text: str) -> str:
    return f"{code}{text}{_RESET}" if _COLOR else text


def green(text: str) -> str:
    return _wrap(_GREEN, text)


def yellow(text: str) -> str:
    return _wrap(_YELLOW, text)


def red(text: str) -> str:
    return _wrap(_RED, text)


def cyan(text: str) -> str:
    return _wrap(_CYAN, text)


def bold(text: str) -> str:
    return _wrap(_BOLD, text)


def dim(text: str) -> str:
    return _wrap(_DIM, text)


def step(current: int, total: int, label: str) -> None:
    prefix = f"[{current}/{total}]"
    print(f"{cyan(prefix)} {label}")
