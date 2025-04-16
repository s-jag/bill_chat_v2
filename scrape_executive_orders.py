#!/usr/bin/env python3

import os
import time
import re
import logging
from pathlib import Path
import firebase_admin
from firebase_admin import credentials, firestore
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_firebase():
    """Initialize Firebase and return Firestore client."""
    try:
        # Check if already initialized
        firebase_admin.get_app()
    except ValueError:
        # Initialize with service account
        cred = credentials.Certificate('poli-ddedb-firebase-adminsdk-ch6ct-3b65358a27.json')
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

def initialize_driver():
    """Initialize and return a configured Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Create a new Chrome driver
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(30)
    return driver

def scrape_executive_order(driver, url, document_number):
    """Scrape the text of an executive order from the given URL."""
    if not url:
        logger.error(f"No URL provided for document {document_number}")
        return None
    
    logger.info(f"Scraping executive order {document_number} from {url}")
    
    try:
        driver.get(url)
        
        # Wait for the content to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Get the main content
        content = driver.find_element(By.TAG_NAME, "body").text
        
        # Clean up the text
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content
    
    except TimeoutException:
        logger.error(f"Timeout while loading {url}")
        return None
    except WebDriverException as e:
        logger.error(f"WebDriver error for {url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        return None

def get_executive_orders_from_firebase(db):
    """Retrieve executive orders from Firestore."""
    try:
        orders = []
        orders_ref = db.collection('executive_orders')
        docs = orders_ref.stream()
        
        # Get the first document to examine structure
        first_doc = None
        for doc in docs:
            if first_doc is None:
                first_doc = doc
                logger.info(f"Sample document structure: {doc.to_dict()}")
            
            orders.append(doc.to_dict())
            
        logger.info(f"Retrieved {len(orders)} executive orders from Firebase")
        return orders
    except Exception as e:
        logger.error(f"Error retrieving executive orders: {e}")
        return []

def main():
    # Create output directory if it doesn't exist
    output_dir = Path('data/executive_orders')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize WebDriver
    driver = initialize_driver()
    
    try:
        # Get executive orders from Firebase
        db = initialize_firebase()
        executive_orders = get_executive_orders_from_firebase(db)
        
        if not executive_orders:
            logger.warning("No executive orders found in Firebase")
            return
        
        # Process each executive order
        for order in executive_orders:
            document_number = order.get('document_number')
            if not document_number:
                logger.warning(f"No document number found for order {order.get('id')}")
                continue
            
            # Create a safe filename
            safe_document_number = re.sub(r'[^\w\-\.]', '_', document_number)
            output_file = output_dir / f"{safe_document_number}.txt"
            
            # Skip if already processed
            if output_file.exists():
                logger.info(f"Skipping {document_number} - already processed")
                continue
            
            # Scrape the executive order text
            url = order.get('body_html_url')
            content = scrape_executive_order(driver, url, document_number)
            
            if content:
                # Save to file
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"Saved executive order {document_number} to {output_file}")
            else:
                logger.error(f"Failed to scrape executive order {document_number}")
            
            # Add a delay to avoid rate limiting
            time.sleep(2)
    
    finally:
        # Clean up
        driver.quit()
        logger.info("Driver closed")

if __name__ == "__main__":
    main() 