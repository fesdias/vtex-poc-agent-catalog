import requests
from bs4 import BeautifulSoup
import pandas as pd
import os

# === CONFIGURAÇÕES ===
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

OUTPUT_FILE = os.path.expanduser("~/Downloads/arvore_categorias_dafiti.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}

def get_subcategories(url, departamento):
    """Extrai categorias e subcategorias a partir do menu lateral de uma categoria raiz"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        if r.status_code != 200:
            print(f"⚠️ Erro {r.status_code} ao acessar {url}")
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        subcats = []

        # blocos comuns de menu lateral
        sidebar = soup.find("aside") or soup.find("nav") or soup.find("div", class_="sidebar")
        if not sidebar:
            print(f"⚠️ Menu lateral não encontrado em {url}")
            return []

        for a in sidebar.select("a[href]"):
            name = a.get_text(strip=True)
            href = a.get("href")
            if not name or not href:
                continue

            # normaliza URL
            if href.startswith("/"):
                href = "https://www.dafiti.com.br" + href

            # evita duplicatas e URLs irrelevantes
            if any(x in href for x in ["promo", "sale", "novo", "marca", "tamanho", "?page"]):
                continue

            # obtém categoria e subcategoria a partir da estrutura da URL
            path = href.replace("https://www.dafiti.com.br/", "").strip("/").split("/")
            categoria = path[0] if len(path) > 0 else ""
            subcategoria = path[1] if len(path) > 1 else ""

            subcats.append({
                "Departamento": departamento,
                "Categoria": categoria.replace("-", " ").title(),
                "Subcategoria": subcategoria.replace("-", " ").title() if subcategoria else "",
                "URL": href
            })

        return subcats

    except Exception as e:
        print(f"Erro em {url}: {e}")
        return []

def main():
    all_rows = []

    for url in BASE_CATEGORIES:
        print(f"\n📂 Extraindo categorias de: {url}")
        departamento = url.split("/")[-2].replace("-", " ").title()
        rows = get_subcategories(url, departamento)
        print(f"   → {len(rows)} subcategorias encontradas.")
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows).drop_duplicates(subset=["URL"])
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print(f"\n✅ Árvore de categorias salva em: {OUTPUT_FILE}")
    print(f"📊 Total de linhas: {len(df)}")

if __name__ == "__main__":
    main()
