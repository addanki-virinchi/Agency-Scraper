'''from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import undetected_chromedriver as uc
import time

def scroll_google_maps():
    driver = uc.Chrome()
    
    try:
        # Navigate to Google Maps
        driver.get('https://www.google.com/maps/search/premium+government+hospitals+in+delhi/@28.6385655,77.0180121,11z?entry=ttu&g_ep=EgoyMDI1MDExNS4wIKXMDSoASAFQAw%3D%3D')
        
        # Wait for initial load
        time.sleep(5)
        
        # Click the first result
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "hfpxzc"))
        )
        element.click()
        
        # Wait for the results panel to load
        time.sleep(3)
        
        urls = set()
        scroll_pause_time = 2
        scroll_attempts = 0
        max_attempts = 50  # Maximum number of scroll attempts
        
        while scroll_attempts < max_attempts:
            try:
                # Find the scrollable container
                scrollable_div = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.m6QErb.DxyBCb.kA9KIf.dS8AEf.ecceSd"))
                )
                
                # Get current scroll position
                last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
                
                # Collect URLs
                places = driver.find_elements(By.CSS_SELECTOR, "a[href*='maps/place']")
                for place in places:
                    url = place.get_attribute('href')
                    if url:
                        urls.add(url)
                
                # Scroll down
                driver.execute_script(
                    'arguments[0].scrollTop = arguments[0].scrollHeight', 
                    scrollable_div
                )
                
                # Wait for new content to load
                time.sleep(scroll_pause_time)
                
                # Calculate new scroll height
                new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
                
                # Print progress
                print(f"Scroll attempt {scroll_attempts + 1}, Found {len(urls)} unique URLs")
                
                # If heights are the same, try a few more times before breaking
                if new_height == last_height:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0  # Reset counter if we successfully scrolled
                
                # Small scroll up and down to trigger loading of new content
                driver.execute_script(
                    'arguments[0].scrollTop = arguments[0].scrollHeight - 100', 
                    scrollable_div
                )
                time.sleep(0.5)
                driver.execute_script(
                    'arguments[0].scrollTop = arguments[0].scrollHeight', 
                    scrollable_div
                )
                
            except Exception as e:
                print(f"Scroll error: {str(e)}")
                scroll_attempts += 1
                time.sleep(1)
        
        # Print results
        print("\nAll collected URLs:")
        for url in urls:
            print(url)
        print(f"\nTotal unique URLs found: {len(urls)}")
        
    except TimeoutException:
        print("Timeout waiting for element")
    except NoSuchElementException:
        print("Element not found")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Save URLs to file
        try:
            with open('google_maps_urls.txt', 'w') as f:
                for url in urls:
                    f.write(url + '\n')
            print("URLs saved to google_maps_urls.txt")
        except Exception as e:
            print(f"Error saving URLs: {str(e)}")
            
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    scroll_google_maps()'''
#Pipeline -1
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import undetected_chromedriver as uc
import time
import csv
import pandas as pd

def scroll_google_maps():
    driver = uc.Chrome()
    options = uc.ChromeOptions()
    options.add_argument('--headless')

    
    # Initialize lists to store data
    all_data = []
    
    try:
        
        driver.get('https://www.google.com/maps/search/IELTS+Coaching+or+Tuition+Institutes+in+Bhikaji+Cama+Place,+Delhi/@28.6317926,76.9776714,43024m/data=!3m2!1e3!4b1?entry=ttu&g_ep=EgoyMDI1MTAxMi4wIKXMDSoASAFQAw%3D%3D')
        time.sleep(5) 
        # Click the first result
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "hfpxzc"))
        )
        element.click()
        
        # Wait for the results panel to load
        time.sleep(3)
        
        urls = set()
        scroll_pause_time = 2
        scroll_attempts = 0
        max_attempts = 20  # Maximum number of scroll attempts
        
        while scroll_attempts < max_attempts:
            try:
                # Find the scrollable container
                scrollable_div = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.m6QErb.DxyBCb.kA9KIf.dS8AEf.ecceSd"))
                )
                
                # Get current scroll position
                last_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
                
                # Collect URLs and other data
                places = driver.find_elements(By.CSS_SELECTOR, "a[href*='maps/place']")
                for place in places:
                    url = place.get_attribute('href')
                    if url and url not in urls:
                        urls.add(url)
                        # You can add more data fields here if needed
                        place_data = {
                            'URL': url,
                            # Add more fields as needed
                        }
                        all_data.append(place_data)
                
                # Scroll down
                driver.execute_script(
                    'arguments[0].scrollTop = arguments[0].scrollHeight', 
                    scrollable_div
                )
                
                # Wait for new content to load
                time.sleep(scroll_pause_time)
                
                # Calculate new scroll height
                new_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_div)
                
                # Print progress
                print(f"Scroll attempt {scroll_attempts + 1}, Found {len(urls)} unique URLs")
                
                if new_height == last_height:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                
                # Small scroll up and down to trigger loading of new content
                driver.execute_script(
                    'arguments[0].scrollTop = arguments[0].scrollHeight - 100', 
                    scrollable_div
                )
                time.sleep(0.5)
                driver.execute_script(
                    'arguments[0].scrollTop = arguments[0].scrollHeight', 
                    scrollable_div
                )
                
            except Exception as e:
                print(f"Scroll error: {str(e)}")
                scroll_attempts += 1
                time.sleep(1)
        
        # Print the complete list of URLs
        print("\nComplete list of URLs:")
        for data in all_data:
            print(data['URL'])
        print(f"\nTotal unique URLs found: {len(urls)}")
        
        # Save to CSV using pandas
        df = pd.DataFrame(all_data)
        df.to_csv('search_4.csv', index=False)
        print("\nData saved to 'google_maps_data.csv'")
        
        # Alternative: Save to CSV using csv module
        with open('search_3.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['URL'])
            writer.writeheader()
            writer.writerows(all_data)
        
        # Return the list of data
        return all_data
        
    except TimeoutException:
        print("Timeout waiting for element")
    except NoSuchElementException:
        print("Element not found")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        driver.quit()
        
    return []

if __name__ == "__main__":
    # Execute the scraping and store results
    results = scroll_google_maps()
    
    # Print the results as a list
    print("\nResults as a list:")
    print(results)
    
    # You can also access specific URLs from the results
    print("\nAccessing individual URLs:")
    for idx, result in enumerate(results):
        print(f"URL {idx + 1}: {result['URL']}") 






















