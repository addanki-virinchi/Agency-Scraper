'''from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import undetected_chromedriver as uc
import time
import csv
import pandas as pd
import re

def extract_phone_number(driver, wait):
    phone_xpaths = [
        # Try different potential phone number locations
        "//div[contains(@class, 'fontBodyMedium') and contains(text(), '0')]",
        "//div[contains(@class, 'Io6YTe') and contains(text(), '0')]",
        "//div[contains(@class, 'fontBodyMedium kR99db')]",
        "//div[contains(@class, 'rogA2c')]//div[contains(@class, 'Io6YTe')]"
    ]
    
    for xpath in phone_xpaths:
        try:
            # Try to find the element
            phone_elements = driver.find_elements(By.XPATH, xpath)
            
            for element in phone_elements:
                # Extract text
                phone_text = element.text.strip()
                
                # Use regex to extract phone number
                phone_match = re.findall(r'\d{3,}[-\s]?\d{3,}[-\s]?\d{3,}', phone_text)
                
                if phone_match:
                    # Return the first matched phone number
                    return phone_match[0].replace(' ', '').replace('-', '')
        
        except Exception as e:
            print(f"Error searching for phone number: {str(e)}")
    
    return "Phone Number Not Found"

def scrape_data(url, driver, wait):
    try:
        # Navigate to the URL
        driver.get(url)
        time.sleep(3)  # Give some time for the page to load
        
        # Initialize variables with default values
        address = website = phone = "Not Found"
        
        try:
            # Address extraction
            address_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class,'rogA2c')]/div[contains(@class,'Io6YTe')]")
            ))
            address = address_element.text
        except (TimeoutException, NoSuchElementException):
            pass

        try:
            # Website extraction
            website_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@aria-label, 'Website')]")
            ))
            website = website_element.get_attribute("href")
        except (TimeoutException, NoSuchElementException):
            pass

        # Phone number extraction
        phone = extract_phone_number(driver, wait)

        return {
            'URL': url,
            'Address': address,
            'Website': website,
            'Phone': phone
        }
    except WebDriverException as e:
        print(f"Error processing URL {url}: {str(e)}")
        return {
            'URL': url,
            'Address': 'Error',
            'Website': 'Error',
            'Phone': 'Error'
        }

def main():
    # Read URLs from CSV file
    try:
        df = pd.read_csv('Project4_alt.csv')  # Replace 'input.csv' with your CSV file name
        urls = df['URL'].tolist()  # Assuming 'URL' is the column name
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return

    # Initialize the driver
    driver = uc.Chrome()
    wait = WebDriverWait(driver, 10)
    
    # List to store results
    results = []

    try:
        # Process each URL
        for url in urls:
            print(f"Processing URL: {url}")
            result = scrape_data(url, driver, wait)
            results.append(result)
            time.sleep(2)  # Add delay between requests
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        # Close the driver
        driver.quit()
        
        # Save results to CSV
        try:
            df_results = pd.DataFrame(results)
            df_results.to_csv('Project_output.csv', index=False)
            print("Results saved to output.csv")
        except Exception as e:
            print(f"Error saving results: {str(e)}")

if __name__ == "__main__":
    main()'''
    
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc
import time
import csv
import pandas as pd
import re

def scroll_page(driver):
    """
    Scroll the page to help reveal dynamic content
    """
    # Get the total height of the page
    total_height = driver.execute_script("return document.body.scrollHeight")
    
    # Scroll in increments
    for i in range(0, total_height, 500):
        driver.execute_script(f"window.scrollTo(0, {i});")
        time.sleep(0.5)
    
    # Scroll back to top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)


