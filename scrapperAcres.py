import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import requests
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
URL = os.getenv('CUSTOM_URL')
MAX_SCROLLS = int(os.getenv('MAX_LISTINGS'))
# Setup Selenium

chrome_options = Options()
#chrome_options.add_argument("--headless") 
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
driver = webdriver.Chrome(service=Service(), options=chrome_options)    

driver.get(URL)

# Wait until at least one price container loads (this ensures full listing content)
try:
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.CLASS_NAME, "tupleNew__priceValWrap"))
    )
except Exception as e:
    print("Listings did not load properly:", e)
    driver.quit()
    exit()

#Scrolling Loop
SCROLL_PAUSE_TIME = 10
last_height = driver.execute_script("return document.body.scrollHeight")

for scroll_round in range(MAX_SCROLLS):
    # Scroll to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(random.uniform(1.5, 4))  # Random sleep

    # Wait for new content to load
    time.sleep(SCROLL_PAUSE_TIME)

    # Calculate new scroll height
    new_height = driver.execute_script("return document.body.scrollHeight")


    if new_height == last_height:
        # No more content loaded
        print("Reached end of listings.")
        break
    last_height = new_height
    print(f"Scroll {scroll_round + 1} complete...")


# Get full page source after JS has run
soup = BeautifulSoup(driver.page_source, "html.parser")

listings = soup.find_all("div", class_="tupleNew__contentWrap")

properties = []


for i, listing in enumerate(listings, 1):
    try:
        #Get Name
        name_elem = listing.select(".tupleNew__locationName.ellipsis")
        buildingName = name_elem[0].get_text(strip = True) if name_elem else "N/A"

        # Get price
        price_elem = listing.select_one(".tupleNew__priceValWrap span")
        price = price_elem.get_text(strip=True) if price_elem else "N/A"

        # Get price per sqft
        price_sqft_elem = listing.select_one(".tupleNew__perSqftWrap.ellipsis")
        price_per_sqft = price_sqft_elem.get_text(strip=True) if price_sqft_elem else "N/A"

        # Get area
        area_elem = listing.select("div.tupleNew__areaWrap .tupleNew__area1Type")
        super_built_area = area_elem[0].get_text(strip=True) if area_elem else "N/A"

        # Get BHK
        bhk = area_elem[1].get_text(strip=True) if len(area_elem) > 1 else "N/A"

        # Get highlights
        highlights_elems = listing.select("div.tupleNew__unitHighlightTxt")
        highlights = [hl.get_text(strip=True) for hl in highlights_elems]
        highlights_str = ", ".join(highlights) if highlights else "N/A"

        print(f"✔️  Listing {i}: {buildingName}— Price: {price}, Area: {super_built_area}, BHK: {bhk}")

        properties.append({
            "Building Name" : buildingName,
            "Price": price,
            "Price per sqft": price_per_sqft,
            "Area": super_built_area,
            "BHK": bhk,
            "Highlights": highlights_str
        })
    except Exception as e:
        print(f"❌  Skipped listing {i} due to error: {e}")

# Save results
df = pd.DataFrame(properties)
df.to_excel("99acres_properties.xlsx", index=False)
print("✅ Scraping complete. Data saved to '99acres_properties.xlsx'.")

driver.quit()
