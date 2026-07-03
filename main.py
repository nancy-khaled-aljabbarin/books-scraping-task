from pathlib import Path
from urllib.parse import urljoin
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_URL = "https://books.toscrape.com/"
EXPECTED_TOTAL_BOOKS = 1000

OUTPUT_DIR = Path("data")
OUTPUT_FILE = OUTPUT_DIR / "books_data.csv"

COLUMNS = ["id", "image", "book_name", "rating", "price", "status", "category"]

RATING_MAP = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
}

SELECTORS = {
    "categories": "div.side_categories ul.nav-list ul li a",
    "book_card": "article.product_pod",
    "title": "h3 a",
    "image": "img.thumbnail",
    "rating": "p.star-rating",
    "price": "p.price_color",
    "status": "p.availability",
    "next_page": "li.next a",
}


def get_soup(url):
    """Fetch page HTML and parse it using BeautifulSoup."""
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return BeautifulSoup(response.text, "html.parser")


def require_one(parent, selector, field_name):
    """Return one HTML element or raise a clear error if selector fails."""
    element = parent.select_one(selector)

    if element is None:
        raise ValueError(f"Missing selector for {field_name}: {selector}")

    return element


def get_categories():
    """Extract all category names and URLs from the sidebar."""
    soup = get_soup(BASE_URL)
    category_links = soup.select(SELECTORS["categories"])

    if not category_links:
        raise ValueError("No categories found. Check category selector.")

    categories = []

    for link in category_links:
        category_name = link.get_text(strip=True)
        category_url = urljoin(BASE_URL, link["href"])

        categories.append({
            "name": category_name,
            "url": category_url,
        })

    return categories


def extract_rating(book):
    """
    Rating is stored in class name.
    Example:
    <p class="star-rating Three"> -> 3
    """
    rating_tag = require_one(book, SELECTORS["rating"], "rating")
    rating_classes = rating_tag.get("class", [])

    rating_word = None

    for class_name in rating_classes:
        if class_name != "star-rating":
            rating_word = class_name
            break

    if rating_word not in RATING_MAP:
        raise ValueError(f"Unknown rating value: {rating_word}")

    return RATING_MAP[rating_word]


def extract_price(book):
    """
    Extract price and convert it to float.
    Example: £51.77 -> 51.77
    """
    price_tag = require_one(book, SELECTORS["price"], "price")
    price_text = price_tag.get_text(strip=True)

    match = re.search(r"\d+\.\d+", price_text)

    if match is None:
        raise ValueError(f"Could not extract price from: {price_text}")

    return float(match.group())


def extract_status(book):
    """
    Convert availability text to Boolean.
    True  = In stock
    False = Not in stock
    """
    status_tag = require_one(book, SELECTORS["status"], "status")
    status_text = status_tag.get_text(" ", strip=True).lower()

    return "in stock" in status_text


def extract_book_data(book, category_name, book_id, current_url):
    """Extract required data from one book card."""
    title_tag = require_one(book, SELECTORS["title"], "book title")
    image_tag = require_one(book, SELECTORS["image"], "book image")

    book_name = title_tag.get("title", "").strip()

    if not book_name:
        raise ValueError("Book title attribute is empty.")

    image_src = image_tag.get("src", "").strip()

    if not image_src:
        raise ValueError("Book image src is empty.")

    image_url = urljoin(current_url, image_src)

    return {
        "id": book_id,
        "image": image_url,
        "book_name": book_name,
        "rating": extract_rating(book),
        "price": extract_price(book),
        "status": extract_status(book),
        "category": category_name,
    }


def scrape_category(category_name, category_url, start_id):
    """Scrape all books from one category, including paginated pages."""
    category_books = []
    current_url = category_url
    book_id = start_id

    while current_url:
        soup = get_soup(current_url)
        books = soup.select(SELECTORS["book_card"])

        if not books:
            raise ValueError(f"No books found in category: {category_name}")

        for book in books:
            book_data = extract_book_data(
                book=book,
                category_name=category_name,
                book_id=book_id,
                current_url=current_url,
            )

            category_books.append(book_data)
            book_id += 1

        next_button = soup.select_one(SELECTORS["next_page"])

        if next_button:
            current_url = urljoin(current_url, next_button["href"])
        else:
            current_url = None

    return category_books, book_id


def validate_dataframe(df, categories_count):
    """Validate final data before saving it."""
    if list(df.columns) != COLUMNS:
        raise ValueError("Columns are not in the required order.")

    if df.empty:
        raise ValueError("Dataframe is empty. No data was scraped.")

    if len(df) != EXPECTED_TOTAL_BOOKS:
        raise ValueError(f"Expected {EXPECTED_TOTAL_BOOKS} books, but got {len(df)}.")

    if df["id"].duplicated().any():
        raise ValueError("Duplicate IDs found.")

    expected_ids = list(range(1, len(df) + 1))

    if df["id"].tolist() != expected_ids:
        raise ValueError("IDs are not sequential.")

    if df["book_name"].isnull().any() or (df["book_name"].str.strip() == "").any():
        raise ValueError("Some book names are missing.")

    if df["image"].isnull().any() or (df["image"].str.strip() == "").any():
        raise ValueError("Some image URLs are missing.")

    if not df["image"].str.startswith("https://").all():
        raise ValueError("Some image URLs are not absolute HTTPS links.")

    if not df["rating"].between(1, 5).all():
        raise ValueError("Rating values must be between 1 and 5.")

    if not pd.api.types.is_float_dtype(df["price"]):
        raise ValueError("Price column must be float.")

    if not pd.api.types.is_bool_dtype(df["status"]):
        raise ValueError("Status column must be Boolean True/False.")

    if df["category"].nunique() != categories_count:
        raise ValueError("Not all categories were scraped.")

    print("Validation passed successfully.")


def main():
    all_books = []
    next_id = 1

    categories = get_categories()
    print(f"Total categories found: {len(categories)}")

    for category in categories:
        print(f"Scraping category: {category['name']}")

        category_books, next_id = scrape_category(
            category_name=category["name"],
            category_url=category["url"],
            start_id=next_id,
        )

        all_books.extend(category_books)

    df = pd.DataFrame(all_books, columns=COLUMNS)

    validate_dataframe(df, categories_count=len(categories))

    OUTPUT_DIR.mkdir(exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("Scraping completed successfully.")
    print(f"Total books scraped: {len(df)}")
    print(f"Saved file: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()