def extract_phone_number(driver, wait):
    """Extract phone number using exact Google Maps HTML structure"""
    try:
        # Scroll and wait for page to be fully loaded
        scroll_page(driver)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        time.sleep(1)

        # Exact XPath selectors based on confirmed HTML structure
        phone_xpaths = [
            # Most specific - targets the exact phone div structure
            "//div[contains(@class, 'AeaXub')]//div[contains(@class, 'Io6YTe') and contains(@class, 'fontBodyMedium') and contains(@class, 'kR99db')]",

            # Parent-child relationship targeting phone container
            "//div[contains(@class, 'rogA2c')]//div[contains(@class, 'Io6YTe') and contains(@class, 'fontBodyMedium')]",

            # Class combination for phone text element
            "//div[contains(@class, 'Io6YTe') and contains(@class, 'kR99db')]",

            # Fallback for tel: links
            "//a[contains(@href, 'tel:')]"
        ]

        for xpath in phone_xpaths:
            try:
                phone_elements = driver.find_elements(By.XPATH, xpath)

                for element in phone_elements:
                    try:
                        # Scroll to element to ensure it's visible
                        driver.execute_script("arguments[0].scrollIntoView(true);", element)
                        time.sleep(0.3)

                        # Extract text or href for tel: links
                        if "tel:" in xpath:
                            phone_text = element.get_attribute("href")
                            if phone_text and phone_text.startswith("tel:"):
                                phone_text = phone_text.replace("tel:", "").strip()
                        else:
                            phone_text = element.text.strip()

                        if phone_text:
                            # Phone number regex patterns for Indian numbers
                            phone_patterns = [
                                r'\+91[-.\s]?\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{4}',  # +91 format with spaces
                                r'0\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{4}',  # 0 prefix format (like 044 2522 2944)
                                r'\d{3}[-.\s]?\d{4}[-.\s]?\d{4}',  # 3-4-4 format
                                r'\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{4}',  # General landline format
                                r'[6-9]\d{9}',  # 10-digit mobile format
                                r'\+91[-.\s]?[6-9]\d{9}'  # +91 mobile format
                            ]

                            for pattern in phone_patterns:
                                phone_matches = re.findall(pattern, phone_text)
                                if phone_matches:
                                    phone_number = phone_matches[0]
                                    # Clean the phone number (keep digits and + only)
                                    cleaned_number = ''.join(c for c in phone_number if c.isdigit() or c == '+')

                                    # Validate length (Indian numbers: 10-13 digits)
                                    digit_count = len(re.findall(r'\d', cleaned_number))
                                    if 10 <= digit_count <= 13:
                                        return cleaned_number
                    except Exception:
                        continue

            except (NoSuchElementException, TimeoutException):
                continue

        return "Phone Number Not Found"

    except Exception as e:
        print(f"Error in phone extraction: {str(e)}")
        return "Phone Number Not Found"
'''def extract_phone_number(driver, wait):
    # Scroll the page first
    scroll_page(driver)
    
    try:
        # Try the most reliable XPath first - looking for elements with phone icon
        phone_elements = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Phone:')]")
        if phone_elements:
            for element in phone_elements:
                phone_text = element.get_attribute("aria-label")
                if phone_text:
                    # Extract just the number part after "Phone: "
                    phone_number = phone_text.split("Phone:")[1].strip()
                    return phone_number.replace(" ", "")
        
        # Alternative approach - look for elements with telephone numbers in the text
        phone_xpaths = [
            "//button[contains(@data-item-id, 'phone:')]",
            "//div[contains(@class, 'Io6YTe')][./parent::div[contains(@class, 'rogA2c')]][./parent::div/div/span[contains(@class, 'NhBTye')]]",
            "//span[contains(@class, 'NhBTye')]/parent::div/following-sibling::div//div[contains(@class, 'Io6YTe')]"
        ]
        
        for xpath in phone_xpaths:
            elements = driver.find_elements(By.XPATH, xpath)
            for element in elements:
                # Scroll to the element to ensure it's in view
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)
                
                phone_text = element.text.strip()
                # Check if this looks like a phone number
                if re.search(r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}|\d{5}[-.\s]?\d{5}|\+\d{1,4}[-.\s]?\d+', phone_text):
                    # Clean the phone number
                    return ''.join(c for c in phone_text if c.isdigit() or c == '+')
        
        # Look for href attributes with tel: links
        tel_links = driver.find_elements(By.XPATH, "//a[contains(@href, 'tel:')]")
        if tel_links:
            for link in tel_links:
                href = link.get_attribute("href")
                if href.startswith("tel:"):
                    return href.replace("tel:", "")
    
    except Exception as e:
        print(f"Error searching for phone number: {str(e)}")
    
    return "Phone Number Not Found"'''

def scrape_data(url, driver, wait):
    try:
        # Navigate to the URL
        driver.get(url)
        time.sleep(3)  # Give some time for the page to load
        
        # Scroll the page
        scroll_page(driver)
        
        # Initialize variables with default values
        address = website = phone = "Not Found"
        
        try:
            # Address extraction
            address_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class,'rogA2c')]/div[contains(@class,'Io6YTe')]")
            ))
            # Scroll to address element
            driver.execute_script("arguments[0].scrollIntoView(true);", address_element)
            address = address_element.text
        except (TimeoutException, NoSuchElementException):
            pass

        try:
            # Website extraction
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

       

        # Phone number extraction
        phone = extract_phone_number(driver, wait)

        return {'URL': url, 'Name': name, 'Address': address, 'Website': website, 'Phone': phone}

    except WebDriverException as e:
        print(f"Error processing URL {url}: {str(e)}")
        return {
          
            'URL': url,
            'Address': 'Error',
            'Website': 'Error',
            'Phone': 'Error'
        }

