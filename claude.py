from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
import time
import csv
import pandas as pd
import re
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

# Global lock for thread-safe CSV writing
csv_lock = threading.Lock()

def extract_coordinates_from_url(url):
    """Extract latitude and longitude coordinates from Google Maps URL"""
    try:
        lat_pattern = r'3d([+-]?\d+\.?\d*)'
        lng_pattern = r'4d([+-]?\d+\.?\d*)'
        
        lat_match = re.search(lat_pattern, url)
        lng_match = re.search(lng_pattern, url)
        
        latitude = lat_match.group(1) if lat_match else "Not Found"
        longitude = lng_match.group(1) if lng_match else "Not Found"
        
        return latitude, longitude
    except Exception as e:
        print(f"Error extracting coordinates: {str(e)}")
        return "Not Found", "Not Found"

def safe_driver_quit(driver):
    """Safely quit the Chrome driver with error handling"""
    if not driver:
        return
    
    try:
        driver.quit()
    except Exception as e:
        print(f"Warning: Error during driver.quit(): {e}")
        try:
            if hasattr(driver, 'service') and driver.service and hasattr(driver.service, 'process'):
                driver.service.process.terminate()
        except:
            pass

def append_result_to_csv(result, output_filename, write_header=False):
    """Thread-safe append of a single result to the output CSV file"""
    try:
        with csv_lock:
            with open(output_filename, 'a', newline='', encoding='utf-8') as file:
                fieldnames = ['URL', 'Name', 'Address', 'Website', 'Phone', 'Store_Type', 
                            'Operating_Status', 'Operating_Hours', 'Rating', 'Permanently_Closed', 
                            'Latitude', 'Longitude']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                
                if write_header:
                    writer.writeheader()
                
                writer.writerow(result)
        return True
    except Exception as e:
        print(f"Error writing to CSV: {e}")
        return False

