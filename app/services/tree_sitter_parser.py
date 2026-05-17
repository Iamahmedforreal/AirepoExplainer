from pathlib import Path

EXTENSION_TO_LANGUAGE = {
    ".py":   "python",
    ".js":   "javascript",
    ".ts":   "typescript"
}


def extract_languages_from_clean_files(cleaned_files: list[dict]) -> str | set[str]:
    """Return list of TreeSitter language names for our repo, or None if unsupported ."""

    detect_language = set()

    for file in cleaned_files:
        file_path = file.get("path", " ")
        ext = Path(file_path).suffix.lower()

        language = EXTENSION_TO_LANGUAGE.get(ext)
        if language:
            detect_language.add(language)

    return detect_language
        

    
  