def main():
    # Read URLs from CSV file
    try:
        df = pd.read_csv('search_4.csv')  # Replace with your CSV file name
        urls = df['URL'].tolist()  # Assuming 'URL' is the column name
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return

    # Initialize the driver
    options = uc.ChromeOptions()
    # Optional: Add some Chrome options to improve scraping
    options.add_argument('--window-size=1920,1080')
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 15)  # Increased timeout
    
    # List to store results
    results = []

    try:
        # Process each URL
        for url in urls:
            print(f"Processing URL: {url}")
            result = scrape_data(url, driver, wait)
            print(result)
            results.append(result)
            time.sleep(2)  # Add delay between requests
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        # Close the driver
        driver.quit()
        
        # Save results to CSV
        try:
            df_results = pd.DataFrame(results)
            df_results.to_csv('search_4_op.csv', index=False, columns=['URL', 'Name', 'Address', 'Website', 'Phone'])

            print("Results saved to output.csv")
        except Exception as e:
            print(f"Error saving results: {str(e)}")

if __name__ == "__main__":
    main()
    
    
'''from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
import undetected_chromedriver as uc
import time
import csv
import pandas as pd
import re

def scroll_page(driver):
    """
    Scroll the page to help reveal dynamic content
    """
    # Get the total height of the page
    total_height = driver.execute_script("return document.body.scrollHeight")
    
    # Scroll in increments
    for i in range(0, total_height, 500):
        driver.execute_script(f"window.scrollTo(0, {i});")
        time.sleep(0.5)
    
    # Scroll back to top
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

def extract_phone_number(driver, wait):
    # Scroll the page first
    scroll_page(driver)
    
    phone_xpaths = [
        "//div[contains(@class, 'fontBodyMedium') and contains(text(), '0')]",
        "//div[contains(@class, 'Io6YTe') and contains(text(), '0')]",
        "//div[contains(@class, 'fontBodyMedium kR99db')]",
        "//div[contains(@class, 'rogA2c')]//div[contains(@class, 'Io6YTe')]",
        "//div[contains(@class, 'phone-number')]",
        "//a[contains(@href, 'tel:')]"
    ]
    
    for xpath in phone_xpaths:
        try:
            # Try to find the elements
            phone_elements = driver.find_elements(By.XPATH, xpath)
            
            for element in phone_elements:
                # Scroll to the element to ensure it's in view
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)
                
                # Extract text
                phone_text = element.text.strip()
                
                # Use regex to extract phone number
                phone_match = re.findall(r'\d{3,}[-\s]?\d{3,}[-\s]?\d{4}', phone_text)
                
                if phone_match:
                    # Return the first matched phone number
                    return phone_match[0].replace(' ', '').replace('-', '')
        
        except Exception as e:
            print(f"Error searching for phone number: {str(e)}")
    
    return "Phone Number Not Found"

def scrape_data(url, driver, wait):
    try:
        # Navigate to the URL
        driver.get(url)
        time.sleep(3)  # Give some time for the page to load
        
        # Scroll the page
        scroll_page(driver)
        
        # Initialize variables with default values
       
        address = "Not Found"
        website = "Not Found"
        phone = "Not Found"
        
        try:
            # Address extraction
            address_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class,'rogA2c')]/div[contains(@class,'Io6YTe')]")
            ))
            # Scroll to address element
            driver.execute_script("arguments[0].scrollIntoView(true);", address_element)
            address = address_element.text
        except (TimeoutException, NoSuchElementException):
            pass

        try:
            # Website extraction
            website_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//a[contains(@aria-label, 'Website')]")
            ))
            website = website_element.get_attribute("href")
        except (TimeoutException, NoSuchElementException):
            pass

        try:
            company_name = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.DUwDvf.lfPIob'))) 
            company = company_name.text
        except (TimeoutException, NoSuchElementException):
            pass

        # Phone number extraction
        phone = extract_phone_number(driver, wait)

        return {
            'Company Name': company,
            'URL': url,
            'Address': address,
            'Website': website,
            'Phone': phone
        }
    except WebDriverException as e:
        print(f"Error processing URL {url}: {str(e)}")
        return {
            'Company Name': "Not Found",
            'URL': url,
            'Address': 'Error',
            'Website': 'Error',
            'Phone': 'Error'
        }

def main():
    # Read URLs from CSV file
    try:
        df = pd.read_csv('Catering_in_Mumbai.csv')  # Replace with your CSV file name
        urls = df['URL'].tolist()  # Assuming 'URL' is the column name
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return

    # Initialize the driver
    options = uc.ChromeOptions()
    # Optional: Add some Chrome options to improve scraping
    options.add_argument('--window-size=1920,1080')
    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 15)  # Increased timeout
    
    # List to store results
    results = []

    try:
        # Process each URL
        for url in urls:
            print(f"Processing URL: {url}")
            result = scrape_data(url, driver, wait)
            results.append(result)
            print(results)
            time.sleep(2)  # Add delay between requests
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        # Close the driver
        driver.quit()
        
        # Save results to CSV
        try:
            df_results = pd.DataFrame(results)
            df_results.to_csv('Catering_in_Mumbai_output.csv', index=False)
            print("Results saved to output.csv")
        except Exception as e:
            print(f"Error saving results: {str(e)}")

if __name__ == "__main__":
    main()  '''
    
