# Books Scraping Task

This project is a web scraping task using Python. It extracts book data from the website Books to Scrape and saves the final structured data into a CSV file.

## Project Goal

The goal of this task is to scrape all book data from all available categories on the website, organize the extracted information into a clean table, and store the result in a CSV file.

## Website

https://books.toscrape.com/

## Extracted Columns

The final dataset contains the following columns:

- id
- image
- book_name
- rating
- price
- status
- category

## How the Scraper Works

The script starts from the home page and extracts all category links from the sidebar.  
Then, it visits each category page and extracts all books that belong to that category.

For each book, the scraper extracts:

- Book image URL
- Book name
- Rating
- Price
- Availability status
- Category name

The scraper also handles pagination by following the Next button when a category has more than one page.

## Data Processing

The extracted data is cleaned and converted into suitable formats:

- The rating is extracted from the HTML class name, such as `star-rating Three`, and converted into a numeric value from 1 to 5.
- The price is converted from text into a numeric float value.
- The availability status is converted into a Boolean value:
  - `True` means the book is in stock.
  - `False` means the book is not in stock.
- Each book is given an auto-generated sequential id.

## Output

The final CSV file is saved in:

`data/books_data.csv`

## Validation

Before saving the final CSV file, the script validates the extracted data by checking:

- The required columns are in the correct order.
- The final dataset is not empty.
- The total number of scraped books is 1000.
- The ids are unique and sequential.
- The rating values are between 1 and 5.
- The price column is numeric.
- The status column is Boolean.
- All categories were scraped.

## Project Structure

`main.py`  
Main Python script that performs the scraping, extraction, validation, and CSV saving.

`requirements.txt`  
Contains the required Python packages needed to run the project.

`data/books_data.csv`  
The final output file containing the scraped book data.

`.gitignore`  
Prevents unnecessary files such as the virtual environment from being uploaded to GitHub.

## Requirements

Install the required packages using:

`python -m pip install -r requirements.txt`

## How to Run

Run the project using:

`python main.py`

After running the script, the output file will be created inside the `data` folder.

## Notes

The website is structured using repeated book cards, not HTML tables.  
Therefore, the scraper extracts data from the HTML book cards and converts the result into a structured table.

The availability status appears as `True` for all rows because all books on the website are marked as in stock.