def check_url_already_processed(url, output_filename):
    """Check if a URL has already been processed"""
    if not os.path.exists(output_filename):
        return False
    
    try:
        with open(output_filename, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row.get('URL') == url:
                    return True
    except Exception as e:
        print(f"Warning: Error checking processed URLs: {e}")
    
    return False

def scroll_page(driver):
    """Scroll the page to help reveal dynamic content"""
    try:
        total_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(0, total_height, 500):
            driver.execute_script(f"window.scrollTo(0, {i});")
            time.sleep(0.3)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(0.5)
    except:
        pass

# def extract_phone_number(driver, wait):
#     """Extract phone number using Google Maps HTML structure"""
#     try:
#         scroll_page(driver)
#         wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
#         time.sleep(1)
        
#         # Prioritized XPath selectors based on the exact HTML structure
#         phone_xpaths = [
#             "//div[contains(@class, 'AeaXub')]//div[contains(@class, 'Io6YTe') and contains(@class, 'fontBodyMedium') and contains(@class, 'kR99db') and contains(@class, 'fdkmkc')]",
#             "//div[contains(@class, 'AeaXub')]//div[contains(@class, 'Io6YTe') and contains(@class, 'fontBodyMedium') and contains(@class, 'kR99db')]",
#             "//div[contains(@class, 'rogA2c')]//div[contains(@class, 'Io6YTe') and contains(@class, 'fontBodyMedium') and contains(@class, 'kR99db')]",
#             "//div[contains(@class, 'Io6YTe') and contains(@class, 'kR99db') and contains(@class, 'fdkmkc')]",
#             "//a[contains(@href, 'tel:')]"
#         ]
        
#         for xpath in phone_xpaths:
#             try:
#                 phone_elements = driver.find_elements(By.XPATH, xpath)
#                 for element in phone_elements:
#                     try:
#                         driver.execute_script("arguments[0].scrollIntoView(true);", element)
#                         time.sleep(0.3)
                        
#                         # Extract phone text
#                         if "tel:" in xpath:
#                             phone_text = element.get_attribute("href")
#                             if phone_text and phone_text.startswith("tel:"):
#                                 phone_text = phone_text.replace("tel:", "").strip()
#                         else:
#                             phone_text = element.text.strip()
                        
#                         if phone_text:
#                             # Clean the phone text - remove all non-digit characters except +
#                             cleaned = ''.join(c for c in phone_text if c.isdigit() or c == '+')
                            
#                             # Remove spaces and special characters for validation
#                             digits_only = ''.join(c for c in cleaned if c.isdigit())
                            
#                             # Validate phone number length and format
#                             # Indian phone numbers: 10 digits (mobile) or 11 digits (with STD code like 044)
#                             # With +91: 12-13 characters total
                            
#                             if len(digits_only) == 10:
#                                 # 10-digit number (mobile or landline without 0)
#                                 # Valid formats: 9876543210, 4412345678
#                                 return phone_text  # Return original format with spaces
                            
#                             elif len(digits_only) == 11:
#                                 # 11-digit number (landline with 0 prefix like 04412345678)
#                                 if digits_only.startswith('0'):
#                                     return phone_text
                            
#                             elif len(digits_only) == 12 and cleaned.startswith('+91'):
#                                 # +91 with 10 digits (mobile)
#                                 return phone_text
                            
#                             elif len(digits_only) == 13 and cleaned.startswith('+91'):
#                                 # +91 with 11 digits (landline with 0)
#                                 return phone_text
                            
#                             # Also check if it's a valid mobile number pattern (starts with 6-9)
#                             if len(digits_only) == 10 and digits_only[0] in '6789':
#                                 return phone_text
                    
#                     except:
#                         continue
            
#             except (NoSuchElementException, TimeoutException):
#                 continue
        
#         return "Phone Number Not Found"
    
    # except Exception as e:
    #     print(f"Error in phone extraction: {str(e)}")
    #     return "Phone Number Not Found"
def extract_phone_number(driver, wait):
    """Extract phone number using the exact Google Maps HTML structure"""
    try:
        scroll_page(driver)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(1)
        
        # XPath that looks for the phone icon container (cXHGnc) followed by the rogA2c container
        phone_xpath = "//div[contains(@class, 'AeaXub')]/div[contains(@class, 'cXHGnc')]/following-sibling::div[contains(@class, 'rogA2c')]//div[contains(@class, 'Io6YTe') and contains(@class, 'fontBodyMedium') and contains(@class, 'kR99db') and contains(@class, 'fdkmkc')]"
        
        # try:
        #     phone_element = driver.find_element(By.XPATH, phone_xpath)
        #     driver.execute_script("arguments[0].scrollIntoView(true);", phone_element)
        #     time.sleep(0.3)
            
        #     phone_text = phone_element.text.strip()
            
        #     if phone_text:
        #         return phone_text
        
        # except (NoSuchElementException, TimeoutException):
        #     pass
        try:
            phone_element = driver.find_element(By.CSS_SELECTOR,"div.rogA2c ")
        except (NoSuchElementException, TimeoutException):
            pass
        
        return "Phone Number Not Found"
    
    except Exception as e:
        print(f"Error in phone extraction: {str(e)}")
        return "Phone Number Not Found"
def extract_store_type(driver, wait):
    """Extract business category/store type from Google Maps page"""
    try:
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        
        category_selectors = [
            "//button[contains(@class, 'DkEaL')]",
            "//button[contains(@class, 'DkEaL') and contains(@jsaction, 'category')]",
            "//div[contains(@class, 'LBgpqf')]//button[contains(@class, 'DkEaL')]",
            "//span[contains(@class, 'YhemCb')]",
            "//button[contains(@aria-label, 'Category')]"
        ]
        
        for selector in category_selectors:
            try:
                category_elements = wait.until(lambda d: d.find_elements(By.XPATH, selector))
                for element in category_elements:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(0.3)
                        category_text = element.text.strip()
                        
                        if category_text:
                            excluded_terms = ['directions', 'save', 'share', 'nearby', 'call', 
                                            'website', 'menu', 'order', 'book']
                            if not any(term in category_text.lower() for term in excluded_terms):
                                return category_text
                    except:
                        continue
            except (NoSuchElementException, TimeoutException):
                continue
    except Exception as e:
        print(f"Error extracting store type: {str(e)}")
    
    return "Not Found"

def extract_operating_status_and_hours(driver, wait):
    """Extract operating status and hours from Google Maps page"""
    try:
        status = "Not Found"
        operating_hours = "Not Found"
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(1)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        
        status_selectors = [
            "//span[contains(@class, 'ZDu9vd')]",
            "//div[contains(@class, 'MkV9')]//span[contains(@class, 'ZDu9vd')]",
            "//span[contains(text(), 'Open') or contains(text(), 'Closed') or contains(text(), 'Closes')]",
            "//div[contains(@class, 'o0Svhf')]//span"
        ]
        
        for selector in status_selectors:
            try:
                status_elements = wait.until(lambda d: d.find_elements(By.XPATH, selector))
                for element in status_elements:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(0.3)
                        status_text = element.text.strip()
                        
                        if status_text and any(kw in status_text.lower() for kw in ['open', 'closed', 'closes', 'opens']):
                            status_text_lower = status_text.lower()
                            
                            if "closed" in status_text_lower and "opens" in status_text_lower:
                                status = "Open"
                                opens_match = re.search(r'opens\s+(.+?)(?:\s+\w{3})?$', status_text, re.IGNORECASE)
                                if opens_match:
                                    time_part = re.sub(r'\s+\w{3}$', '', opens_match.group(1).strip()).strip()
                                    operating_hours = f"Opens {time_part}"
                                return status, operating_hours
                            
                            elif "open" in status_text_lower and "closes" in status_text_lower:
                                status = "Open now" if "open now" in status_text_lower else "Open"
                                closes_match = re.search(r'closes\s+(.+?)(?:\s+\w{3})?$', status_text, re.IGNORECASE)
                                if closes_match:
                                    time_part = re.sub(r'\s+\w{3}$', '', closes_match.group(1).strip()).strip()
                                    operating_hours = f"Closes {time_part}"
                                return status, operating_hours
                            
                            elif "open now" in status_text_lower:
                                return "Open now", operating_hours
                            elif "open" in status_text_lower:
                                return "Open", operating_hours
                            elif "closed" in status_text_lower:
                                return "Closed", operating_hours
                    except:
                        continue
                
                if status != "Not Found":
                    break
            except (NoSuchElementException, TimeoutException):
                continue
        
        if operating_hours == "Not Found":
            try:
                hours_selectors = [
                    "//table[contains(@class, 'eK4R0e')]",
                    "//div[contains(@class, 't39EBf')]//table"
                ]
                
                for table_selector in hours_selectors:
                    try:
                        hours_table = driver.find_element(By.XPATH, table_selector)
                        if hours_table:
                            today_row = hours_table.find_element(By.XPATH, ".//tr[contains(@class, 'y0skZc')][1]")
                            if today_row:
                                hours_cell = today_row.find_element(By.XPATH, ".//td[contains(@class, 'mxowUb')]")
                                if hours_cell:
                                    hours_text = hours_cell.text.strip()
                                    if hours_text and ("–" in hours_text or "-" in hours_text):
                                        operating_hours = hours_text
                                        break
                    except (NoSuchElementException, TimeoutException):
                        continue
            except:
                pass
    
    except Exception as e:
        print(f"Error extracting operating status: {str(e)}")
    
    return status, operating_hours

def extract_rating(driver, wait):
    """Extract rating from Google Maps page"""
    try:
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        
        rating_selectors = [
            "//div[contains(@class, 'F7nice')]//span[@aria-hidden='true']",
            "//span[contains(@class, 'ceNzKf')]/preceding-sibling::span[@aria-hidden='true']",
            "//div[contains(@jslog, '76333')]//span[@aria-hidden='true']",
            "//span[@aria-hidden='true' and string-length(text()) <= 3]"
        ]
        
        for selector in rating_selectors:
            try:
                rating_elements = wait.until(lambda d: d.find_elements(By.XPATH, selector))
                for element in rating_elements:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(0.3)
                        rating_text = element.text.strip()
                        
                        if rating_text:
                            if rating_text.replace('.', '').replace(',', '').isdigit():
                                try:
                                    rating_value = float(rating_text.replace(',', '.'))
                                    if 0 <= rating_value <= 5:
                                        return rating_text
                                except ValueError:
                                    continue
                            
                            rating_match = re.search(r'^([0-5](?:\.[0-9])?)$', rating_text)
                            if rating_match:
                                return rating_match.group(1)
                    except:
                        continue
            except (NoSuchElementException, TimeoutException):
                continue
    except Exception as e:
        print(f"Error extracting rating: {str(e)}")
    
    return "Not Found"

def extract_permanently_closed_status(driver, wait):
    """Check if business is permanently closed"""
    try:
        closed_selectors = [
            "//span[contains(@class, 'aSftqf') and contains(text(), 'Permanently closed')]",
            "//div[contains(@class, 'MkV9')]//span[contains(text(), 'Permanently closed')]",
            "//span[contains(text(), 'Permanently closed')]"
        ]
        
        for selector in closed_selectors:
            try:
                closed_element = driver.find_element(By.XPATH, selector)
                if closed_element and "Permanently closed" in closed_element.text:
                    return "Yes"
            except (NoSuchElementException, TimeoutException):
                continue
    except Exception as e:
        print(f"Error checking permanently closed status: {str(e)}")
    
    return "No"

def scrape_data(url, driver, wait):
    """Main scraping function to extract all business information"""
    try:
        driver.get(url)
        time.sleep(8)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(2)
        
        scroll_page(driver)
        time.sleep(2)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        
        address = website = phone = "Not Found"
        
        try:
            address_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class,'rogA2c')]/div[contains(@class,'Io6YTe')]")
            ))
            driver.execute_script("arguments[0].scrollIntoView(true);", address_element)
            address = address_element.text
        except (TimeoutException, NoSuchElementException):
            pass
        
        try:
            website_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@aria-label, 'Website')]")
            ))
            website = website_element.get_attribute("href")
        except (TimeoutException, NoSuchElementException):
            pass
        
        try:
            name_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//h1[contains(@class, 'DUwDvf lfPIob')]")
            ))
            driver.execute_script("arguments[0].scrollIntoView(true);", name_element)
            name = name_element.text.strip()
        except (TimeoutException, NoSuchElementException):
            name = "Name Not Found"
        
        phone = extract_phone_number(driver, wait)
        store_type = extract_store_type(driver, wait)
        operating_status, operating_hours = extract_operating_status_and_hours(driver, wait)
        rating = extract_rating(driver, wait)
        permanently_closed = extract_permanently_closed_status(driver, wait)
        latitude, longitude = extract_coordinates_from_url(url)
        
        return {
            'URL': url,
            'Name': name,
            'Address': address,
            'Website': website,
            'Phone': phone,
            'Store_Type': store_type,
            'Operating_Status': operating_status,
            'Operating_Hours': operating_hours,
            'Rating': rating,
            'Permanently_Closed': permanently_closed,
            'Latitude': latitude,
            'Longitude': longitude
        }
    
    except WebDriverException as e:
        print(f"Error processing URL {url}: {str(e)}")
        latitude, longitude = extract_coordinates_from_url(url)
        return {
            'URL': url,
            'Name': 'Error',
            'Address': 'Error',
            'Website': 'Error',
            'Phone': 'Error',
            'Store_Type': 'Error',
            'Operating_Status': 'Error',
            'Operating_Hours': 'Error',
            'Rating': 'Error',
            'Permanently_Closed': 'Error',
            'Latitude': latitude,
            'Longitude': longitude
        }

