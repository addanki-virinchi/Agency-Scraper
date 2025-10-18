import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Load names from CSV
data = pd.read_csv('maps.csv')  # CSV should have a column named 'name'
names = data['name'].tolist()

# Initialize Chrome
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Open Google Maps
driver.get("https://www.google.com/maps")
time.sleep(3)

urls = []

for name in names:
    print(f"Searching for: {name}")
    
    # Find search box
    search_box = driver.find_element(By.ID, "searchboxinput")
    search_box.clear()
    search_box.send_keys(name)
    search_box.send_keys(Keys.ENTER)
    
    time.sleep(5)  # wait for results to load

    # Capture the URL of current search result
    current_url = driver.current_url
    urls.append({"name": name, "url": current_url})
    
    print(f"Collected: {current_url}")
    time.sleep(2)

# Save URLs to CSV
output = pd.DataFrame(urls)
output.to_csv("maps_results.csv", index=False)

driver.quit()
print("✅ Done! URLs saved to maps_results.csv")
