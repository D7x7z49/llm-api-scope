# apiscope/commands/rfc.py
"""
RFC (Request for Comments) document reader.

Provides commands to search and read IETF RFC documents from the RFC Editor.
https://www.rfc-editor.org/
"""
import click
import httpx
from pathlib import Path
from ..core.output import OutputBuilder
from ..core.config import GLOBAL_CONFIG


RFC_BASE_URL = "https://www.rfc-editor.org"
RFC_SEARCH_URL = "https://www.rfc-editor.org/search/search.php"


@click.group()
def rfc_command():
    """
    Search and read IETF RFC documents.
    
    RFCs are technical and organizational documents about the Internet,
    including specifications and policy documents.
    """
    pass


@rfc_command.command()
@click.argument('number', type=int)
@click.option('--cache', is_flag=True, help='Cache RFC locally')
@click.pass_context
def read(ctx: click.Context, number: int, cache: bool):
    """
    Read a specific RFC document.
    
    NUMBER: RFC number (e.g., 9110 for HTTP/1.1)
    
    Examples:
        apiscope rfc read 9110
        apiscope rfc read 7231 --cache
    """
    output = OutputBuilder()
    output.section(f"RFC {number}")
    
    # RFC URL
    rfc_url = f"{RFC_BASE_URL}/rfc/rfc{number:04d}.txt"
    rfc_html_url = f"{RFC_BASE_URL}/rfc/rfc{number:04d}"
    
    output.action(f"Fetching RFC {number}")
    
    try:
        # Check environment variables for proxy (httpx reads these automatically)
        import os
        http_proxy = os.getenv('http_proxy') or os.getenv('HTTP_PROXY')
        https_proxy = os.getenv('https_proxy') or os.getenv('HTTPS_PROXY')
        
        if http_proxy or https_proxy:
            output.note(f"Using proxy: {http_proxy or https_proxy}")
        
        # httpx automatically uses environment proxy variables
        with httpx.Client() as client:
            response = client.get(rfc_url, timeout=30.0)
            
            if response.status_code == 404:
                output.result(f"RFC {number} not found")
                output.note(f"Check the number: {RFC_BASE_URL}/search/search.php")
                output.complete("Read RFC")
                output.emit()
                return
            
            response.raise_for_status()
            rfc_content = response.text
            
        output.result(f"Successfully fetched RFC {number}")
        
        # Cache if requested
        if cache:
            cache_dir = GLOBAL_CONFIG.get_cache_dir() / "rfc"
            cache_dir.mkdir(exist_ok=True)
            cache_file = cache_dir / f"rfc{number:04d}.txt"
            cache_file.write_text(rfc_content)
            output.result(f"Cached to: {cache_file}")
        
        # Display RFC metadata (first few lines)
        output.action("RFC Information")
        lines = rfc_content.split('\n')
        
        # Find title and metadata
        in_header = False
        header_lines = []
        number_str = str(number)
        for line in lines[:50]:
            if 'Request for Comments:' in line or ('RFC' in line and number_str in line):
                in_header = True
            if in_header:
                header_lines.append(line)
                if 'Category:' in line or 'Published:' in line:
                    continue
        
        # Print first 30 lines as preview
        output.note("Preview (first 30 lines):")
        for line in lines[:30]:
            click.echo(line)
        
        if len(lines) > 30:
            output.note(f"... ({len(lines) - 30} more lines)")
        
        output.action("Access Options")
        output.note(f"Plain text: {rfc_url}")
        output.note(f"HTML version: {rfc_html_url}")
        
        # If not cached, suggest caching
        if not cache:
            output.note("Use --cache to save locally for offline access")
        
        output.complete("Read RFC")
        output.emit()
        
    except httpx.RequestError as e:
        output.result(f"Failed to fetch RFC {number}")
        output.note(f"Error: {str(e)}")
        output.note("Check your network connection and proxy settings")
        output.complete("Read RFC")
        output.emit()
        return