def create_chrome_driver():
    """Create a Chrome driver with optimized options"""
    options = ChromeOptions()
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    # Uncomment for headless mode:
    # options.add_argument('--headless')
    
    driver = webdriver.Chrome(options=options)
    return driver

def process_single_url(url, output_filename, thread_id, total_urls, current_index):
    """Process a single URL in a thread-safe manner"""
    driver = None
    try:
        print(f"\n[Thread {thread_id}] [{current_index}/{total_urls}] Processing: {url}")
        
        if check_url_already_processed(url, output_filename):
            print(f"[Thread {thread_id}] ⏭️  Skipped - already processed")
            return {'status': 'skipped', 'url': url}
        
        driver = create_chrome_driver()
        wait = WebDriverWait(driver, 15)
        
        result = scrape_data(url, driver, wait)
        success = append_result_to_csv(result, output_filename, write_header=False)
        
        if success:
            print(f"[Thread {thread_id}] ✅ Saved: {result.get('Name', 'N/A')}")
            print(f"[Thread {thread_id}]    Phone: {result.get('Phone', 'N/A')}")
            print(f"[Thread {thread_id}]    Coords: {result.get('Latitude', 'N/A')}, {result.get('Longitude', 'N/A')}")
            return {'status': 'success', 'url': url, 'result': result}
        else:
            print(f"[Thread {thread_id}] ❌ Failed to save to CSV")
            return {'status': 'csv_error', 'url': url}
    
    except Exception as e:
        print(f"[Thread {thread_id}] ❌ Error: {str(e)}")
        try:
            latitude, longitude = extract_coordinates_from_url(url)
            error_result = {
                'URL': url, 'Name': 'Error', 'Address': 'Error', 'Website': 'Error',
                'Phone': 'Error', 'Store_Type': 'Error', 'Operating_Status': 'Error',
                'Operating_Hours': 'Error', 'Rating': 'Error', 'Permanently_Closed': 'Error',
                'Latitude': latitude, 'Longitude': longitude
            }
            append_result_to_csv(error_result, output_filename, write_header=False)
        except:
            pass
        return {'status': 'error', 'url': url, 'error': str(e)}
    
    finally:
        if driver:
            safe_driver_quit(driver)

