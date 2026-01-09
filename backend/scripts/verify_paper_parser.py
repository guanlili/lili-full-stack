import asyncio
import sys
import os

# Add backend directory to path so we can import app
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.paper_parser import PaperParser

async def test_parser():
    urls = [
        "https://arxiv.org/abs/2303.08774", # arXiv
        "https://ieeexplore.ieee.org/document/10121396", # IEEE
        "https://link.springer.com/article/10.1007/s10955-023-03120-8", # Springer
    ]

    for url in urls:
        print(f"Testing URL: {url}")
        try:
            detail = await PaperParser.parse_paper(url)
            print("Title:", detail.title)
            print("Authors:", detail.authors[:3] if detail.authors else "None", "..." if detail.authors and len(detail.authors)>3 else "")
            print("Date:", detail.publication_date)
            print("Venue:", detail.venue)
            print("DOI:", detail.doi)
            print("Source:", detail.source_site)
            print("-" * 50)
        except Exception as e:
            print(f"FAILED: {e}")
            print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_parser())
