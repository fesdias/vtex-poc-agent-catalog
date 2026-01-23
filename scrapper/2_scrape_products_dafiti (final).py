import os
import re
import json
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# === CONFIG ===
INPUT_FILE = os.path.expanduser("~/Downloads/produtos_link1.csv")
OUTPUT_FILE = os.path.expanduser("~/Downloads/catalogo_dafiti.csv")
IMAGES_DIR = os.path.expanduser("~/Downloads/dafiti_imagens")
os.makedirs(IMAGES_DIR, exist_ok=True)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT}

def clean_text(t):
    return re.sub(r"\s+", " ", t or "").strip()

def parse_jsonld(soup):
    """Coleta objetos JSON-LD úteis (Product)."""
    out = []
    for s in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(s.string or "")
            if isinstance(data, dict):
                out.append(data)
            elif isinstance(data, list):
                out.extend([d for d in data if isinstance(d, dict)])
        except Exception:
            continue
    # filtra Product
    products = [d for d in out if d.get("@type") in ("Product", ["Product"], "schema:Product")]
    return products

def pick_brand(soup, jsonld_products):
    # 1) seletor direto mais comum no HTML
    el = soup.select_one("a.brand-name, span.brand-name, .product-brand a, .product-brand span, [data-testid='brand-name']")
    if el and el.get_text(strip=True):
        return clean_text(el.get_text())

    # 2) meta tags que algumas páginas usam
    for name_attr in ["productBrand", "og:brand", "twitter:data2", "twitter:label2"]:
        mt = soup.find("meta", {"name": name_attr}) or soup.find("meta", {"property": name_attr})
        if mt and mt.get("content"):
            return clean_text(mt["content"])

    # 3) JSON-LD: procurar 'brand' em qualquer nível
    def search_brand(obj):
        if isinstance(obj, dict):
            if "brand" in obj:
                b = obj["brand"]
                if isinstance(b, dict) and b.get("name"):
                    return clean_text(b["name"])
                if isinstance(b, str):
                    return clean_text(b)
            # percorre recursivamente
            for v in obj.values():
                res = search_brand(v)
                if res:
                    return res
        elif isinstance(obj, list):
            for v in obj:
                res = search_brand(v)
                if res:
                    return res
        return None

    for p in jsonld_products:
        res = search_brand(p)
        if res:
            return res

    # 4) fallback leve: tenta extrair do título (mantém só a “palavra de marca”, sem impacto em outras partes)
    ogt = soup.find("meta", {"property": "og:title"})
    if ogt and ogt.get("content"):
        title = ogt["content"].strip()
        # heurística: pega token que antecede um tipo de produto comum (Bolsa, Tênis, Camiseta etc.)
        tokens = re.split(r"\s+", title)
        if len(tokens) >= 2:
            # exemplo: "Tênis Slip On Santa Lolla Suede Preto" -> pega "Santa Lolla"
            # procura um bloco de 1-3 palavras com letras maiúsculas seguidas
            m = re.search(r"([A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁÉÍÓÚÂÊÔÃÕÇ\-]+(?:\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][\wÁÉÍÓÚÂÊÔÃÕÇ\-]+){0,2})", title)
            if m:
                return clean_text(m.group(1))

    return ""

def pick_description(soup, jsonld_products):
    # 1) HTML
    for sel in ["div[itemprop='description']", "section.product-description"]:
        el = soup.select_one(sel)
        if el:
            return clean_text(el.get_text(" "))
    # 2) og:description
    ogd = soup.find("meta", {"property": "og:description"})
    if ogd and ogd.get("content"):
        return clean_text(ogd["content"])
    # 3) JSON-LD
    for p in jsonld_products:
        desc = p.get("description")
        if desc:
            return clean_text(desc)
    return ""

def pick_price(soup):
    # PRIORIDADE: o trecho que você disse que funcionava
    preco_tag = soup.find("span", {"class": "catalog-detail-price-value"})
    if not preco_tag:
        preco_tag = soup.find("span", {"itemprop": "price"})
    preco = ""
    if preco_tag:
        preco = re.sub(r"[^\d,]", "", preco_tag.get_text(strip=True)).replace(",", ".")
    if not preco:
        preco_meta = soup.find("meta", {"itemprop": "price"})
        if preco_meta and preco_meta.get("content"):
            preco = preco_meta["content"]
    # fallbacks adicionais
    if not preco:
        meta_prop = soup.find("meta", {"property": "product:price:amount"})
        if meta_prop and meta_prop.get("content"):
            preco = meta_prop["content"]
    return preco

