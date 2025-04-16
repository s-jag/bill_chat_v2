import os
import time
import re
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Ensure directory exists
os.makedirs("data/executive_orders", exist_ok=True)

# Firebase credentials
firebase_creds_name = "poli-ddedb-firebase-adminsdk-ch6ct-3b65358a27.json"

def initialize_firebase():
    """Initialize Firebase and return Firestore client"""
    cred = credentials.Certificate(firebase_creds_name)
    firebase_admin.initialize_app(cred)
    return firestore.client()

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

def scrape_executive_order(driver, url, document_number):
    """Scrape executive order text using Selenium WebDriver"""
    print(f"Scraping executive order {document_number} from {url}")
    
    try:
        # Navigate to the URL
        driver.get(url)
        
        # Wait for the page to load (max 10 seconds)
        wait = WebDriverWait(driver, 10)
        
        try:
            # Wait for the content to be present - adjust selector as needed for Federal Register
            # For federal register full text HTML, the content is inside a div with class "body-content"
            content_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".body-content")))
            
            # Get the text content
            text_content = content_element.text
            
            if text_content:
                print(f"Successfully scraped executive order {document_number}")
                return text_content
                
        except TimeoutException:
            print(f"Timeout waiting for content on {url}")
            # Try to get whatever text is on the page
            try:
                # Get the body text as a fallback
                body_text = driver.find_element(By.TAG_NAME, "body").text
                if body_text:
                    print(f"Retrieved body text for {document_number}")
                    return body_text
            except:
                pass
            
    except Exception as e:
        print(f"Error accessing {url}: {e}")
    
    print(f"Failed to scrape executive order {document_number}")
    return None

def get_executive_orders_from_firebase():
    """Get all executive orders from Firebase"""
    db = initialize_firebase()
    exec_orders = []
    
    # Get all documents from the executive_orders collection
    collection_name = "executive_orders"
    docs = db.collection(collection_name).stream()
    
    for doc in docs:
        data = doc.to_dict()
        if 'document_number' in data and 'body_html_url' in data:
            exec_orders.append({
                'document_number': data['document_number'],
                'body_html_url': data['body_html_url'],
                'title': data.get('title', '')
            })
    
    print(f"Retrieved {len(exec_orders)} executive orders from Firebase")
    return exec_orders

# Main script execution
try:
    # Initialize WebDriver
    driver = initialize_driver()
    
    # Get executive orders from Firebase
    exec_orders = get_executive_orders_from_firebase()
    
    for order in exec_orders:
        document_number = order['document_number']
        url = order['body_html_url']
        
        # Check if file already exists
        output_path = Path(f"data/executive_orders/{document_number}.txt")
        
        if output_path.exists():
            print(f"File already exists for {document_number}, skipping")
            continue
        
        # Scrape executive order text
        order_text = scrape_executive_order(driver, url, document_number)
        
        if order_text:
            # Save to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(order_text)
            print(f"Saved {document_number} text to {output_path}")
        else:
            print(f"Failed to scrape {document_number}")
        
        # Add delay to avoid hitting rate limits
        time.sleep(2)
    
    print("Scraping completed")

finally:
    # Always close the driver
    if 'driver' in locals():
        driver.quit()
        print("WebDriver closed") 