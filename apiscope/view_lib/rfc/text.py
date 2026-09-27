# apiscope/view_lib/rfc/text.py
def split_pages(text: str) -> tuple[str, ...]:
    return tuple(page for page in text.split("\f") if page.strip())