def parse_breadcrumbs(soup):
    """
    Retorna (departamento, categoria, subcategoria).
    1) Tenta <ul itemtype="https://schema.org/BreadcrumbList"> (server-side legado)
    2) Tenta <ol class="flex ... items-center"> (client-side novo)
    3) Tenta JSON-LD @type="BreadcrumbList"
    Remove 'Início' e limita a 3 níveis: dep=links[0], cat=links[1], sub=links[2]/[-1].
    """
    def _clean(items):
        out = []
        for t in items:
            t = re.sub(r"\s+", " ", t or "").strip()
            if t and not re.match(r"^in[ií]cio$", t, flags=re.I):
                out.append(t)
        return out

    # --- 1) LEGADO server-side: <ul itemtype="https://schema.org/BreadcrumbList">
    ul = soup.find("ul", attrs={"itemtype": "https://schema.org/BreadcrumbList"})
    if ul:
        names = []
        for li in ul.find_all("li"):
            # preferir <span itemprop="name">
            name_el = li.find(attrs={"itemprop": "name"})
            if name_el and name_el.get_text(strip=True):
                names.append(name_el.get_text(strip=True))
            else:
                a = li.find("a")
                if a and a.get_text(strip=True):
                    names.append(a.get_text(strip=True))
        names = _clean(names)
        if names:
            if len(names) >= 3:
                return names[0], names[1], names[-1]
            if len(names) == 2:
                return names[0], names[1], ""
            if len(names) == 1:
                return names[0], "", ""

    # --- 2) NOVO client-side: <ol class="flex ... items-center">
    ol = soup.select_one("ol.flex.items-center") or soup.select_one("ol.flex.flex-wrap")
    if not ol:
        # ainda mais permissivo: qualquer <ol> que tenha o separador do breadcrumb
        ol = soup.select_one("ol:has([data-testid='breadcrumb-separator'])")
    if ol:
        names = [a.get_text(strip=True) for a in ol.select("a[href]")]
        names = _clean(names)
        if names:
            if len(names) >= 3:
                return names[0], names[1], names[-1]
            if len(names) == 2:
                return names[0], names[1], ""
            if len(names) == 1:
                return names[0], "", ""

    # --- 3) JSON-LD @type BreadcrumbList (fallback)
    try:
        for s in soup.find_all("script", type=lambda v: v and "ld+json" in v):
            txt = (s.string or s.get_text(strip=True) or "").strip()
            if not txt:
                continue
            data = json.loads(txt)
            nodes = data if isinstance(data, list) else [data]
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                graphs = [node]
                if isinstance(node.get("@graph"), list):
                    graphs += [g for g in node["@graph"] if isinstance(g, dict)]
                for g in graphs:
                    if g.get("@type") == "BreadcrumbList" and isinstance(g.get("itemListElement"), list):
                        names = []
                        for it in g["itemListElement"]:
                            name = None
                            if isinstance(it, dict):
                                if isinstance(it.get("item"), dict) and it["item"].get("name"):
                                    name = it["item"]["name"]
                                elif isinstance(it.get("name"), str):
                                    name = it["name"]
                                elif it.get("@type") == "ListItem" and isinstance(it.get("item"), dict):
                                    name = it["item"].get("name")
                            if name:
                                names.append(name.strip())
                        names = _clean(names)
                        if names:
                            if len(names) >= 3:
                                return names[0], names[1], names[-1]
                            if len(names) == 2:
                                return names[0], names[1], ""
                            if len(names) == 1:
                                return names[0], "", ""
    except Exception:
        pass

    return "", "", ""

