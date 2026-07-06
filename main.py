from urllib.parse import urljoin
import os

import requests
import pandas as pd
from bs4 import BeautifulSoup


BASE_URL = "https://books.toscrape.com/"
OUTPUT_FILE = "data/books_data.csv"

rating_map = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}

def get_soup(url):
    response = requests.get(url)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return BeautifulSoup(response.text, "html.parser")


def get_categories():
    soup = get_soup(BASE_URL)

    category_links = soup.select("div.side_categories ul.nav-list ul li a")
    categories = []

    for link in category_links:
        category_name = link.get_text(strip=True)
        category_url = urljoin(BASE_URL, link["href"])

        categories.append({
            "name": category_name,
            "url": category_url,
        })

    return categories


def scrape_category(category_name, category_url):
    books_data = []
    current_url = category_url

    while current_url:
        soup = get_soup(current_url)
        books = soup.select("article.product_pod")

        for book in books:
            title_tag = book.select_one("h3 a")
            image_tag = book.select_one("img.thumbnail")
            rating_tag = book.select_one("p.star-rating")
            price_tag = book.select_one("p.price_color")
            status_tag = book.select_one("p.availability")

            if not title_tag or not image_tag or not rating_tag or not price_tag or not status_tag:
                continue

            book_name = title_tag.get("title", "").strip()
            image_src = image_tag.get("src", "").strip()
            image_url = urljoin(current_url, image_src)

            rating_word = None
            for class_name in rating_tag.get("class", []):
                if class_name in rating_map:
                    rating_word = class_name
                    break

            if rating_word is None:
                continue

            rating = rating_map[rating_word]

            price_text = price_tag.get_text(strip=True)
            price = float(price_text.replace("£", ""))

            status_text = status_tag.get_text(" ", strip=True)
            status = "In stock" in status_text

            books_data.append({
                "image": image_url,
                "book_name": book_name,
                "rating": rating,
                "price": price,
                "status": status,
                "category": category_name,
            })

        next_button = soup.select_one("li.next a")

        if next_button:
            current_url = urljoin(current_url, next_button["href"])
        else:
            current_url = None

    return books_data


def main():
    all_books = []

    categories = get_categories()
    print("Total categories:", len(categories))

    for category in categories:
        print("Scraping:", category["name"])

        category_books = scrape_category(
            category["name"],
            category["url"]
        )

        all_books.extend(category_books)

    df = pd.DataFrame(all_books)

    df.insert(0, "id", range(1, len(df) + 1))

    os.makedirs("data", exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("Scraping finished.")
    print("Total books:", len(df))
    print("Saved file:", OUTPUT_FILE)


if __name__ == "__main__":
    main()