import re

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

# Test URLs
test_urls = [
    "https://www.google.com/maps/place/IELTS+Coaching/data=!4m7!3m6!1s0x390cfdc986a3a7bd:0x4a4982d184f40d72!8m2!3d28.6291627!4d77.2249081!16s%2Fg%2F11h2l33jjp!19sChIJvaejhsn9DDkRcg30hNGCSUo?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/place/Delhi+-+Barakhamba+International+Education+Career+Launcher+Center/data=!4m7!3m6!1s0x390cfd6fad6e2917:0xa37a59502520406b!8m2!3d28.6296381!4d77.2257202!16s%2Fg%2F11tdtbzwyd!19sChIJFylurW_9DDkRa0AgJVBZeqM?authuser=0&hl=en&rclk=1",
    "https://www.google.com/maps/@28.6315,77.2167,15z",
    "https://www.google.com/maps/search/IELTS+Coaching/@28.6315,77.2167,13000m"
]

print("Testing coordinate extraction function:")
print("=" * 50)

for i, url in enumerate(test_urls, 1):
    print(f"\nTest {i}:")
    print(f"URL: {url[:80]}...")
    lat, lon = extract_coordinates_from_url(url)
    if lat and lon:
        print(f"Result: SUCCESS - Lat: {lat}, Lon: {lon}")
    else:
        print(f"Result: FAILED - No coordinates found")
