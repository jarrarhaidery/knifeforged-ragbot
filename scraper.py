# scraper.py
import requests
from bs4 import BeautifulSoup
import json
import os
from urllib.parse import urljoin
from config import WP_SITE

OUT_DIR = "data"
OUT_FILE = os.path.join(OUT_DIR, "products.json")
os.makedirs(OUT_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; RAGScraper/1.0; +https://example.com)"
}

def try_rest_api(base_url):
    """
    Try to retrieve products using common WordPress/WooCommerce REST endpoints.
    Many WooCommerce installs require authentication — this tries public endpoints first.
    """
    candidates = [
        "/wp-json/wc/v3/products",    # WooCommerce v3 (often requires auth)
        "/wp-json/wp/v2/product",     # custom product post type (public)
        "/wp-json/wp/v2/posts",       # fallback: some shops store products as posts
        "/?rest_route=/wp/v2/pages"   # generic example (not product-specific)
    ]
    collected = []
    for path in candidates:
        url = urljoin(base_url, path)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    # Heuristic: find objects containing title, content, link, price keys
                    for item in data:
                        title = item.get("name") or (item.get("title") and (item["title"].get("rendered") if isinstance(item["title"], dict) else item["title"]))
                        if not title:
                            continue
                        desc = item.get("description") or item.get("content", {}).get("rendered") or item.get("excerpt", {}).get("rendered", "")
                        price = item.get("price") or item.get("meta", {}).get("price")
                        images = []
                        if item.get("images"):
                            for im in item["images"]:
                                if isinstance(im, dict):
                                    images.append(im.get("src") or im.get("url"))
                        link = item.get("permalink") or item.get("link")
                        categories = []
                        if item.get("categories"):
                            for c in item["categories"]:
                                if isinstance(c, dict):
                                    categories.append(c.get("name"))
                        availability = item.get("stock_status") or item.get("status")
                        collected.append({
                            "title": title,
                            "description": desc,
                            "price": price,
                            "categories": categories,
                            "images": images,
                            "availability": availability,
                            "product_url": link
                        })
                    if collected:
                        print(f"[rest] got {len(collected)} items from {url}")
                        return collected
                except Exception:
                    continue
        except Exception:
            continue
    return []

def html_scrape(base_url, max_pages=5):
    """
    Basic HTML scraper: looks for elements commonly used in WooCommerce themes.
    This is heuristic; adjust selectors for your theme.
    """
    collected = []
    try:
        resp = requests.get(base_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print("Error fetching base URL:", e)
        return collected

    soup = BeautifulSoup(resp.text, "html.parser")
    # Candidate product links: elements with class 'product' or 'woocommerce-product' or 'product-item'
    anchors = set()
    for a in soup.select("a"):
        href = a.get("href")
        if not href:
            continue
        # heuristics: product pages often contain '/product/' in URL
        if "/product/" in href or "product" in a.get("class", []) or "product" in (a.get("href") or ""):
            anchors.add(urljoin(base_url, href))

    # If none found, fallback to all links on homepage
    if not anchors:
        anchors = set(urljoin(base_url, a.get("href")) for a in soup.find_all("a", href=True))

    # Visit unique anchors and try to extract product info
    count = 0
    for link in list(anchors)[:300]:  # cap number of pages visited
        if count >= max_pages * 20:
            break
        try:
            r = requests.get(link, headers=HEADERS, timeout=12)
            if r.status_code != 200:
                continue
            sp = BeautifulSoup(r.text, "html.parser")
            # heuristics for title/price/description
            title = sp.select_one(".product_title") or sp.select_one("h1") or sp.select_one(".entry-title")
            price_el = sp.select_one(".price") or sp.select_one(".woocommerce-Price-amount") or sp.find(text=lambda t: t and "PKR" in t or "Rs" in t or "Rs." in t)
            desc_el = sp.select_one(".woocommerce-product-details__short-description") or sp.select_one(".product_description") or sp.select_one(".entry-content")
            imgs = []
            for im in sp.select("img"):
                src = im.get("src") or im.get("data-src")
                if src and ("/uploads/" in src or "product" in src or src.startswith("http")):
                    imgs.append(urljoin(link, src))
            availability = None
            stock = sp.select_one(".stock") or sp.find(text=lambda t: t and "In stock" in t or "Out of stock" in t)
            if stock:
                availability = stock.get_text(strip=True) if hasattr(stock, "get_text") else str(stock)

            product_data = {
                "title": title.get_text(strip=True) if title else None,
                "description": desc_el.get_text(strip=True) if desc_el else None,
                "price": price_el.get_text(strip=True) if price_el and hasattr(price_el, "get_text") else (price_el if isinstance(price_el, str) else None),
                "categories": [c.get_text(strip=True) for c in sp.select(".posted_in a")] or [],
                "images": imgs,
                "availability": availability,
                "product_url": link
            }
            if product_data["title"] and (product_data["description"] or product_data["price"] or product_data["images"]):
                collected.append(product_data)
                count += 1
                print(f"[html] scraped {product_data['title']}")
        except Exception:
            continue
    return collected

def main():
    print("Starting scraping for:", WP_SITE)
    items = try_rest_api(WP_SITE)
    if not items:
        print("REST API didn't yield product results or required auth — falling back to HTML scraping.")
        items = html_scrape(WP_SITE, max_pages=8)

    # sanitize and export
    cleaned = []
    for p in items:
        if not p.get("title"):
            continue
        cleaned.append({
            "title": p.get("title"),
            "description": p.get("description") or "",
            "price": p.get("price") or "",
            "categories": p.get("categories") or [],
            "images": p.get("images") or [],
            "availability": p.get("availability") or "",
            "product_url": p.get("product_url") or ""
        })

    print(f"Found {len(cleaned)} products. Saving to {OUT_FILE}")
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
