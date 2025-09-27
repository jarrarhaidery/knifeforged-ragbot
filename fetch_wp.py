import requests
import json
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Your WooCommerce site + API keys (now from .env)
WC_API_URL = os.getenv("WC_API_URL")  # e.g. "https://bla/wp-json/wc/v3/products"
CONSUMER_KEY = os.getenv("WC_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("WC_CONSUMER_SECRET")

def fetch_all_products():
    page = 1
    products = []

    while True:
        print(f"Fetching page {page}...")
        response = requests.get(
            WC_API_URL,
            params={
                "consumer_key": CONSUMER_KEY,
                "consumer_secret": CONSUMER_SECRET,
                "per_page": 100,  # WooCommerce max per page
                "page": page
            }
        )

        if response.status_code != 200:
            print("Error fetching data:", response.text)
            break

        data = response.json()
        if not data:  # No more products
            break

        products.extend(data)
        page += 1

    return products

def save_products(products, filename="products.json", textfile="products.txt"):
    # Save raw JSON (for future use)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(products, f, indent=2, ensure_ascii=False)

    # Also create a simple text version for embeddings
    with open(textfile, "w", encoding="utf-8") as f:
        for p in products:
            name = p.get("name", "")
            desc = p.get("description", "")
            price = p.get("price", "N/A")
            category = ", ".join([c["name"] for c in p.get("categories", [])])

            f.write(f"Product: {name}\nCategory: {category}\nPrice: {price}\nDescription: {desc}\n\n")

if __name__ == "__main__":
    products = fetch_all_products()
    print(f"Fetched {len(products)} products.")

    save_products(products)
    print("Products saved to products.json and products.txt")
