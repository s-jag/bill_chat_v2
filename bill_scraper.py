import os
import re
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Ensure directory exists
os.makedirs("data/bills", exist_ok=True)

# Bill type mapping
type_mapping = {
    "hr": "house-bill",
    "hres": "house-resolution",
    "hjres": "house-joint-resolution",
    "hcres": "house-concurrent-resolution",
    "hconres": "house-concurrent-resolution",
    "s": "senate-bill",
    "sres": "senate-resolution",
    "sjres": "senate-joint-resolution",
    "scres": "senate-concurrent-resolution",
    "sconres": "senate-concurrent-resolution"
}

# List of bill IDs to scrape
bill_ids = [
    "hr-22-119", "hconres-14-119", "hjres-20-119", "hr-1228-119", "hr-1526-119", 
    "sjres-18-119", "sjres-28-119", "hres-313-119", "hres-294-119", "hr-1039-119", 
    "hr-586-119", "sjres-26-119", "sjres-33-119", "hjres-24-119", "sjres-37-119", 
    "hr-1491-119", "hres-282-119", "hr-997-119", "hr-517-119", "hr-1048-119", 
    "hjres-75-119", "hjres-25-119", "hres-242-119", "hr-1534-119", "hr-1326-119", 
    "hr-359-119", "hr-1968-119", "s-331-119", "hr-1156-119", "hres-211-119", 
    "hr-993-119", "hr-901-119", "hr-495-119", "hres-189-119", "sjres-11-119", 
    "hjres-42-119", "hjres-61-119", "sjres-3-119", "hres-177-119", "hr-758-119", 
    "hr-856-119", "s-9-119", "hjres-35-119", "sjres-12-119", "sjres-10-119", 
    "hr-695-119", "hr-804-119", "hr-788-119", "hres-161-119", "hr-818-119", 
    "hr-832-119", "hr-825-119", "sconres-7-119", "hr-35-119", "hr-77-119", 
    "hres-122-119", "hr-736-119", "hr-692-119", "hr-26-119", "hr-27-119", 
    "hres-93-119", "hr-776-119", "hr-43-119", "hr-23-119", "hr-21-119", 
    "hr-471-119", "hr-375-119", "s-5-119", "hr-165-119", "s-6-119", 
    "hres-53-119", "hr-187-119", "hr-186-119", "hr-30-119", "hr-33-119", "hr-144-119"
]

# Remove duplicates to avoid redundant scraping
unique_bill_ids = list(set(bill_ids))
print(f"Found {len(unique_bill_ids)} unique bills to scrape")

def initialize_driver():
    """Initialize and return a headless Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    # Add a realistic user agent
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_bill_text(driver, bill_id):
    """Scrape bill text using Selenium WebDriver"""
    # Parse bill ID components
    match = re.match(r"([a-zA-Z]+)-([0-9]+)-([0-9]+)", bill_id)
    if not match:
        print(f"Invalid bill ID format: {bill_id}")
        return None

    bill_type, bill_number, congress = match.groups()
    
    # Get the type string for URL
    type_string = type_mapping.get(bill_type.lower())
    if not type_string:
        print(f"Unknown bill type: {bill_type}")
        return None
    
    # Try different URL formats
    urls_to_try = [
        f"https://www.congress.gov/bill/{congress}th-congress/{type_string}/{bill_number}/text/enr?format=txt",
        f"https://www.congress.gov/bill/{congress}th-congress/{type_string}/{bill_number}/text?format=txt",
        f"https://www.congress.gov/bill/{congress}th-congress/{type_string}/{bill_number}/text/rfs?format=txt"
    ]
    
    for url in urls_to_try:
        print(f"Trying to scrape {bill_id} from {url}")
        
        try:
            # Navigate to the URL
            driver.get(url)
            
            # Wait for the page to load (max 10 seconds)
            wait = WebDriverWait(driver, 10)
            
            try:
                # Wait for the pre tag to be present
                pre_element = wait.until(EC.presence_of_element_located((By.TAG_NAME, "pre")))
                
                # Get the text content
                text_content = pre_element.text
                
                if text_content:
                    print(f"Successfully scraped {bill_id}")
                    return text_content
                    
            except TimeoutException:
                print(f"Timeout waiting for content on {url}")
                # Try the next URL
                continue
                
        except Exception as e:
            print(f"Error accessing {url}: {e}")
            # Try the next URL
            continue
    
    # If we've tried all URLs and none worked
    print(f"Failed to scrape {bill_id} from any URL")
    return None

# Main script execution
try:
    # Initialize WebDriver
    driver = initialize_driver()
    
    for bill_id in unique_bill_ids:
        # Check if file already exists
        output_path = Path(f"data/bills/{bill_id}.txt")
        
        if output_path.exists():
            print(f"File already exists for {bill_id}, skipping")
            continue
        
        # Scrape bill text
        bill_text = scrape_bill_text(driver, bill_id)
        
        if bill_text:
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(bill_text)
            print(f"Saved {bill_id} text to {output_path}")
        else:
            print(f"Failed to scrape {bill_id}")
        
        # Add delay to avoid hitting rate limits
        time.sleep(2)
    
    print("Scraping completed")

finally:
    # Always close the driver
    if 'driver' in locals():
        driver.quit()
        print("WebDriver closed") 