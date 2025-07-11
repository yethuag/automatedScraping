from bs4 import BeautifulSoup
import requests
import json

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"
}

def get_product_links(query, page=1):
    search_url = f"https://www.walmart.com/search/?query={query}&page={page}"
    response = requests.get(search_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a", href=True)
    product_links = []
    seen = set()

    for link in links:
        href = link["href"]
        if "/ip/" in href:
            if "https" in href:
                full_url = href
            else:
                full_url = "https://www.walmart.com" + href
            if full_url not in seen:
                product_links.append(full_url)
                seen.add(full_url)

    return product_links

def extract_product_info(url):
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if not script_tag:
        return None

    data = json.loads(script_tag.string)
    product_data = None

    try:
        product_data = data["props"]["pageProps"]["initialData"]["data"]["product"]
    except KeyError:
        try:
            product_data = data["props"]["pageProps"]["product"]
        except KeyError:
            return None

    price_info = product_data.get("priceInfo", {}).get("currentPrice", {})
    reviews_data = product_data.get("reviews", {})

    product_info = {
        "price": price_info.get("price", None),
        "review_count": reviews_data.get("totalReviewCount", 0),
        "item_id": product_data.get("usItemId", ""),
        "avg_rating": reviews_data.get("averageOverallRating", 0),
        "product_name": product_data.get("name", ""),
        "brand": product_data.get("brand", ""),
        "availability": product_data.get("availabilityStatus", ""),
        "image_url": product_data.get("imageInfo", {}).get("thumbnailUrl", ""),
        "short_description": product_data.get("shortDescription", "")
    }

    return product_info

def main():
    OUTPUT_FILE = "walmart_products.json"

    page_number = 1
    with open(OUTPUT_FILE, "w") as file:
        while page_number <= 99:
            links = get_product_links("computers", page_number)
            if not links:
                print("No products found on page", page_number)
                break
            for link in links:
                try:
                    info = extract_product_info(link)
                    if info:
                        file.write(json.dumps(info) + "\n")
                except Exception as e:
                    print(f"Error extracting info from {link}: {e}")
            print(f"Search page {page_number} completed.")
            page_number += 1

if __name__ == "__main__":
    main()
