import io
from typing import Any

import httpx
import pandas as pd
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser
from app.models import (
    ScholarAuthor,
    ScholarPublication,
    ScholarSearchResults,
    ScholarExportData,
)

router = APIRouter(prefix="/scholar", tags=["scholar"])


def parse_scholar_html(html: str) -> ScholarSearchResults:
    soup = BeautifulSoup(html, "html.parser")
    publications = []
    authors = []

    # 1. Parse author profiles
    for author_row in soup.select(".gs_scl"):
        name_tag = author_row.select_one(".gs_ai_name a")
        if name_tag:
            name = name_tag.text
            href = name_tag.get("href", "")
            scholar_id = ""
            if "user=" in href:
                scholar_id = href.split("user=")[1].split("&")[0]

            affiliation = ""
            aff_tag = author_row.select_one(".gs_ai_aff")
            if aff_tag:
                affiliation = aff_tag.text

            interests = []
            for int_tag in author_row.select(".gs_ai_int a"):
                interests.append(int_tag.text)

            img_tag = author_row.select_one(".gs_ai_img img")
            url_picture = img_tag.get("src") if img_tag else None
            if url_picture and url_picture.startswith("/"):
                url_picture = f"https://scholar.google.com{url_picture}"

            authors.append(
                ScholarAuthor(
                    name=name,
                    scholar_id=scholar_id,
                    affiliation=affiliation,
                    interests=interests,
                    url_picture=url_picture,
                )
            )

    # 2. Parse publications
    for result in soup.select(".gs_ri"):
        title_tag = result.select_one(".gs_rt a")
        title = ""
        link = None
        if title_tag:
            title = title_tag.text
            link = title_tag.get("href")
        else:
            title_container = result.select_one(".gs_rt")
            if title_container:
                title = title_container.text

        snippet_tag = result.select_one(".gs_rs")
        snippet = snippet_tag.text if snippet_tag else ""

        info_tag = result.select_one(".gs_a")
        info_text = info_tag.text if info_tag else ""
        
        # Standardize info parsing: "Authors - Venue, Year - Publisher"
        parts = info_text.split(" - ")
        authors_str = parts[0] if len(parts) > 0 else ""
        venue_year = parts[1] if len(parts) > 1 else ""
        
        # Robust year extraction using regex (looks for 4-digit year between 1900 and 2099)
        import re
        year_match = re.search(r"\b(19|20)\d{2}\b", info_text)
        year = year_match.group(0) if year_match else None
        
        venue = venue_year
        if year and year in venue:
            venue = venue.replace(year, "").strip(" ,")

        # Parse footer for cited_by and versions
        cited_by = None
        versions = None
        footer_links = result.parent.select(".gs_fl a")
        for link_tag in footer_links:
            text = link_tag.text.lower()
            if "cited by" in text or "引用" in text:
                try:
                    num = "".join(filter(str.isdigit, text))
                    if num: cited_by = int(num)
                except: pass
            elif "versions" in text or "个版本" in text:
                try:
                    num = "".join(filter(str.isdigit, text))
                    if num: versions = int(num)
                except: pass

        publications.append(
            ScholarPublication(
                title=title,
                link=link,
                snippet=snippet,
                authors=authors_str,
                venue=venue,
                year=year,
                cited_by=cited_by,
                versions=versions,
            )
        )

    return ScholarSearchResults(
        authors=authors,
        publications=publications,
        count=len(authors) + len(publications),
    )


async def fetch_scholar_html(params: dict) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://scholar.google.com/",
    }
    url = "https://scholar.google.com/scholar"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params, headers=headers, follow_redirects=True)
        if response.status_code != 200:
            if response.status_code in [302, 301]:
                raise HTTPException(status_code=429, detail="Blocked by Google Scholar (Captcha).")
            raise HTTPException(status_code=response.status_code, detail=f"Google Error: {response.status_code}")
        return response.text


@router.get("/search", response_model=ScholarSearchResults)
async def search_scholar(
    current_user: CurrentUser,
    q: str,
    hl: str | None = "en",
    as_ylo: int | None = None,
    as_yhi: int | None = None,
    as_vis: int | None = None,
    as_sdt: str | None = None,
    start: int | None = 0,
) -> Any:
    params = {"q": q, "hl": hl, "start": start}
    if as_ylo: params["as_ylo"] = as_ylo
    if as_yhi: params["as_yhi"] = as_yhi
    if as_vis is not None: params["as_vis"] = as_vis
    if as_sdt: params["as_sdt"] = as_sdt

    html = await fetch_scholar_html(params)
    return parse_scholar_html(html)


@router.post("/export")
async def export_scholar(
    current_user: CurrentUser,
    data: ScholarExportData,
) -> Any:
    # Create DataFrame from received data
    pub_data = [
        {
            "Title": p.title,
            "Authors": p.authors,
            "Venue": p.venue,
            "Year": p.year,
            "Cited By": p.cited_by,
            "Versions": p.versions,
            "Link": p.link,
            "Snippet": p.snippet
        }
        for p in data.publications
    ]
    
    columns = ["Title", "Authors", "Venue", "Year", "Cited By", "Versions", "Link", "Snippet"]
    df = pd.DataFrame(pub_data, columns=columns)
    
    # Export to Excel in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Scholar Results")
    
    output.seek(0)
    
    filename = data.filename or "scholar_results.xlsx"
    if not filename.endswith(".xlsx"):
        filename += ".xlsx"

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
