"""Explicit, small local key-file loader. No dotenv discovery or shell evaluation."""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

KEY_NAME = 'OPENROUTER_API_KEY'
MAX_FILE_BYTES = 8192
PLACEHOLDER = 'REPLACE_WITH_YOUR_OPENROUTER_KEY'
ERROR_CODES = {'ENV_FILE_INVALID', 'ENV_FILE_MISSING_KEY', 'ENV_FILE_PLACEHOLDER', 'ENV_FILE_TOO_LARGE', 'ENV_FILE_UNREADABLE'}


class EnvFileError(ValueError):
    def __init__(self, code):
        self.code = code if code in ERROR_CODES else 'ENV_FILE_INVALID'
        super().__init__(self.code)


def parse_key(text: str) -> str:
    """Only KEY=value, optional literal quotes, comments and blank lines.

    No export, interpolation, escapes, multiline values or inline comments.
    Errors contain no source line, filename or value.
    """
    value = None
    for line in text.removeprefix('\ufeff').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        name, separator, candidate = line.partition('=')
        if not separator or name.strip() != KEY_NAME or value is not None:
            raise EnvFileError('ENV_FILE_INVALID')
        candidate = candidate.strip()
        if candidate.startswith(('"', "'")):
            quote = candidate[0]
            if len(candidate) < 2 or candidate[-1] != quote:
                raise EnvFileError('ENV_FILE_INVALID')
            candidate = candidate[1:-1]
        if not candidate or len(candidate) > 4096 or any(ord(char) < 33 or ord(char) > 126 or char in ('"', "'") for char in candidate):
            raise EnvFileError('ENV_FILE_INVALID')
        if candidate == PLACEHOLDER:
            raise EnvFileError('ENV_FILE_PLACEHOLDER')
        value = candidate
    if value is None:
        raise EnvFileError('ENV_FILE_MISSING_KEY')
    return value


def read_key(path: Path) -> str:
    try:
        with Path(path).open('rb') as file:
            raw = file.read(MAX_FILE_BYTES + 1)
        if len(raw) > MAX_FILE_BYTES:
            raise EnvFileError('ENV_FILE_TOO_LARGE')
        text = raw.decode('utf-8-sig')
    except EnvFileError:
        raise
    except (OSError, UnicodeError, ValueError):
        raise EnvFileError('ENV_FILE_UNREADABLE') from None
    return parse_key(text)


@contextmanager
def scoped_env_file_key(path: Path, *, environ=None):
    """Call only after live authorization. Explicit environment wins, without file I/O.

    The temporary value exists in this Python CLI process, not persistent Windows
    settings. String/process memory erasure cannot be guaranteed.
    """
    environ = os.environ if environ is None else environ
    previous = environ.get(KEY_NAME)
    if previous:
        yield 'environment'
        return
    had_value = KEY_NAME in environ
    key = read_key(path)
    try:
        environ[KEY_NAME] = key
        yield 'env_file'
    finally:
        if had_value:
            environ[KEY_NAME] = previous
        else:
            environ.pop(KEY_NAME, None)
        key = None
