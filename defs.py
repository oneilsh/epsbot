"""
Dynamic content loaders for external resources.
Fetches content from GitHub URLs when called.
"""

import re
import urllib.request
import bibtexparser
from streamlit import cache_data

@cache_data
def fetch_markdown_content() -> str:
    """
    Fetch the markdown content from the wellcome-poster-supplement repository.
    
    Returns:
        str: The markdown content as a string.
    """
    url = "https://raw.githubusercontent.com/oneilsh/wellcome-poster-supplement/refs/heads/main/pages/index.md"
    with urllib.request.urlopen(url) as response:
        content = response.read().decode('utf-8')
    return content


def parse_bibtex_to_dict(bibtex_string: str) -> dict[str, dict]:
    """
    Parse a BibTeX string into a dictionary keyed by citation key.
    
    Args:
        bibtex_string: The raw BibTeX content as a string.
    
    Returns:
        dict: Dictionary where keys are citation keys (e.g., 'Pfaff2023-ap')
              and values are dictionaries containing parsed BibTeX fields such as:
              - 'ENTRYTYPE': The entry type (e.g., 'article', 'inproceedings')
              - 'author': Author(s) of the work
              - 'title': Title of the work
              - 'year': Publication year
              - 'journal': Journal name (if applicable)
              - 'doi': DOI identifier (if available)
              - 'url': URL (if available)
              - and other fields depending on the entry
    """
    # Clean up the BibTeX string - remove commas between entries (non-standard format)
    # The source file has entries like: @ARTICLE{...} ,@INPROCEEDINGS{...}
    # We need to change "} ,@" to "}\n@" for proper parsing
    cleaned_bibtex = re.sub(r'\}\s*,\s*@', r'}\n@', bibtex_string)
    
    # Parse the BibTeX string using bibtexparser
    bib_database = bibtexparser.loads(cleaned_bibtex)
    
    # Convert the list of entries to a dictionary keyed by citation key
    entries = {}
    for entry in bib_database.entries:
        # The 'ID' field contains the citation key
        citation_key = entry.get('ID')
        if citation_key:
            entries[citation_key] = entry
    
    return entries

@cache_data
def fetch_bibtex_content() -> tuple[str, dict[str, dict]]:
    """
    Fetch the BibTeX content from the wellcome-poster-supplement repository.
    
    Returns:
        tuple: A tuple containing:
            - str: The complete BibTeX content as a string
            - dict: Dictionary keyed by citation key, values are parsed BibTeX entry dictionaries
    """
    url = "https://raw.githubusercontent.com/oneilsh/wellcome-poster-supplement/refs/heads/main/_bibliography/references.bib"
    with urllib.request.urlopen(url) as response:
        content = response.read().decode('utf-8')
    
    bibtex_dict = parse_bibtex_to_dict(content)
    
    return content, bibtex_dict


# Module-level variables that are populated when first accessed
_markdown_content = None
_bibtex_string = None
_bibtex_dict = None


def get_markdown_content() -> str:
    """
    Get the markdown content, fetching it if not already cached.
    
    Returns:
        str: The markdown content.
    """
    global _markdown_content
    if _markdown_content is None:
        _markdown_content = fetch_markdown_content()
    return _markdown_content


def get_bibtex_content() -> tuple[str, dict[str, dict]]:
    """
    Get the BibTeX content, fetching it if not already cached.
    
    Returns:
        tuple: The BibTeX string and dictionary of parsed entries.
    """
    global _bibtex_string, _bibtex_dict
    if _bibtex_string is None or _bibtex_dict is None:
        _bibtex_string, _bibtex_dict = fetch_bibtex_content()
    return _bibtex_string, _bibtex_dict


# Convenience accessors
def markdown_content() -> str:
    """Get the markdown content as a string."""
    return get_markdown_content()


def bibtex_string() -> str:
    """Get the BibTeX content as a complete string."""
    string, _ = get_bibtex_content()
    return string


def bibtex_dict() -> dict[str, dict]:
    """Get the BibTeX content as a dictionary keyed by citation key."""
    _, dict_content = get_bibtex_content()
    return dict_content


# For direct module-level access (will fetch on first import)
if __name__ != "__main__":
    # Auto-fetch when module is imported (not when run directly)
    MARKDOWN_CONTENT = get_markdown_content()
    BIBTEX_STRING, BIBTEX_DICT = get_bibtex_content()