@rfc_command.command()
@click.argument('keywords', nargs=-1, required=True)
@click.option('--limit', default=10, help='Maximum results to show')
@click.pass_context
def search(ctx: click.Context, keywords: tuple, limit: int):
    """
    Search RFC documents by keywords.
    
    KEYWORDS: Space-separated search terms
    
    Examples:
        apiscope rfc search HTTP
        apiscope rfc search REST API design
    """
    output = OutputBuilder()
    output.section("Search RFC")
    
    query = ' '.join(keywords)
    output.action(f"Searching for: {query}")
    
    try:
        # RFC Editor doesn't have a public JSON API, so we'll use a simple approach
        # In production, you might want to scrape the search results or use a different API
        
        # For now, provide guidance on manual search
        search_url = f"{RFC_SEARCH_URL}?search={query.replace(' ', '+')}"
        
        output.result(f"RFC Editor Search")
        output.note(f"Search URL: {search_url}")
        output.note("RFC Editor doesn't provide a JSON API for programmatic search")
        output.note(f"Open in browser: gh browse '{search_url}'")
        
        # Suggest alternative: use web search
        output.action("Alternative Search Methods")
        output.note(f"Google: https://www.google.com/search?q=site:rfc-editor.org+{query.replace(' ', '+')}")
        output.note(f"DuckDuckGo: https://duckduckgo.com/?q=site:rfc-editor.org+{query.replace(' ', '+')}")
        
        output.complete("Search RFC")
        output.emit()
        
    except Exception as e:
        output.result("Search failed")
        output.note(f"Error: {str(e)}")
        output.complete("Search RFC")
        output.emit()


@rfc_command.command()
@click.option('--status', type=click.Choice(['standards', 'bcp', 'informational', 'experimental', 'historic']), help='Filter by status')
@click.option('--author', help='Filter by author')
@click.pass_context
def list(ctx: click.Context, status: str, author: str):
    """
    List RFC documents by category.
    
    Examples:
        apiscope rfc list --status standards
        apiscope rfc list --author "Fielding"
    """
    output = OutputBuilder()
    output.section("List RFCs")
    
    output.action("RFC Categories")
    
    categories = {
        'standards': 'Official Internet Protocol Standards',
        'bcp': 'Best Current Practice',
        'informational': 'Informational RFCs',
        'experimental': 'Experimental RFCs',
        'historic': 'Historic RFCs',
    }
    
    if status:
        output.result(f"Category: {status.upper()}")
        output.note(f"Description: {categories.get(status, 'Unknown')}")
        browse_url = f"{RFC_BASE_URL}/search/rfc_search_detail.php?pubstatus%5B%5D={status.capitalize()}"
        output.note(f"Browse: {browse_url}")
    else:
        for cat, desc in categories.items():
            output.note(f"{cat.upper()}: {desc}")
    
    if author:
        output.action(f"Author: {author}")
        output.note(f"Search: {RFC_SEARCH_URL}?search=author%3A{author.replace(' ', '+')}")
    
    output.action("Browse All RFCs")
    output.note(f"RFC Index (HTML): {RFC_BASE_URL}/rfc-index-100a.html")
    output.note(f"RFC Index (TXT): {RFC_BASE_URL}/rfc-index.txt")
    
    output.complete("List RFCs")
    output.emit()


@rfc_command.command()
@click.argument('number', type=int)
@click.option('--note-path', help='Path to note file to add reference')
@click.pass_context
def reference(ctx: click.Context, number: int, note_path: str):
    """
    Reference an RFC in a note.
    
    NUMBER: RFC number to reference
    
    Examples:
        apiscope rfc reference 9110 --note-path my-note.txt
    """
    output = OutputBuilder()
    output.section(f"Reference RFC {number}")
    
    rfc_url = f"{RFC_BASE_URL}/rfc/rfc{number:04d}"
    reference_text = f"[RFC {number}]({rfc_url})"
    
    output.result(f"RFC {number} Reference")
    output.note(f"Markdown: {reference_text}")
    output.note(f"Plain: RFC {number} - {rfc_url}")
    
    if note_path:
        output.action(f"Adding to note: {note_path}")
        note_file = Path(note_path)
        if note_file.exists():
            content = note_file.read_text()
            content += f"\n\nReferences:\n- {reference_text}\n"
            note_file.write_text(content)
            output.result("Reference added to note")
        else:
            output.note(f"Note file not found: {note_path}")
            output.note("Create the note first with 'apiscope note write'")
    
    output.complete("Reference RFC")
    output.emit()
