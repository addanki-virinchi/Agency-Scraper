import re
import math
import csv
import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ---------------------------
# Utility: extract lat/lon from Google Maps URL
# ---------------------------
def extract_coordinates_from_url(url):
    """
    Extract latitude and longitude coordinates from Google Maps URL

    Args:
        url (str): Google Maps URL containing coordinates

    Returns:
        tuple: (latitude, longitude) as floats, or (None, None) if not found
    """
    try:
        # Use regex to find latitude (3d parameter) and longitude (4d parameter)
        lat_pattern = r'3d([+-]?\d+\.?\d*)'
        lng_pattern = r'4d([+-]?\d+\.?\d*)'

        lat_match = re.search(lat_pattern, url)
        lng_match = re.search(lng_pattern, url)

        if lat_match and lng_match:
            latitude = float(lat_match.group(1))
            longitude = float(lng_match.group(1))
            print(f"    ✅ Coordinates extracted: {latitude}, {longitude}")
            return latitude, longitude
        else:
            # Fallback to original pattern for URLs with @lat,lon format
            match = re.search(r'/@([-+]?\d+\.\d+),([-+]?\d+\.\d+)', url)
            if match:
                latitude = float(match.group(1))
                longitude = float(match.group(2))
                print(f"    ✅ Coordinates extracted (fallback): {latitude}, {longitude}")
                return latitude, longitude
            else:
                print(f"    ❌ No coordinates found in URL")
                return None, None
    except Exception as e:
        print(f"    ❌ Error extracting coordinates: {str(e)}")
        return None, None


# ---------------------------
# Utility: Haversine distance
# ---------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------
# Load existing URLs from CSV files for deduplication
# ---------------------------
def load_existing_urls(all_urls_csv, filtered_csv):
    """Load existing URLs from both CSV files to avoid duplicates"""
    existing_urls = set()

    # Load from all_scraped_urls.csv
    try:
        df_all = pd.read_csv(all_urls_csv)
        if 'url' in df_all.columns:
            urls_from_all = set(df_all['url'].dropna())
            existing_urls.update(urls_from_all)
            print(f"📋 Loaded {len(urls_from_all)} existing URLs from {all_urls_csv}")
        else:
            print(f"⚠️ No 'url' column found in {all_urls_csv}")
    except FileNotFoundError:
        print(f"📄 {all_urls_csv} not found - will create new file")
    except Exception as e:
        print(f"⚠️ Error reading {all_urls_csv}: {str(e)}")

    # Load from filtered_places.csv
    try:
        df_filtered = pd.read_csv(filtered_csv)
        if 'url' in df_filtered.columns:
            urls_from_filtered = set(df_filtered['url'].dropna())
            existing_urls.update(urls_from_filtered)
            print(f"🎯 Loaded {len(urls_from_filtered)} existing URLs from {filtered_csv}")
        else:
            print(f"⚠️ No 'url' column found in {filtered_csv}")
    except FileNotFoundError:
        print(f"📄 {filtered_csv} not found - will create new file")
    except Exception as e:
        print(f"⚠️ Error reading {filtered_csv}: {str(e)}")

    print(f"🔍 Total unique URLs already processed: {len(existing_urls)}")
    return existing_urls


