import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.core.paper_parser import PaperParser

async def test_ijcai_parsing():
    # Attempt to parse the PDF URL directly. 
    # The parser should rewrite this to the abstract page and succeed.
    url = "https://www.ijcai.org/proceedings/2025/0585.pdf" 
    print(f"Testing IJCAI PDF URL: {url}")
    try:
        detail = await PaperParser.parse_paper(url)
        print("Title:", detail.title)
        print("Authors:", detail.authors)
        print("Source:", detail.source_site)
        print("Final URL:", detail.url) # Check if URL stored is the abstract one or original
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_ijcai_parsing())
