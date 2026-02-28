import re
import math
import csv
import time
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, List, Set
from dataclasses import dataclass
from contextlib import contextmanager

import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('maps_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SCROLL_PAUSE_TIME = 2
MAX_SCROLL_ATTEMPTS = 10
DISTANCE_THRESHOLD_KM = 7
EARTH_RADIUS_KM = 6371
SEARCH_RADIUS_METERS = 13000

# CSS Selectors
SCROLLABLE_SELECTORS = [
    "div.m6QErb.DxyBCb.kA9KIf.dS8AEf.ecceSd",
    "div[role='main']",
    "div.siAUzd",
    "div.m6QErb"
]

PLACE_SELECTORS = [
    "a[href*='maps/place']",
    "a[data-value*='maps/place']",
    "a[href*='/place/']",
    "div[data-result-index] a",
    ".hfpxzc"
]

@dataclass
class PlaceData:
    """Data class to store place information"""
    search_item: str
    search_lat: float
    search_lon: float
    url: str
    url_lat: Optional[float] = None
    url_lon: Optional[float] = None
    distance_km: Optional[float] = None
    within_7km: str = "NO"

class MapsScraperError(Exception):
    """Custom exception for Maps Scraper errors"""
    pass

class CoordinateExtractor:
    """Handles coordinate extraction from Google Maps URLs"""
    
    @staticmethod
    def extract_coordinates_from_url(url: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Extract latitude and longitude coordinates from Google Maps URL
        
        Args:
            url (str): Google Maps URL containing coordinates
            
        Returns:
            tuple: (latitude, longitude) as floats, or (None, None) if not found
        """
        try:
            # Primary pattern: 3d(lat) and 4d(lon)
            lat_pattern = r'3d([+-]?\d+\.?\d*)'
            lng_pattern = r'4d([+-]?\d+\.?\d*)'
            
            lat_match = re.search(lat_pattern, url)
            lng_match = re.search(lng_pattern, url)
            
            if lat_match and lng_match:
                latitude = float(lat_match.group(1))
                longitude = float(lng_match.group(1))
                logger.debug(f"Coordinates extracted: {latitude}, {longitude}")
                return latitude, longitude
            
            # Fallback pattern: @lat,lon
            fallback_match = re.search(r'/@([-+]?\d+\.\d+),([-+]?\d+\.\d+)', url)
            if fallback_match:
                latitude = float(fallback_match.group(1))
                longitude = float(fallback_match.group(2))
                logger.debug(f"Coordinates extracted (fallback): {latitude}, {longitude}")
                return latitude, longitude
            
            logger.warning(f"No coordinates found in URL: {url[:50]}...")
            return None, None
            
        except (ValueError, AttributeError) as e:
            logger.error(f"Error extracting coordinates from URL: {str(e)}")
            return None, None

class DistanceCalculator:
    """Handles distance calculations using Haversine formula"""
    
    @staticmethod
    def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on earth
        
        Args:
            lat1, lon1: Latitude and longitude of point 1 in degrees
            lat2, lon2: Latitude and longitude of point 2 in degrees
            
        Returns:
            float: Distance in kilometers
        """
        try:
            # Convert decimal degrees to radians
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            
            # Haversine formula
            a = (math.sin(dphi / 2) ** 2 +
                 math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
            
            return 2 * EARTH_RADIUS_KM * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            
        except (ValueError, TypeError) as e:
            logger.error(f"Error calculating distance: {str(e)}")
            raise MapsScraperError(f"Invalid coordinates for distance calculation: {str(e)}")

class URLManager:
    """Manages URL deduplication and CSV operations"""
    
    def __init__(self, all_urls_csv: str, filtered_csv: str):
        self.all_urls_csv = all_urls_csv
        self.filtered_csv = filtered_csv
        self.existing_urls: Set[str] = set()
        self._initialize_csv_files()
        self._load_existing_urls()
    
    def _initialize_csv_files(self) -> None:
        """Initialize CSV files with headers if they don't exist"""
        headers = [
            "search_item", "search_lat", "search_lon", "url",
            "url_lat", "url_lon", "distance_km", "within_7km"
        ]
        
        for csv_file in [self.all_urls_csv, self.filtered_csv]:
            if not Path(csv_file).exists():
                pd.DataFrame(columns=headers).to_csv(csv_file, index=False)
                logger.info(f"Created new CSV file: {csv_file}")
    
    def _load_existing_urls(self) -> None:
        """Load existing URLs from both CSV files to avoid duplicates"""
        for csv_file, description in [(self.all_urls_csv, "all URLs"), (self.filtered_csv, "filtered URLs")]:
            try:
                if Path(csv_file).exists():
                    df = pd.read_csv(csv_file)
                    if 'url' in df.columns:
                        urls = set(df['url'].dropna())
                        self.existing_urls.update(urls)
                        logger.info(f"Loaded {len(urls)} existing {description}")
                    else:
                        logger.warning(f"No 'url' column found in {csv_file}")
            except Exception as e:
                logger.error(f"Error reading {csv_file}: {str(e)}")
        
        logger.info(f"Total unique URLs already processed: {len(self.existing_urls)}")
    
    def is_duplicate(self, url: str) -> bool:
        """Check if URL has already been processed"""
        return url in self.existing_urls
    
    def add_url(self, url: str) -> None:
        """Add URL to the set of processed URLs"""
        self.existing_urls.add(url)
    
    def save_place_data(self, place_data: PlaceData) -> None:
        """Save place data to appropriate CSV files"""
        try:
            # Convert to dictionary for DataFrame creation
            data_dict = {
                "search_item": place_data.search_item,
                "search_lat": place_data.search_lat,
                "search_lon": place_data.search_lon,
                "url": place_data.url,
                "url_lat": place_data.url_lat,
                "url_lon": place_data.url_lon,
                "distance_km": place_data.distance_km,
                "within_7km": place_data.within_7km
            }
            
            # Save to all URLs CSV
            pd.DataFrame([data_dict]).to_csv(self.all_urls_csv, mode='a', header=False, index=False)
            
            # Save to filtered CSV if within threshold
            if place_data.within_7km == "YES":
                pd.DataFrame([data_dict]).to_csv(self.filtered_csv, mode='a', header=False, index=False)
                
        except Exception as e:
            logger.error(f"Error saving place data: {str(e)}")
            raise MapsScraperError(f"Failed to save place data: {str(e)}")

@contextmanager
def webdriver_context(headless: bool = False):
    """Context manager for WebDriver lifecycle"""
    driver = None
    try:
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        driver = uc.Chrome(options=options)
        yield driver
    except Exception as e:
        logger.error(f"WebDriver error: {str(e)}")
        raise MapsScraperError(f"WebDriver initialization failed: {str(e)}")
    finally:
        if driver:
            driver.quit()

class MapsScraper:
    """Main class for scraping Google Maps places"""
    
    def __init__(self, url_manager: URLManager):
        self.url_manager = url_manager
        self.coordinate_extractor = CoordinateExtractor()
        self.distance_calculator = DistanceCalculator()
    
    def _find_scrollable_element(self, driver) -> Optional:
        """Find the scrollable element on the page"""
        for selector in SCROLLABLE_SELECTORS:
            try:
                element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                logger.debug(f"Found scrollable div with selector: {selector}")
                return element
            except TimeoutException:
                continue
        return None
    
    def _find_place_elements(self, driver) -> List:
        """Find all place elements on the page"""
        places = []
        for selector in PLACE_SELECTORS:
            try:
                found_places = driver.find_elements(By.CSS_SELECTOR, selector)
                if found_places:
                    places.extend(found_places)
                    logger.debug(f"Found {len(found_places)} places with selector: {selector}")
            except Exception as e:
                logger.warning(f"Error with selector {selector}: {str(e)}")
        
        # Remove duplicates based on href
        unique_places = []
        seen_hrefs = set()
        for place in places:
            href = place.get_attribute("href")
            if href and href not in seen_hrefs:
                unique_places.append(place)
                seen_hrefs.add(href)
        
        return unique_places
    
    def _process_place(self, place, search_item: str, search_lat: float, search_lon: float) -> Optional[PlaceData]:
        """Process a single place element"""
        url = place.get_attribute("href")
        if not url:
            return None
        
        # Check for duplicates
        if self.url_manager.is_duplicate(url):
            logger.debug(f"Skipping duplicate URL: {url[:50]}...")
            return None
        
        # Extract coordinates
        url_lat, url_lon = self.coordinate_extractor.extract_coordinates_from_url(url)
        if url_lat is None or url_lon is None:
            logger.warning(f"Skipping URL - coordinates not found: {url[:50]}...")
            return None
        
        # Calculate distance
        try:
            distance = self.distance_calculator.haversine(search_lat, search_lon, url_lat, url_lon)
            within_7km = "YES" if distance <= DISTANCE_THRESHOLD_KM else "NO"
            
            place_data = PlaceData(
                search_item=search_item,
                search_lat=search_lat,
                search_lon=search_lon,
                url=url,
                url_lat=url_lat,
                url_lon=url_lon,
                distance_km=round(distance, 2),
                within_7km=within_7km
            )
            
            self.url_manager.add_url(url)
            return place_data
            
        except MapsScraperError as e:
            logger.error(f"Error processing place: {str(e)}")
            return None
    
    def _scroll_page(self, driver, scrollable_element) -> None:
        """Scroll the page to load more results"""
        try:
            if scrollable_element:
                driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_element)
            else:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        except Exception as e:
            logger.warning(f"Error scrolling: {str(e)}")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    
    def scrape_places(self, search_item: str, search_lat: float, search_lon: float, 
                     headless: bool = False) -> List[PlaceData]:
        """
        Scrape all places for a given search term and location
        
        Args:
            search_item: Search term
            search_lat: Search center latitude
            search_lon: Search center longitude
            headless: Whether to run browser in headless mode
            
        Returns:
            List of PlaceData objects
        """
        places_data = []
        processed_urls = set()
        
        with webdriver_context(headless=headless) as driver:
            try:
                query = f'https://www.google.com/maps/search/"{search_item}"/@{search_lat},{search_lon},{SEARCH_RADIUS_METERS}m'
                logger.info(f"Loading: {query}")
                driver.get(query)
                time.sleep(DEFAULT_SCROLL_PAUSE_TIME)
                
                scroll_attempts = 0
                new_urls_count = 0
                
                while scroll_attempts < MAX_SCROLL_ATTEMPTS:
                    # Find scrollable element
                    scrollable_element = self._find_scrollable_element(driver)
                    
                    # Find place elements
                    places = self._find_place_elements(driver)
                    logger.info(f"Scroll {scroll_attempts + 1}/{MAX_SCROLL_ATTEMPTS}: Found {len(places)} unique place elements")
                    
                    # Process places
                    new_urls_this_scroll = 0
                    for place in places:
                        url = place.get_attribute("href")
                        if url and url not in processed_urls:
                            processed_urls.add(url)
                            place_data = self._process_place(place, search_item, search_lat, search_lon)
                            
                            if place_data:
                                places_data.append(place_data)
                                self.url_manager.save_place_data(place_data)
                                new_urls_this_scroll += 1
                                new_urls_count += 1
                                
                                logger.info(f"Processed URL #{new_urls_count}: {url[:50]}... "
                                          f"Distance: {place_data.distance_km} km "
                                          f"Within 7km: {place_data.within_7km}")
                    
                    logger.info(f"New URLs this scroll: {new_urls_this_scroll}")
                    
                    # Check if we should continue scrolling
                    if new_urls_this_scroll == 0:
                        logger.info("No new URLs found, continuing to scroll...")
                    
                    # Scroll down
                    self._scroll_page(driver, scrollable_element)
                    time.sleep(DEFAULT_SCROLL_PAUSE_TIME)
                    scroll_attempts += 1
                
                logger.info(f"Search '{search_item}' completed: {new_urls_count} new URLs processed")
                return places_data
                
            except Exception as e:
                logger.error(f"Error during scraping: {str(e)}")
                raise MapsScraperError(f"Scraping failed for '{search_item}': {str(e)}")

class InputValidator:
    """Validates input data and parameters"""
    
    @staticmethod
    def validate_coordinates(lat: any, lon: any) -> Tuple[Optional[float], Optional[float]]:
        """Validate and convert coordinates to float"""
        try:
            if pd.isna(lat) or pd.isna(lon):
                return None, None
            return float(lat), float(lon)
        except (ValueError, TypeError):
            return None, None
    
    @staticmethod
    def validate_input_file(input_csv: str) -> pd.DataFrame:
        """Validate input CSV file and return DataFrame"""
        if not Path(input_csv).exists():
            raise MapsScraperError(f"Input file '{input_csv}' not found")
        
        try:
            df = pd.read_csv(input_csv)
        except Exception as e:
            raise MapsScraperError(f"Error reading input file: {str(e)}")
        
        # Validate required columns
        required_columns = ['search_item', 'latitude', 'longitude']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise MapsScraperError(f"Missing required columns: {missing_columns}")
        
        return df

def main():
    """Main function to run the scraper"""
    input_csv = "maps_results.csv"
    output_csv = "filtered_places.csv"
    all_urls_csv = "all_scraped_urls.csv"
    
    try:
        # Validate input
        df = InputValidator.validate_input_file(input_csv)
        
        # Initialize components
        url_manager = URLManager(all_urls_csv, output_csv)
        scraper = MapsScraper(url_manager)
        
        logger.info("Starting scraping process...")
        logger.info(f"Output files: {all_urls_csv} (all URLs), {output_csv} (filtered URLs)")
        
        total_scraped = 0
        total_filtered = 0
        
        # Process each search item
        for _, row in df.iterrows():
            search_item = row['search_item']
            
            # Validate coordinates
            search_lat, search_lon = InputValidator.validate_coordinates(
                row['latitude'], row['longitude']
            )
            
            if search_lat is None or search_lon is None:
                logger.warning(f"Skipping '{search_item}' - Invalid coordinates: "
                             f"lat={row['latitude']}, lon={row['longitude']}")
                continue
            
            logger.info(f"\nSearching for: {search_item}")
            logger.info(f"Search center: {search_lat}, {search_lon}")
            
            # Scrape places
            try:
                places_data = scraper.scrape_places(search_item, search_lat, search_lon)
                
                # Count filtered results
                filtered_count = sum(1 for place in places_data if place.within_7km == 'YES')
                
                total_scraped += len(places_data)
                total_filtered += filtered_count
                
                logger.info(f"Found {filtered_count} places within 7 km "
                           f"(out of {len(places_data)} total NEW places)")
                
            except MapsScraperError as e:
                logger.error(f"Failed to scrape '{search_item}': {str(e)}")
                continue
        
        # Final summary
        logger.info("\nFINAL SUMMARY:")
        logger.info(f"   - Total URLs scraped: {total_scraped}")
        logger.info(f"   - URLs within 7 km: {total_filtered}")
        if total_scraped > 0:
            logger.info(f"   - Filtering efficiency: {total_filtered/total_scraped*100:.1f}%")
        logger.info(f"   - All URLs saved to: {all_urls_csv}")
        logger.info(f"   - Filtered URLs saved to: {output_csv}")
        
        # Warnings for edge cases
        if total_scraped == 0:
            logger.warning("\nNo URLs were scraped. Please check:")
            logger.warning("   1. Internet connection")
            logger.warning("   2. Google Maps page structure hasn't changed")
            logger.warning("   3. CSS selectors are still valid")
        elif total_filtered == 0:
            logger.warning("\nNo results found within 7 km. Consider:")
            logger.warning("   1. Increasing the distance threshold")
            logger.warning("   2. Checking if search coordinates are correct")
            logger.warning("   3. Verifying the search area has relevant places")
        
    except MapsScraperError as e:
        logger.error(f"Application error: {str(e)}")
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()