"""Sitemap extraction and recursive crawler for finding product URLs."""
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Set
from xml.etree import ElementTree as ET


USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def build_session():
    """Build a requests session with retry logic."""
    s = requests.Session()
    s.headers.update(HEADERS)
    try:
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        retry = Retry(
            total=5,
            backoff_factor=0.8,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD", "OPTIONS"]
        )
        s.mount("https://", HTTPAdapter(max_retries=retry))
        s.mount("http://", HTTPAdapter(max_retries=retry))
    except Exception:
        pass
    return s


def extract_sitemap_urls(base_url: str, session: requests.Session) -> List[str]:
    """
    Try to find and extract URLs from sitemap.xml files.
    
    Returns list of product/page URLs found in sitemaps.
    """
    parsed = urlparse(base_url)
    sitemap_paths = [
        "/sitemap.xml",
        "/sitemap_index.xml",
        "/sitemaps.xml",
        "/robots.txt",  # robots.txt often contains sitemap locations
    ]
    
    all_urls = []
    
    # Try to get sitemap index or main sitemap
    for path in sitemap_paths:
        sitemap_url = f"{parsed.scheme}://{parsed.netloc}{path}"
        try:
            print(f"   🔍 Checking: {sitemap_url}")
            r = session.get(sitemap_url, timeout=15)
            if r.status_code == 200:
                content_type = r.headers.get("content-type", "").lower()
                if "xml" in content_type or path.endswith(".xml"):
                    urls = _parse_sitemap_xml(r.text, session, base_url)
                    all_urls.extend(urls)
                elif "robots.txt" in path:
                    # Extract sitemap URLs from robots.txt
                    sitemap_refs = re.findall(r"Sitemap:\s*(.+)", r.text, re.I)
                    for sitemap_ref in sitemap_refs:
                        urls = _parse_sitemap_xml(session.get(sitemap_ref.strip()).text, session, base_url)
                        all_urls.extend(urls)
                break
        except Exception as e:
            print(f"     ⚠️  Error accessing {sitemap_url}: {e}")
            continue
    
    return list(set(all_urls))  # Deduplicate


def _parse_sitemap_xml(xml_content: str, session: requests.Session, base_url: str) -> List[str]:
    """Parse sitemap XML and extract URLs, handling sitemap indexes."""
    urls = []
    try:
        root = ET.fromstring(xml_content)
        namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        
        # Check if this is a sitemap index
        sitemapindex = root.find("sm:sitemapindex", namespace)
        if sitemapindex is None:
            sitemapindex = root.find("sitemapindex")  # Try without namespace
        
        if sitemapindex is not None:
            # It's a sitemap index, fetch all referenced sitemaps
            for sitemap in sitemapindex.findall("sm:sitemap", namespace) or sitemapindex.findall("sitemap"):
                loc_elem = sitemap.find("sm:loc", namespace) or sitemap.find("loc")
                if loc_elem is not None and loc_elem.text:
                    try:
                        sub_content = session.get(loc_elem.text.strip(), timeout=15).text
                        urls.extend(_parse_sitemap_xml(sub_content, session, base_url))
                    except Exception as e:
                        print(f"     ⚠️  Error fetching sub-sitemap {loc_elem.text}: {e}")
        else:
            # Regular sitemap, extract URLs
            for url_elem in root.findall("sm:url", namespace) or root.findall("url"):
                loc = url_elem.find("sm:loc", namespace) or url_elem.find("loc")
                if loc is not None and loc.text:
                    urls.append(loc.text.strip())
    except ET.ParseError:
        # Fallback: try regex for simple cases
        urls = re.findall(r"<loc>(.+?)</loc>", xml_content)
    
    return urls


def recursive_crawl_pdp_patterns(
    base_url: str,
    session: requests.Session,
    max_pages: int = 100,
    sleep_sec: float = 1.0
) -> List[str]:
    """
    Recursively crawl website to find Product Detail Pages (PDPs).
    
    Looks for common PDP patterns:
    - URLs with product IDs (e.g., .../product-12345.html)
    - URLs in /product/, /p/, /item/ paths
    - Pages with product-specific metadata
    """
    parsed = urlparse(base_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    
    visited: Set[str] = set()
    product_urls: Set[str] = set()
    queue: List[str] = [base_url]
    
    # Common PDP patterns
    pdp_patterns = [
        re.compile(r".*[-\/](p|product|item|prod)[-\/].*", re.I),
        re.compile(r".*[-\/]\d{5,}\.html?$"),  # URLs ending with product ID
        re.compile(r".*/p/[^/]+$"),  # /p/slug pattern
        re.compile(r".*/produto/.*"),  # Portuguese
        re.compile(r".*/product/.*"),  # English
    ]
    
    page_count = 0
    
    while queue and page_count < max_pages:
        current_url = queue.pop(0)
        
        if current_url in visited:
            continue
        
        visited.add(current_url)
        page_count += 1
        
        try:
            print(f"   📄 [{page_count}/{max_pages}] Crawling: {current_url}")
            r = session.get(current_url, timeout=25)
            if r.status_code != 200:
                continue
            
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Check if this looks like a PDP
            if _is_product_page(soup):
                product_urls.add(current_url)
                print(f"     ✅ PDP detected: {current_url}")
            
            # Extract links to crawl
            for a in soup.find_all("a", href=True):
                href = a.get("href")
                if not href:
                    continue
                
                # Normalize URL
                if href.startswith("//"):
                    href = f"{parsed.scheme}:{href}"
                elif href.startswith("/"):
                    href = urljoin(domain, href)
                elif not href.startswith("http"):
                    continue
                
                # Stay within same domain
                if urlparse(href).netloc != parsed.netloc:
                    continue
                
                # Remove fragments and query params for dedup
                clean_href = href.split("#")[0].split("?")[0]
                
                # Check if it matches PDP pattern
                if any(pattern.match(clean_href) for pattern in pdp_patterns):
                    product_urls.add(clean_href)
                    print(f"     ✅ Potential PDP: {clean_href}")
                elif clean_href not in visited and len(queue) < 500:
                    queue.append(clean_href)
            
            time.sleep(sleep_sec)
            
        except Exception as e:
            print(f"     ⚠️  Error crawling {current_url}: {e}")
            continue
    
    return list(product_urls)


def _is_product_page(soup: BeautifulSoup) -> bool:
    """Heuristic to detect if a page is a Product Detail Page."""
    # Check for common product page indicators
    indicators = [
        soup.find("script", type="application/ld+json"),  # JSON-LD Product
        soup.find("meta", {"property": "og:type", "content": re.compile(r"product", re.I)}),
        soup.find("span", {"itemprop": "price"}),
        soup.select_one('[itemtype*="Product"]'),
        soup.select_one('form[action*="cart"], form[action*="add"]'),
        soup.select_one('button[class*="buy"], button[class*="add-to-cart"]'),
    ]
    return any(indicator is not None for indicator in indicators)

