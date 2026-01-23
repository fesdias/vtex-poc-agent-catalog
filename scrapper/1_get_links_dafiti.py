import re
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_CATEGORIES = [
    "https://www.dafiti.com.br/calcados-femininos/",
    "https://www.dafiti.com.br/roupas-femininas/",
    "https://www.dafiti.com.br/bolsas-e-acessorios-femininos/",
    "https://www.dafiti.com.br/roupas-masculinas/",
    "https://www.dafiti.com.br/calcados-masculinos/",
    "https://www.dafiti.com.br/bolsas-e-acessorios-masculinos/",
    "https://www.dafiti.com.br/moda-esportiva/",
    "https://www.dafiti.com.br/calcados-esportivos/",
]

OUTPUT_FILE = "produtos_link.csv"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
}

# URLs de produto típicas: ...-14524299.html
PRODUCT_RE = re.compile(r"https?://www\.dafiti\.com\.br/[A-Za-z0-9\-\_/]+-\d{5,}\.html$")

def build_session():
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

def extract_product_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")

    # 1) âncoras normais
    hrefs = [a.get("href") for a in soup.find_all("a", href=True)]

    # 2) imagens com data-href (às vezes o card usa wrapper com JS)
    hrefs += [img.get("data-href") for img in soup.find_all("img") if img.get("data-href")]

    # normaliza e filtra
    norm = []
    for h in hrefs:
        if not h:
            continue
        if h.startswith("//"):
            h = "https:" + h
        elif h.startswith("/"):
            h = urljoin(base_url, h)
        # remove anchors e params de tracking
        h = h.split("#")[0].split("?")[0]
        norm.append(h)

    # mantêm só padrões ...-123456.html no domínio da Dafiti
    out = [u for u in norm if PRODUCT_RE.match(u)]
    # remove duplicados preservando ordem
    seen, unique = set(), []
    for u in out:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique

def crawl_category(session, category_url, max_pages=20, sleep_sec=1.2):
    found = []
    last_count = -1
    for page in range(1, max_pages + 1):
        url = f"{category_url}?page={page}"
        print(f"   → Página {page}: {url}")
        r = session.get(url, timeout=25, headers={"Referer": category_url})
        if r.status_code != 200:
            print(f"     (status {r.status_code}) encerrando categoria.")
            break

        links = extract_product_links(r.text, category_url)
        print(f"     {len(links)} links candidatos nesta página.")
        # se não trouxe links, paramos (fim da paginação real)
        if len(links) == 0:
            print("     Nenhum produto encontrado, encerrando categoria.")
            break

        # agrega, evitando duplicatas globais
        for u in links:
            if u not in found:
                found.append(u)

        # heurística: se não cresce por 2 páginas seguidas, para
        if len(found) == last_count:
            print("     Sem novos produtos em relação à página anterior; encerrando.")
            break
        last_count = len(found)

        time.sleep(sleep_sec)
    return found

def main():
    session = build_session()
    all_links = []

    for cat in BASE_CATEGORIES:
        print(f"\n📂 Extraindo categoria: {cat}")
        links = crawl_category(session, cat)
        print(f"   → {len(links)} produtos coletados nesta categoria.")
        all_links.extend(links)

    # dedup global preservando ordem
    seen, uniq = set(), []
    for u in all_links:
        if u not in seen:
            seen.add(u)
            uniq.append(u)

    print(f"\n✅ Total de produtos únicos: {len(uniq)}")
    pd.DataFrame(uniq, columns=["link"]).to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"💾 Links salvos em: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