def pick_variations(soup, jsonld_products):
    vals = set()
    # 1) Botões de tamanho
    for el in soup.select("ul[data-testid='size-selector'] li button"):
        txt = clean_text(el.get_text())
        if txt and not txt.lower().startswith("selecione"):
            vals.add(txt)
    # 2) Select de tamanho
    for el in soup.select("select[name*='size'] option"):
        txt = clean_text(el.get_text())
        if txt and not txt.lower().startswith("selecione"):
            vals.add(txt)
    # 3) Labels/inputs comuns
    for el in soup.select("fieldset[name*='size'] label, fieldset[id*='size'] label, div[class*='size'] label"):
        txt = clean_text(el.get_text())
        if txt:
            vals.add(txt)
    # 4) JSON-LD (às vezes traz atributos/sku)
    for p in jsonld_products:
        # Algumas lojas colocam variações dentro de offers/sku
        offers = p.get("offers")
        if isinstance(offers, dict):
            sz = offers.get("size") or offers.get("sku")
            if isinstance(sz, str):
                vals.add(clean_text(sz))
            elif isinstance(sz, list):
                for v in sz:
                    if isinstance(v, str):
                        vals.add(clean_text(v))
        # Às vezes aparece "additionalProperty"
        props = p.get("additionalProperty") or p.get("additionalProperties")
        if isinstance(props, list):
            for prop in props:
                if isinstance(prop, dict) and prop.get("name") and prop.get("value"):
                    n = prop["name"].lower()
                    v = clean_text(prop["value"])
                    if any(k in n for k in ["tamanho", "size", "cor", "color"]) and v:
                        vals.add(v)
    # Limpeza básica (excluir valores genéricos)
    vals = {v for v in vals if v and v.lower() not in {"único", "unico", "tamanho único"}}
    return ", ".join(sorted(vals, key=lambda x: (len(x), x)))

def pick_images(soup, jsonld_products=None):
    """
    Coleta TODAS as imagens de produto na Dafiti:
    - preview (data-testid=image-gallery-preview)
    - thumbnails (data-testid=image-gallery-thumbnail)
    - <picture><source srcset=...>
    - img[data-src], img[srcset]
    - meta og:image
    Além disso, se achar "-1-product.jpg", tenta montar "-2-feed.jpg", "-3-feed.jpg" etc.
    Retorna até 8 URLs normalizadas (sem querystring), na ordem correta.
    """
    urls = []

    def _add(u):
        if not u:
            return
        if u.startswith("//"):
            u = "https:" + u
        u = u.split("?")[0]
        if "static.dafiti.com.br" in u and any(tag in u for tag in ["-product", "-feed", "-zoom"]):
            urls.append(u)

    # 1) preview principal (+ srcset)
    for img in soup.select("img[data-testid='image-gallery-preview']"):
        _add(img.get("src"))
        if img.has_attr("srcset"):
            for part in img["srcset"].split(","):
                _add(part.strip().split(" ")[0])

    # 2) thumbnails
    for img in soup.select("img[data-testid='image-gallery-thumbnail']"):
        _add(img.get("src"))
        if img.has_attr("srcset"):
            for part in img["srcset"].split(","):
                _add(part.strip().split(" ")[0])

    # 3) picture/source (srcset em <source>)
    for src in soup.select("picture source[srcset]"):
        for part in src["srcset"].split(","):
            _add(part.strip().split(" ")[0])

    # 4) lazy: img[data-src], img[srcset]
    for img in soup.find_all("img"):
        _add(img.get("data-src"))
        if img.has_attr("srcset"):
            for part in img["srcset"].split(","):
                _add(part.strip().split(" ")[0])
        _add(img.get("src"))

    # 5) metas og:image
    for m in soup.find_all("meta", {"property": "og:image"}):
        _add(m.get("content"))

    # normaliza, mantém ordem, remove duplicatas
    seen, final = set(), []
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            final.append(u)

    # 6) heurística: se há -1-product.jpg, tentar -2..-8 feed/zoom
    # ex.: ...-1-product.jpg -> ...-2-feed.jpg, ...-3-feed.jpg
    expanded = []
    base_first = None
    for u in final:
        expanded.append(u)
        m = re.search(r"-(\d+)-(product|zoom)\.jpg$", u)
        if m:
            base_first = u
            num = int(m.group(1))
            # tenta gerar até mais 7 imagens além da principal
            for i in range(num + 1, num + 8):
                for kind in ("feed", "zoom", "product"):
                    candidate = re.sub(r"-(\d+)-(product|zoom)\.jpg$",
                                       f"-{i}-{kind}.jpg",
                                       u)
                    if candidate not in expanded:
                        expanded.append(candidate)
            # não precisa repetir para todas; usar a primeira como base já cobre a sequência
            break

    final = expanded if base_first else final

    # limita pra evitar excesso (ajuste se quiser)
    return final[:3]

def baixar_imagem(url, sku, idx):
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        if r.status_code == 200:
            fname = f"{sku}_{idx}.jpg"
            path = os.path.join(IMAGES_DIR, fname)
            with open(path, "wb") as f:
                f.write(r.content)
            print(f"     ✅ Imagem salva: {fname}")
        else:
            print(f"     ⚠️ Falha {r.status_code} ao baixar {url}")
    except Exception as e:
        print(f"     ⚠️ Erro ao baixar {url}: {e}")

