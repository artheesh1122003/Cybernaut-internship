import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class IMDbScraper:
    def __init__(self, headless=True):
        self.url = "https://www.imdb.com/chart/top/"
        
        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
        chrome_options.add_argument("--accept-lang=en-US,en;q=0.9")
        
        # Initialize WebDriver
        logging.info("Initializing Chrome WebDriver...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def scrape_top_movies(self, limit=250):
        logging.info(f"Navigating to {self.url}")
        self.driver.get(self.url)
        
        try:
            # We need to wait for the movie list to load
            wait = WebDriverWait(self.driver, 15)
            
            # Scrolling down slightly to help load dynamics list
            self.driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(2)
            self.driver.execute_script("window.scrollBy(0, 2000);")
            time.sleep(2)
            
            # The list items currently have the class 'ipc-metadata-list-summary-item'
            items = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.ipc-metadata-list-summary-item")))
            logging.info(f"Found {len(items)} movies on the page.")
            
            movies_data = []
            
            for item in items[:limit]:
                try:
                    # Title element typically contains text like "1. The Shawshank Redemption"
                    title_element = item.find_element(By.CSS_SELECTOR, "h3.ipc-title__text")
                    title_text = title_element.text.strip()
                    
                    # Splitting rank and name
                    if ". " in title_text:
                        rank, name = title_text.split(". ", 1)
                    else:
                        rank = len(movies_data) + 1
                        name = title_text
                        
                    # Year, Duration, Age rating are typically in span under a div with class containing cli-title-metadata
                    metadata_elements = item.find_elements(By.CSS_SELECTOR, "div.cli-title-metadata span.cli-title-metadata-item")
                    year = metadata_elements[0].text.strip() if metadata_elements else "N/A"
                    
                    # Rating is usually in an element with class containing ipc-rating-star
                    rating_element = item.find_element(By.CSS_SELECTOR, "span.ipc-rating-star")
                    rating_text = rating_element.get_attribute('aria-label')
                    if rating_text:
                        # e.g., "IMDb rating: 9.3"
                        rating_text = rating_text.replace("IMDb rating: ", "").strip()
                    else:
                        rating_text = rating_element.text.strip().split("\n")[0]
                    
                    movies_data.append({
                        "Rank": rank,
                        "Movie Name": name,
                        "Release Year": year,
                        "IMDb Rating": rating_text
                    })
                except Exception as e:
                    logging.warning(f"Error scraping a movie item: {e}")
                    continue
                    
            return movies_data
            
        except Exception as e:
            logging.error(f"Error while waiting for page to load: {e}")
            return []
            
    def close(self):
        logging.info("Closing WebDriver.")
        self.driver.quit()

def main():
    print("=== IMDb Top 250 Movies Scraper ===")
    scraper = IMDbScraper(headless=True)
    
    try:
        movies = scraper.scrape_top_movies(limit=250)
        
        if movies:
            df = pd.DataFrame(movies)
            output_file = "imdb_top_movies.csv"
            df.to_csv(output_file, index=False, encoding='utf-8')
            
            print(f"\nSuccessfully scraped {len(df)} movies!")
            print(f"Data saved to '{output_file}'")
            print("\nPreview of the data:")
            print(df.head())
        else:
            print("\nFailed to retrieve movie data.")
            
    finally:
        scraper.close()

if __name__ == "__main__":
    main()
