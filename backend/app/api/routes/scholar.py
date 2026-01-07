import io
import json
from datetime import datetime
from typing import Any

import asyncio
import random
import httpx
import pandas as pd
from bs4 import BeautifulSoup
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUser, get_db
from app import crud
from app.models import (
    ScholarAuthor,
    ScholarPublication,
    ScholarSearchResults,
    ScholarExportData,
    SearchHistory,
    CacheEntry,
)

router = APIRouter(prefix="/scholar", tags=["scholar"])


async def fetch_scholar_html(params: dict) -> str:
    base_url = "https://scholar.google.com/scholar"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    }
    
    # 随机延迟，模拟人类行为
    await asyncio.sleep(random.uniform(0.5, 1.5))
    
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30.0) as client:
        try:
            resp = await client.get(base_url, params=params)
            
            if resp.status_code == 429:
                print("Google Scholar Rate Limit 429 Hit!")
                raise HTTPException(status_code=429, detail="Google Scholar rate limit exceeded. Please try again later.")
                
            if resp.status_code != 200:
                print(f"Google Scholar Error: {resp.status_code}")
                raise HTTPException(status_code=resp.status_code, detail=f"Failed to fetch from Google Scholar: {resp.status_code}")
                
            return resp.text
            
        except httpx.RequestError as e:
            print(f"Network Error: {e}")
            raise HTTPException(status_code=500, detail=f"Network error connecting to Google Scholar: {str(e)}")


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


from fastapi import Depends
from sqlmodel import Session
from app.api.deps import get_db

import re

# ... existing imports ...

@router.get("/search", response_model=ScholarSearchResults)
async def search_scholar(
    current_user: CurrentUser,
    q: str,
    year: int,  # 年份为必选项
    hl: str | None = "en",
    sort: str = "relevance",
    max_pages: int = 1, # Default to 1 page
    as_vis: int | None = 1,
    as_sdt: str | None = "2007",
    session: Session = Depends(get_db),
) -> Any:
    """
    搜索指定年份的所有文献。年份为必选参数，会自动循环获取该年份所有分页的结果。
    """
    # Cap max_pages at 100 for safety
    if max_pages > 100:
        max_pages = 100
    if max_pages < 1:
        max_pages = 1

    # Generate cache key based on parameters
    cache_key = json.dumps({
        "q": q, 
        "year": year, 
        "hl": hl, 
        "sort": sort,
        "max_pages": max_pages,
        "as_vis": as_vis, 
        "as_sdt": as_sdt
    })
    # Try cache
    cached = crud.get_cache_entry(session=session, key=cache_key)
    if cached:
        # Record history as cache hit
        crud.create_history_entry(
            session=session,
            key=cache_key,
            url=None,
            summary=f"Cache hit for query '{q}' year {year}",
            source="cache",
        )
        return json.loads(cached.result_json)

    # No cache, perform fetch
    all_authors = []
    all_publications = []
    start = 0
    
    for page in range(max_pages):
        params = {
            "q": q,
            "hl": hl,
            "start": start,
            "as_ylo": year,
            "as_yhi": year,
            "as_vis": as_vis,
            "as_sdt": as_sdt,
        }
        
        # Add date sorting if requested
        if sort == "date":
            params["scisbd"] = 1
            
        html = await fetch_scholar_html(params)
        page_results = parse_scholar_html(html)
        
        if page == 0:
            all_authors.extend(page_results.authors)
            
        all_publications.extend(page_results.publications)

        if len(page_results.publications) < 10:
            break
        start += 10
        # random delay already added in fetch loop
    result = ScholarSearchResults(
        authors=all_authors,
        publications=all_publications,
        count=len(all_authors) + len(all_publications),
    )
    # Store in cache
    crud.create_cache_entry(session=session, key=cache_key, result=result)
    # Record history as remote fetch
    crud.create_history_entry(
        session=session,
        key=cache_key,
        url=None,
        summary=f"Fetched {len(all_publications)} publications",
        source="remote",
    )
    return result
    """
    搜索指定年份的所有文献。年份为必选参数，会自动循环获取该年份所有分页的结果。
    """
    # Generate cache key based on parameters
    cache_key = json.dumps({"q": q, "year": year, "hl": hl, "as_vis": as_vis, "as_sdt": as_sdt})
    # Try cache
    cached = crud.get_cache_entry(session=Session, key=cache_key)
    if cached:
        # Record history as cache hit
        crud.create_history_entry(
            session=Session,
            key=cache_key,
            url=None,
            summary=f"Cache hit for query '{q}' year {year}",
            source="cache",
        )
        return json.loads(cached.result_json)

    # No cache, perform fetch
    all_authors = []
    all_publications = []
    start = 0
    max_pages = 100
    for page in range(max_pages):
        params = {
            "q": q,
            "hl": hl,
            "start": start,
            "as_ylo": year,
            "as_yhi": year,
            "as_vis": as_vis,
            "as_sdt": as_sdt,
            "scisbd": 1,
        }
        html = await fetch_scholar_html(params)
        page_results = parse_scholar_html(html)
        if page == 0:
            all_authors.extend(page_results.authors)
        all_publications.extend(page_results.publications)
        if len(page_results.publications) < 10:
            break
        start += 10
        # random delay already added in fetch loop
    result = ScholarSearchResults(
        authors=all_authors,
        publications=all_publications,
        count=len(all_authors) + len(all_publications),
    )
    # Store in cache
    crud.create_cache_entry(session=session, key=cache_key, result=result)
    # Record history as remote fetch
    crud.create_history_entry(
        session=session,
        key=cache_key,
        url=None,
        summary=f"Fetched {len(all_publications)} publications",
        source="remote",
    )
    return result

# History endpoints
@router.get("/history", response_model=list[SearchHistory])
def list_search_history(
    current_user: CurrentUser,
    keyword: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    session: Session = Depends(get_db),
):
    return crud.list_history(session=session, keyword=keyword, start_date=start_date, end_date=end_date)

@router.delete("/history/{history_id}")
def delete_history_entry(
    current_user: CurrentUser,
    history_id: str,
    session: Session = Depends(get_db),
):
    crud.delete_history_entry(session=session, history_id=history_id)
    return {"detail": "deleted"}

@router.delete("/history")
def clear_search_history(current_user: CurrentUser, session: Session = Depends(get_db)):
    crud.clear_history(session=session)
    return {"detail": "all cleared"}

@router.get("/history/export")
def export_history(
    current_user: CurrentUser,
    format: str = "json",
    session: Session = Depends(get_db),
):
    data = crud.list_history(session=session)
    if format == "csv":
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "key", "url", "summary", "source", "created_at"])
        for h in data:
            writer.writerow([h.id, h.key, h.url, h.result_summary, h.source, h.created_at])
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=search_history.csv"},
        )
    else:
        return data



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
