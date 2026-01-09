import asyncio
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.core.paper_parser import PaperParser

# Use a likely S3 URL pattern for IJCAI preprints if exact one isn't known, 
# or search for one. Since we don't have the exact URL, we'll try to find one or use a dummy S3 URL to test PDF handling.
# However, to be precise, I will use a known PDF URL to test the parser's behavior on PDFs.
# Example: A PDF from arXiv or another source that yields raw content.

async def test_pdf_parsing():
    # This is a real PDF URL (arXiv) - behaves similar to the S3 link which is likely a PDF
    url = "https://arxiv.org/pdf/2303.08774.pdf" 
    print(f"Testing PDF URL: {url}")
    try:
        detail = await PaperParser.parse_paper(url)
        print("Title:", detail.title)
        print("Authors:", detail.authors)
        print("Source:", detail.source_site)
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(test_pdf_parsing())