# ---------------------------
# Scrape Google Maps for each search term (collect ALL URLs)
# ---------------------------
def scrape_all_places(search_item, search_lat, search_lon, all_urls_csv="all_scraped_urls.csv", filtered_csv="filtered_places.csv"):
    """Scrape all URLs with incremental CSV writing, deduplication, and detailed debugging"""
    urls_data = []
    driver = uc.Chrome(headless=False)

    # Load existing URLs for deduplication
    existing_urls = load_existing_urls(all_urls_csv, filtered_csv)

    # Initialize CSV files with headers if they don't exist
    for csv_file in [all_urls_csv, filtered_csv]:
        try:
            pd.read_csv(csv_file)
        except FileNotFoundError:
            # Create CSV with headers
            headers_df = pd.DataFrame(columns=[
                "search_item", "search_lat", "search_lon", "url",
                "url_lat", "url_lon", "distance_km", "within_7km"
            ])
            headers_df.to_csv(csv_file, index=False)
            print(f"📄 Created new CSV file: {csv_file}")

    # Counters for logging
    new_urls_count = 0
    skipped_urls_count = 0

    try:
        query = f'https://www.google.com/maps/search/"{search_item}"/@{search_lat},{search_lon},13000m'
        print(f"🌐 Loading: {query}")
        driver.get(query)
        time.sleep(5)

        urls = set()
        scroll_pause_time = 2
        scroll_attempts = 0
        max_attempts = 10
        urls_found_this_scroll = 0

        while scroll_attempts < max_attempts:
            try:
                # Try multiple selectors for the scrollable div
                scrollable_div = None
                scrollable_selectors = [
                    "div.m6QErb.DxyBCb.kA9KIf.dS8AEf.ecceSd",
                    "div[role='main']",
                    "div.siAUzd",
                    "div.m6QErb"
                ]

                for selector in scrollable_selectors:
                    try:
                        scrollable_div = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        print(f"  ✅ Found scrollable div with selector: {selector}")
                        break
                    except TimeoutException:
                        continue

                if not scrollable_div:
                    print(f"  ❌ Could not find scrollable div, trying to scroll page body")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                # Try multiple selectors for place links
                places = []
                place_selectors = [
                    "a[href*='maps/place']",
                    "a[data-value*='maps/place']",
                    "a[href*='/place/']",
                    "div[data-result-index] a",
                    ".hfpxzc"
                ]

                for selector in place_selectors:
                    found_places = driver.find_elements(By.CSS_SELECTOR, selector)
                    if found_places:
                        places.extend(found_places)
                        print(f"  ✅ Found {len(found_places)} places with selector: {selector}")

                # Remove duplicates based on href
                unique_places = []
                seen_hrefs = set()
                for place in places:
                    href = place.get_attribute("href")
                    if href and href not in seen_hrefs:
                        unique_places.append(place)
                        seen_hrefs.add(href)

                places = unique_places
                print(f"  📍 Scroll {scroll_attempts + 1}/{max_attempts}: Found {len(places)} unique place elements")

                new_urls_this_scroll = 0
                for place in places:
                    url = place.get_attribute("href")
                    if url and url not in urls:
                        urls.add(url)

                        # Check if URL already exists in previous runs
                        if url in existing_urls:
                            skipped_urls_count += 1
                            print(f"    ⏭️ Skipping URL #{len(urls)} (already processed): {url[:80]}...")
                            continue

                        new_urls_this_scroll += 1
                        new_urls_count += 1

                        print(f"    🔗 Processing NEW URL #{len(urls)}: {url[:80]}...")

                        url_lat, url_lon = extract_coordinates_from_url(url)

                        if url_lat is not None and url_lon is not None:
                            distance = haversine(search_lat, search_lon, url_lat, url_lon)
                            within_7km = "YES" if distance <= 7 else "NO"

                            url_data = {
                                "search_item": search_item,
                                "search_lat": search_lat,
                                "search_lon": search_lon,
                                "url": url,
                                "url_lat": url_lat,
                                "url_lon": url_lon,
                                "distance_km": round(distance, 2),
                                "within_7km": within_7km
                            }

                            urls_data.append(url_data)

                            # Add to existing URLs set to prevent duplicates within this session
                            existing_urls.add(url)

                            # Append to all_scraped_urls.csv immediately
                            pd.DataFrame([url_data]).to_csv(all_urls_csv, mode='a', header=False, index=False)

                            # Also append to filtered CSV if within 7km
                            if within_7km == "YES":
                                pd.DataFrame([url_data]).to_csv(filtered_csv, mode='a', header=False, index=False)

                            print(f"    📊 Distance: {distance:.2f} km | Within 7km: {within_7km}")
                        else:
                            print(f"    ⚠️ Skipping URL - coordinates not found")

                print(f"  ➕ New URLs this scroll: {new_urls_this_scroll}")

                # If no new URLs found in this scroll, we might be done
                if new_urls_this_scroll == 0:
                    print(f"  🔄 No new URLs found, continuing to scroll...")

                # Scroll down using multiple methods
                if scrollable_div:
                    try:
                        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                    except Exception:
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                else:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

                time.sleep(scroll_pause_time)
                scroll_attempts += 1

            except Exception as e:
                print(f"  ❌ Scroll error: {str(e)}")
                scroll_attempts += 1

    except Exception as e:
        print(f"❌ Error for {search_item}: {str(e)}")
    finally:
        driver.quit()

    print(f"✅ Search '{search_item}' completed:")
    print(f"   - New URLs processed: {new_urls_count}")
    print(f"   - URLs skipped (duplicates): {skipped_urls_count}")
    print(f"   - Total URLs found this session: {len(urls_data)}")
    return urls_data





