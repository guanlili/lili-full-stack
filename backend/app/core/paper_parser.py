import re
import json
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from app.models import PaperDetail

class PaperParser:
    @staticmethod
    async def fetch_url(url: str) -> tuple[str, str]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            
            content_type = resp.headers.get("content-type", "").lower()
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                raise ValueError(f"Non-HTML content type: {content_type}")
                
            return resp.text, content_type

    @staticmethod
    def extract_meta_tags(soup: BeautifulSoup) -> dict:
        metadata = {}
        
        # Dublin Core
        for tag in soup.find_all("meta", attrs={"name": re.compile(r"^DC\.", re.I)}):
            name = tag.get("name", "").lower()
            content = tag.get("content")
            if content:
                if name not in metadata:
                    metadata[name] = []
                metadata[name].append(content)
        
        # Highwire Press (citation_*)
        for tag in soup.find_all("meta", attrs={"name": re.compile(r"^citation_", re.I)}):
            name = tag.get("name", "").lower()
            content = tag.get("content")
            if content:
                if name not in metadata:
                    metadata[name] = []
                metadata[name].append(content)

        # OpenGraph
        for tag in soup.find_all("meta", attrs={"property": re.compile(r"^og:", re.I)}):
            name = tag.get("property", "").lower()
            content = tag.get("content")
            if content:
                metadata[name] = content

        return metadata

    @staticmethod
    def extract_json_ld(soup: BeautifulSoup) -> list:
        json_ld_data = []
        for tag in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(tag.string)
                if isinstance(data, list):
                    json_ld_data.extend(data)
                else:
                    json_ld_data.append(data)
            except (ValueError, TypeError):
                continue
        return json_ld_data

    @staticmethod
    def extract_ieee_metadata(html: str) -> dict | None:
        """
        Extract metadata from IEEE Xplore global JavaScript object.
        Pattern: xplGlobal.document.metadata = { ... };
        """
        try:
            # Look for the metadata object definition
            # We use a non-greedy wildcard to capture the object content
            match = re.search(r"xplGlobal\.document\.metadata\s*=\s*(\{.*?\});", html, re.DOTALL)
            if match:
                json_str = match.group(1)
                # The JS object might not be valid JSON (keys not quoted sometimes).
                # But IEEE usually sends valid JSON in this block.
                # If keys are unquoted, we might need a more robust parser or regex fix.
                # Let's try standard JSON load first, if it fails, try a simple regex extraction for known keys.
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    # Fallback: Extract specific fields with regex from the JS string
                    metadata = {}
                    
                    def extract_field(key, source):
                        m = re.search(rf'"{key}"\s*:\s*"(.*?)"', source)
                        return m.group(1) if m else None

                    metadata["title"] = extract_field("title", json_str)
                    metadata["doi"] = extract_field("doi", json_str)
                    metadata["publicationTitle"] = extract_field("publicationTitle", json_str)
                    
                    # Authors is an array, harder to regex. 
                    # Try to match the whole authors array string
                    authors_match = re.search(r'"authors"\s*:\s*(\[.*?\])', json_str, re.DOTALL)
                    if authors_match:
                        try:
                            metadata["authors"] = json.loads(authors_match.group(1))
                        except: pass
                        
                    return metadata
        except Exception:
            pass
        return None

    @classmethod
    async def parse_paper(cls, url: str) -> PaperDetail:
        # Pre-processing for specific sites
        # IJCAI: PDF links (ijcai.org/.../0585.pdf) -> HTML Abstract (ijcai.org/.../0585)
        if "ijcai.org" in url and url.endswith(".pdf"):
            url = url[:-4]
            
        html, _ = await cls.fetch_url(url)
        soup = BeautifulSoup(html, "html.parser")
        
        meta = cls.extract_meta_tags(soup)
        json_ld = cls.extract_json_ld(soup)
        ieee_data = cls.extract_ieee_metadata(html)
        
        # Flatten meta for easier access
        def get_meta(keys):
            for k in keys:
                if k in meta:
                    val = meta[k]
                    return val[0] if isinstance(val, list) else val
            return None

        def get_meta_list(keys):
            for k in keys:
                if k in meta:
                    val = meta[k]
                    return val if isinstance(val, list) else [val]
            return []

        # Try to extract fields with priorities
        title = get_meta(["citation_title", "dc.title", "og:title"]) or soup.title.string.strip() if soup.title else "Unknown Title"
        authors = get_meta_list(["citation_author", "dc.creator"])
        pub_date = get_meta(["citation_publication_date", "citation_date", "dc.date"])
        venue = get_meta(["citation_journal_title", "citation_conference_title", "dc.relation.ispartof", "og:site_name"])
        doi = get_meta(["citation_doi", "dc.identifier", "dc.identifier.doi"])
        
        # Fallback to JSON-LD for SchorlarlyArticle
        for data in json_ld:
            if data.get("@type") in ["ScholarlyArticle", "Article", "TechArticle"]:
                title = title or data.get("headline") or data.get("name")
                if not authors and data.get("author"):
                    author_data = data.get("author")
                    if isinstance(author_data, list):
                        authors = [a.get("name") for a in author_data if isinstance(a, dict) and a.get("name")]
                    elif isinstance(author_data, dict):
                        authors = [author_data.get("name")]
                pub_date = pub_date or data.get("datePublished")
                venue = venue or (data.get("isPartOf", {}).get("name") if isinstance(data.get("isPartOf"), dict) else None)
                break
        
        # Fallback to IEEE xplGlobal
        if ieee_data:
            title = title or ieee_data.get("title")
            venue = venue or ieee_data.get("publicationTitle")
            doi = doi or ieee_data.get("doi")
            if not authors and ieee_data.get("authors"):
                authors = [a.get("name") for a in ieee_data.get("authors") if a.get("name")]
            # Try to get date
            pub_date = pub_date or ieee_data.get("displayPublicationDate") or ieee_data.get("publicationDate")

        # Extract abstract
        abstract = get_meta(["citation_abstract", "dc.description", "og:description"])
        if not abstract and ieee_data:
             abstract = ieee_data.get("abstract")

        if not abstract:
            # Common abstract ID/classes
            abs_tag = soup.find(id=re.compile(r"abstract|summary", re.I)) or \
                      soup.find(class_=re.compile(r"abstract|summary", re.I))
            if abs_tag:
                abstract = abs_tag.get_text(strip=True)

        source_site = urlparse(url).netloc

        return PaperDetail(
            title=title,
            authors=authors,
            publication_date=pub_date,
            venue=venue,
            doi=doi,
            source_site=source_site,
            url=url,
            abstract=abstract
        )