def extrair_produto(url):
    r = requests.get(url, headers=HEADERS, timeout=35)
    if r.status_code != 200:
        print(f"⚠️ HTTP {r.status_code} em {url}")
        return None
    open("/Users/elisa.bettega/Downloads/debug_breadcrumb.html","w").write(r.text)

    soup = BeautifulSoup(r.text, "html.parser")
    # IDs e slug
    m = re.search(r"(\d{5,})\.html", url)
    produto_id = m.group(1) if m else ""
    sku = produto_id
    slug = url.split("/")[-1].replace(".html", "")

    # JSON-LD
    jsonld = parse_jsonld(soup)

    # Nome
    nome_el = soup.select_one("h1[itemprop='name'], h1.product-name, h1")
    nome = clean_text(nome_el.get_text()) if nome_el else ""

    # Marca
    marca = pick_brand(soup, jsonld)

    # Preço
    preco = pick_price(soup)

    # Descrição
    descricao = pick_description(soup, jsonld)

       # === Breadcrumb ===
    departamento, categoria, subcategoria = parse_breadcrumbs(soup)


    # Variações
    variacao = pick_variations(soup, jsonld)

    # Imagens (todas)
    imagens = pick_images(soup, jsonld)
    print(f"   DEBUG imagens encontradas: {len(imagens)}")
    for k,u in enumerate(imagens[:5],1):
        print(f"     {k}: {u}")
    for i, img in enumerate(imagens, 1):
        baixar_imagem(img, sku, i)

    return {
        "_IDSKU": sku,
        "_NomeSKU": "",
        "_AtivarSKUSePossível": "SIM",
        "_SKUAtivo (Não alterável)": "SIM",
        "_EANSKU": "",
        "_Altura": "", "_AlturaReal": "",
        "_Largura": "", "_LarguraReal": "",
        "_Comprimento": "", "_ComprimentoReal": "",
        "_Peso": "", "_PesoReal": "",
        "_UnidadeMedida": "un",
        "_MultiplicadorUnidade": "1,000000",
        "_CodigoReferenciaSKU": sku,
        "_ValorFidelidade": "",
        "_DataPrevisaoChegada": "",
        "_CodigoFabricante": "",
        "_IDProduto": produto_id,
        "_NomeProduto": nome,
        "_BreveDescricaoProduto": descricao[:200],
        "_ProdutoAtivo (Não alterável)": "SIM",
        "_CodigoReferenciaProduto": sku,
        "_MostrarNoSite": "SIM",
        "_LinkTexto (Não alterável)": slug,
        "_DescricaoProduto": descricao,
        "_DataLancamentoProduto": datetime.today().strftime("%d/%m/%Y"),
        "_PalavrasChave": "",
        "_TituloSite": nome,
        "_DescricaoMetaTag": descricao[:160],
        "_IDFornecedor": "",
        "_MostrarSemEstoque": "SIM",
        "_Kit (Não alterável)": "",
        "_IDDepartamento (Não alterável)": "",
        "_NomeDepartamento": departamento,
        "_IDCategoria": "",
        "_NomeCategoria": categoria,
        "_NomeSubcategoria": subcategoria,
        "_IDMarca": "",
        "_Marca": marca,
        "_PesoCubico": "",
        "_Preço": preco,
        "_Variacao": variacao,
    }

def main():
    df = pd.read_csv(INPUT_FILE)
    cols = [c.lower() for c in df.columns]
    if "link" in cols:
        col_link = df.columns[cols.index("link")]
    elif "url" in cols:
        col_link = df.columns[cols.index("url")]
    else:
        raise ValueError(f"❌ Nenhuma coluna de link encontrada: {df.columns.tolist()}")

    out_rows = []
    for i, row in df.iterrows():
        url = str(row[col_link]).strip()
        if not url.startswith("http"):
            continue
        print(f"\n[{i+1}/{len(df)}] {url}")
        data = extrair_produto(url)
        if data:
            out_rows.append(data)
        time.sleep(1.0)

    pd.DataFrame(out_rows).to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    print(f"\n✅ Catálogo salvo em: {OUTPUT_FILE}")
    print(f"🖼️ Imagens salvas em: {IMAGES_DIR}")

if __name__ == "__main__":
    main()