# ---------------------------
# Main Function
# ---------------------------
def main():
    input_csv = "maps_results.csv"  # Use the sample file with coordinates
    output_csv = "filtered_places.csv"
    all_urls_csv = "all_scraped_urls.csv"  # File to store all URLs with incremental writing

    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"❌ Error: Input file '{input_csv}' not found.")
        print(f"💡 Please ensure you have a CSV file with columns: search_item, latitude, longitude")
        return
    except Exception as e:
        print(f"❌ Error reading input file: {str(e)}")
        return

    # Validate required columns
    required_columns = ['search_item', 'latitude', 'longitude']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"❌ Error: Missing required columns: {missing_columns}")
        return

    print(f"🚀 Starting scraping process...")
    print(f"📄 Output files: {all_urls_csv} (all URLs), {output_csv} (filtered URLs)")

    total_scraped = 0
    total_filtered = 0

    for _, row in df.iterrows():
        search_item = row['search_item']

        # Handle missing or invalid coordinates
        try:
            search_lat = float(row['latitude']) if pd.notna(row['latitude']) else None
            search_lon = float(row['longitude']) if pd.notna(row['longitude']) else None
        except (ValueError, TypeError):
            print(f"⚠️ Skipping '{search_item}' - Invalid coordinates: lat={row['latitude']}, lon={row['longitude']}")
            continue

        if search_lat is None or search_lon is None:
            print(f"⚠️ Skipping '{search_item}' - Missing coordinates")
            continue

        print(f"\n🔍 Searching for: {search_item}")
        print(f"📍 Search center: {search_lat}, {search_lon}")

        # Scrape all URLs with incremental writing to both CSV files
        all_urls_for_item = scrape_all_places(search_item, search_lat, search_lon, all_urls_csv, output_csv)

        # Count filtered results from this search
        filtered_count = sum(1 for url_data in all_urls_for_item if url_data['within_7km'] == 'YES')

        total_scraped += len(all_urls_for_item)
        total_filtered += filtered_count

        print(f"✅ Found {filtered_count} places within 7 km (out of {len(all_urls_for_item)} total NEW places)")

    # Final summary
    print(f"\n📊 FINAL SUMMARY:")
    print(f"   - Total URLs scraped: {total_scraped}")
    print(f"   - URLs within 7 km: {total_filtered}")
    print(f"   - Filtering efficiency: {total_filtered/total_scraped*100:.1f}%" if total_scraped > 0 else "N/A")
    print(f"   - All URLs saved to: {all_urls_csv}")
    print(f"   - Filtered URLs saved to: {output_csv}")

    if total_scraped == 0:
        print("\n⚠️ No URLs were scraped. Please check:")
        print("   1. Internet connection")
        print("   2. Google Maps page structure hasn't changed")
        print("   3. CSS selectors are still valid")
    elif total_filtered == 0:
        print("\n⚠️ No results found within 7 km. Consider:")
        print("   1. Increasing the distance threshold")
        print("   2. Checking if search coordinates are correct")
        print("   3. Verifying the search area has relevant places")


if __name__ == "__main__":
    main()
