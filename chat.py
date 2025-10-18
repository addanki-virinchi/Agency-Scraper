import csv
import time
import re
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, WebDriverException, NoSuchElementException
)
from webdriver_manager.chrome import ChromeDriverManager


# -------------------------- Chrome Setup --------------------------
def create_driver(headless=False):
    """Initialize a Chrome WebDriver instance."""
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except WebDriverException as e:
        print(f"[Driver Error] {e}")
        return None


# -------------------------- Data Extraction --------------------------
def extract_business_data(driver, url):
    """Extract business information from a Google Maps business URL."""
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 10)

        # Name
        name = wait.until(
            EC.presence_of_element_located((By.XPATH, "//h1[contains(@class, 'fontHeadlineLarge')]"))
        ).text.strip()

        # Address
        try:
            address = driver.find_element(By.XPATH, "//button[@data-item-id='address']").text.strip()
        except NoSuchElementException:
            address = None

        # Website
        try:
            website = driver.find_element(By.XPATH, "//a[@data-item-id='authority']").get_attribute("href")
        except NoSuchElementException:
            website = None

        # Phone
        try:
            phone = driver.find_element(By.XPATH, "//button[@data-item-id='phone']").text.strip()
        except NoSuchElementException:
            phone = None

        # Rating
        try:
            rating = driver.find_element(By.XPATH, "//div[@role='img']").get_attribute("aria-label")
        except NoSuchElementException:
            rating = None

        # Operating Hours
        try:
            hours = driver.find_element(By.XPATH, "//div[contains(@aria-label, 'Hours')]").get_attribute("aria-label")
        except NoSuchElementException:
            hours = None

        # Permanently Closed
        try:
            closed = "Permanently closed" in driver.page_source
        except Exception:
            closed = False

        return {
            'URL': url,
            'Name': name,
            'Address': address,
            'Website': website,
            'Phone': phone,
            'Rating': rating,
            'Operating_Hours': hours,
            'Permanently_Closed': closed
        }

    except TimeoutException:
        print(f"[Timeout] {url}")
    except Exception as e:
        print(f"[Error scraping {url}] {e}")

    return {
        'URL': url,
        'Name': None,
        'Address': None,
        'Website': None,
        'Phone': None,
        'Rating': None,
        'Operating_Hours': None,
        'Permanently_Closed': None
    }


# -------------------------- Thread Worker --------------------------
def process_url(row, input_headers):
    """Worker for each URL row."""
    driver = create_driver()
    if not driver:
        return None

    url = row.get("URL", "")
    data = extract_business_data(driver, url)
    driver.quit()

    # Preserve input CSV columns + append scraped data
    output_row = {**{col: row.get(col, None) for col in input_headers}, **data}
    return output_row


# -------------------------- CSV Helpers --------------------------
def read_input_csv(input_file):
    """Read URLs and data from input CSV."""
    with open(input_file, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return list(reader), reader.fieldnames


def write_output_csv(output_file, data, headers):
    """Write or append scraped data to output CSV."""
    file_exists = os.path.exists(output_file)
    with open(output_file, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=headers)
        if not file_exists:
            writer.writeheader()
        writer.writerows(data)


# -------------------------- Main Scraper --------------------------
def main(input_file="input.csv", output_file="output.csv", max_threads=5):
    """Main threaded scraping controller."""
    rows, input_headers = read_input_csv(input_file)

    output_headers = input_headers + [
        'Name', 'Address', 'Website', 'Phone', 'Rating', 'Operating_Hours', 'Permanently_Closed'
    ]

    print(f"[INFO] Starting scrape for {len(rows)} URLs using {max_threads} threads...")

    results = []
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(process_url, row, input_headers): row for row in rows}

        for future in as_completed(futures):
            data = future.result()
            if data:
                results.append(data)
                print(f"[DONE] {data.get('URL')}")

            # Periodic save
            if len(results) % 10 == 0:
                write_output_csv(output_file, results, output_headers)
                results.clear()

    # Write remaining results
    if results:
        write_output_csv(output_file, results, output_headers)

    print("[INFO] Scraping completed successfully!")


# -------------------------- Entry Point --------------------------
if __name__ == "__main__":
    main(input_file="filtered_places.csv", output_file="filterd_output.csv", max_threads=5)
