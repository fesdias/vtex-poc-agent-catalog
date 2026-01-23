import os
import re
import csv
import urllib.request
from urllib.parse import urlsplit, urlunsplit, quote
from html.parser import HTMLParser

downloads = os.path.expanduser("~/Downloads")
input_csv = os.path.join(downloads, "produtos_link - catalogo poc.csv")
output_dir = os.path.join(downloads, "imagens_dafiti")
os.makedirs(output_dir, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}


def encode_url(url):
    parts = urlsplit(url)
    path = quote(parts.path)
    return urlunsplit((parts.scheme, parts.netloc, path, parts.query, parts.fragment))


class DafitiParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return

        data = dict(attrs)

        if "class" in data and "gallery-thumb" in data["class"]:
            if "data-img-gallery" in data:
                self.images.append(data["data-img-gallery"])


def baixar(link):
    print("\n🔍 Processando:", link)

    m = re.search(r'(\d+)\.html', link)
    if not m:
        print("❌ SKU não encontrado")
        return

    idsku = m.group(1)

    req = urllib.request.Request(link, headers=HEADERS)
    html = urllib.request.urlopen(req).read().decode("utf-8")

    parser = DafitiParser()
    parser.feed(html)

    print(f"🖼 Encontradas {len(parser.images)} imagens")

    for idx, url in enumerate(parser.images, start=1):
        safe_url = encode_url(url)

        filename = f"{idsku}_{idx}.jpg"
        filepath = os.path.join(output_dir, filename)

        try:
            urllib.request.urlretrieve(safe_url, filepath)
            print(f"   ✔ {filename}")
        except Exception as e:
            print(f"   ❌ Erro ao baixar {safe_url}: {e}")


with open(input_csv, newline='', encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        baixar(row["link"].strip())

print("\n🎉 FINALIZADO COM SUCESSO!")
