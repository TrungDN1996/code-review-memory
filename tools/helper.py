from pathlib import Path


def get_language_type(path: str) -> str:
    """Return language name for a file path string."""
    if not path:
        return "unknown"
    ext_map = {
        ".ts": "typescript",
        ".tsx": "typescript",
        ".cs": "csharp",
        ".html": "HTML",
        ".aspx": "HTML",
        ".sql": "SQL",
    }
    ext = Path(path).suffix.lower()
    return ext_map.get(ext, "unknown")

def strip_ref(ref: str, prefix: str) -> str:
    return ref.removeprefix(prefix) if ref else ref