def process_urls_multithreaded(urls, output_filename, file_exists):
    """Process URLs using multithreading"""
    MAX_THREADS = 2
    total_urls = len(urls)
    processed_new = 0
    skipped_existing = 0
    errors = 0
    
    print(f"\n{'='*80}")
    print(f"STARTING MULTI-THREADED DATA EXTRACTION")
    print(f"{'='*80}")
    print(f"Total URLs: {total_urls}")
    print(f"Output file: {output_filename}")
    print(f"Threads: {MAX_THREADS}")
    print("-" * 80)
    
    if not file_exists:
        try:
            with open(output_filename, 'w', newline='', encoding='utf-8') as file:
                fieldnames = ['URL', 'Name', 'Address', 'Website', 'Phone', 'Store_Type',
                            'Operating_Status', 'Operating_Hours', 'Rating', 'Permanently_Closed',
                            'Latitude', 'Longitude']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
            print("✅ Created output file with headers")
        except Exception as e:
            print(f"❌ Error creating output file: {e}")
            return
    
    try:
        with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            future_to_url = {}
            for index, url in enumerate(urls, 1):
                future = executor.submit(process_single_url, url, output_filename,
                                       index % MAX_THREADS, total_urls, index)
                future_to_url[future] = (url, index)
            
            for future in as_completed(future_to_url):
                url, index = future_to_url[future]
                try:
                    result = future.result()
                    
                    if result['status'] == 'success':
                        processed_new += 1
                    elif result['status'] == 'skipped':
                        skipped_existing += 1
                    else:
                        errors += 1
                    
                    completed = processed_new + skipped_existing + errors
                    print(f"📊 Progress: {completed}/{total_urls} | New: {processed_new} | Skipped: {skipped_existing} | Errors: {errors}")
                
                except Exception as e:
                    errors += 1
                    print(f"❌ Thread error for {url}: {str(e)}")
    
    except KeyboardInterrupt:
        print(f"\n⚠️  Interrupted by user")
        print(f"✅ Progress saved: {processed_new} URLs processed")
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        print(f"✅ Progress saved: {processed_new} URLs processed")
    finally:
        print(f"\n{'='*80}")
        print(f"EXTRACTION COMPLETED")
        print(f"{'='*80}")
        print(f"Total URLs: {total_urls}")
        print(f"New processed: {processed_new}")
        print(f"Skipped: {skipped_existing}")
        print(f"Errors: {errors}")
        print(f"Output: {output_filename}")
        
        try:
            if os.path.exists(output_filename):
                with open(output_filename, 'r', newline='', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    final_count = sum(1 for _ in reader)
                print(f"Total records in file: {final_count}")
        except Exception as e:
            print(f"Warning: Could not count records: {e}")
        
        print("="*80)

def main():
    input_filename = 'filtered_places.csv'
    
    if not os.path.exists(input_filename):
        print(f"Error: Input file '{input_filename}' not found!")
        return
    
    try:
        df = pd.read_csv(input_filename)
        if 'URL' not in df.columns:
            print(f"Error: 'URL' column not found")
            print(f"Available columns: {list(df.columns)}")
            return
        
        urls = df['URL'].tolist()
        print(f"Successfully loaded {len(urls)} URLs from {input_filename}")
    except Exception as e:
        print(f"Error reading CSV: {str(e)}")
        return
    
    output_filename = 'filtered_places_output.csv'
    file_exists = os.path.exists(output_filename)
    
    if file_exists:
        try:
            with open(output_filename, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                processed_count = sum(1 for row in reader)
            print(f"Found existing output with {processed_count} processed URLs")
            print("Will skip already processed URLs")
        except Exception as e:
            print(f"Warning: Error reading existing output: {e}")
    
    process_urls_multithreaded(urls, output_filename, file_exists)

if __name__ == "__main__":
    main()