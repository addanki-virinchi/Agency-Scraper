import pandas as pd
import os

def test_deduplication():
    """Test the deduplication functionality"""
    
    # Create sample CSV files with some existing URLs
    all_urls_csv = "test_all_scraped_urls.csv"
    filtered_csv = "test_filtered_places.csv"
    
    # Sample existing data
    existing_data = [
        {
            "search_item": "Test Search 1",
            "search_lat": 28.6315,
            "search_lon": 77.2167,
            "url": "https://www.google.com/maps/place/Test+Place+1/data=!4m7!3m6!1s0x123:0x456!8m2!3d28.6291627!4d77.2249081",
            "url_lat": 28.6291627,
            "url_lon": 77.2249081,
            "distance_km": 2.5,
            "within_7km": "YES"
        },
        {
            "search_item": "Test Search 1", 
            "search_lat": 28.6315,
            "search_lon": 77.2167,
            "url": "https://www.google.com/maps/place/Test+Place+2/data=!4m7!3m6!1s0x789:0xabc!8m2!3d28.6296381!4d77.2257202",
            "url_lat": 28.6296381,
            "url_lon": 77.2257202,
            "distance_km": 8.2,
            "within_7km": "NO"
        }
    ]
    
    # Create test CSV files
    df_all = pd.DataFrame(existing_data)
    df_all.to_csv(all_urls_csv, index=False)
    
    # Filtered CSV should only have URLs within 7km
    df_filtered = df_all[df_all['within_7km'] == 'YES']
    df_filtered.to_csv(filtered_csv, index=False)
    
    print(f"✅ Created test files:")
    print(f"   - {all_urls_csv}: {len(df_all)} URLs")
    print(f"   - {filtered_csv}: {len(df_filtered)} URLs")
    
    # Test the load_existing_urls function
    from Improved import load_existing_urls
    
    existing_urls = load_existing_urls(all_urls_csv, filtered_csv)
    
    print(f"\n🔍 Deduplication test results:")
    print(f"   - Total unique URLs loaded: {len(existing_urls)}")
    print(f"   - Expected: 2 unique URLs")
    print(f"   - Test result: {'✅ PASS' if len(existing_urls) == 2 else '❌ FAIL'}")
    
    # Test specific URLs
    expected_urls = {
        "https://www.google.com/maps/place/Test+Place+1/data=!4m7!3m6!1s0x123:0x456!8m2!3d28.6291627!4d77.2249081",
        "https://www.google.com/maps/place/Test+Place+2/data=!4m7!3m6!1s0x789:0xabc!8m2!3d28.6296381!4d77.2257202"
    }
    
    print(f"\n📋 URL verification:")
    for url in expected_urls:
        if url in existing_urls:
            print(f"   ✅ Found: {url[:60]}...")
        else:
            print(f"   ❌ Missing: {url[:60]}...")
    
    # Clean up test files
    try:
        os.remove(all_urls_csv)
        os.remove(filtered_csv)
        print(f"\n🧹 Cleaned up test files")
    except Exception as e:
        print(f"\n⚠️ Error cleaning up: {str(e)}")

if __name__ == "__main__":
    test_deduplication()
