from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import json
import logging
from datetime import datetime
import os
from tqdm import tqdm

class PumpFunScraper:
    def __init__(self):
        self.url = "https://pump.fun/board"
        self.setup_logger()
        
    def setup_logger(self):
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Setup logger
        self.logger = logging.getLogger('PumpFunScraper')
        self.logger.setLevel(logging.DEBUG)
        
        # Create handlers
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # File handler for debug logs
        debug_handler = logging.FileHandler(f'logs/debug_{timestamp}.log')
        debug_handler.setLevel(logging.DEBUG)
        
        # File handler for errors
        error_handler = logging.FileHandler(f'logs/error_{timestamp}.log')
        error_handler.setLevel(logging.ERROR)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatters and add it to handlers
        debug_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        simple_format = logging.Formatter('%(levelname)s - %(message)s')
        
        debug_handler.setFormatter(debug_format)
        error_handler.setFormatter(debug_format)
        console_handler.setFormatter(simple_format)
        
        # Add handlers to the logger
        self.logger.addHandler(debug_handler)
        self.logger.addHandler(error_handler)
        self.logger.addHandler(console_handler)
        
    def scrape_tokens(self):
        print("🚀 Starting the scraper...")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        print("🌐 Initializing Chrome driver...")
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        tokens = []
        try:
            print(f"📫 Accessing URL: {self.url}")
            driver.get(self.url)
            
            # Handle popups before proceeding
            self.handle_popups(driver)
            
            print("⏳ Waiting for content to load...")
            print(f"📄 Page title: {driver.title}")
            
            try:
                print("🔍 Looking for token grid...")
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "grid-cols-1"))
                )
            except Exception as e:
                print(f"⚠️ Warning: Grid not found: {str(e)}")
                driver.save_screenshot("debug_screenshot.png")
                print("📸 Saved debug screenshot to debug_screenshot.png")
            
            print("⌛ Allowing extra time for dynamic content...")
            time.sleep(5)
            
            page_source = driver.page_source
            print(f"📝 Page source length: {len(page_source)} characters")
            
            print("🔎 Parsing content...")
            soup = BeautifulSoup(page_source, 'html.parser')
            
            token_cards = soup.find_all('div', class_=lambda x: x and ('token-card' in x.lower() or 'grid' in x.lower()))
            print(f"🎯 Found {len(token_cards)} potential token cards")
            
            if not token_cards:
                print("⚠️ No token cards found. Dumping HTML structure:")
                print(soup.prettify()[:1000])
            
            for index, card in enumerate(tqdm(token_cards, desc="Processing tokens")):
                try:
                    token = {
                        'name': self._extract_text(card, '.token-name'),
                        'symbol': self._extract_text(card, '.token-symbol'),
                        'creator': self._extract_creator(card),
                        'time_created': self._extract_time(card),
                        'market_cap': self._extract_market_cap(card),
                        'replies_count': self._extract_replies(card),
                        'description': self._extract_description(card),
                        'social_links': self._extract_social_links(card)
                    }
                    if any(token.values()):
                        tokens.append(token)
                        print(f"✅ Successfully processed token {index + 1}")
                    else:
                        print(f"⚠️ No data found for token {index + 1}")
                except Exception as e:
                    print(f"❌ Error processing token {index + 1}: {str(e)}")
                    
        except Exception as e:
            print(f"❌ Error during scraping: {str(e)}")
            self.logger.error(f"Scraping error: {str(e)}", exc_info=True)
        finally:
            print("🔄 Closing browser...")
            driver.quit()
            
        return tokens

    def handle_popups(self, driver):
        try:
            print("🔍 Checking for popups...")
            
            # Handle "how it works" popup
            try:
                ready_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'ready to pump')]"))
                )
                print("📌 Found 'ready to pump' button")
                ready_button.click()
                print("✅ Closed 'how it works' popup")
            except Exception as e:
                print(f"ℹ️ No 'how it works' popup found or unable to close: {str(e)}")

            # Handle cookie settings popup
            try:
                accept_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept All')]"))
                )
                print("📌 Found 'Accept All' button")
                accept_button.click()
                print("✅ Closed cookie settings popup")
            except Exception as e:
                print(f"ℹ️ No cookie popup found or unable to close: {str(e)}")

            # Wait a moment for popups to clear
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠️ Error handling popups: {str(e)}")

    def _extract_text(self, card, selector):
        try:
            element = card.select_one(selector)
            return element.text.strip() if element else None
        except Exception as e:
            self.logger.error(f"Error extracting text with selector {selector}: {str(e)}")
            return None

    def _extract_creator(self, card):
        try:
            creator_elem = card.find(text=lambda t: t and 'created by' in t.lower())
            if creator_elem:
                return creator_elem.split('created by')[-1].strip()
            return None
        except Exception as e:
            self.logger.error(f"Error extracting creator: {str(e)}")
            return None

    def _extract_time(self, card):
        try:
            time_elem = card.find(text=lambda t: t and ('ago' in t.lower()))
            return time_elem.strip() if time_elem else None
        except Exception as e:
            self.logger.error(f"Error extracting time: {str(e)}")
            return None

    def _extract_market_cap(self, card):
        try:
            market_cap_elem = card.find(text=lambda t: t and 'market cap' in t.lower())
            if market_cap_elem:
                return market_cap_elem.split(':')[-1].strip()
            return None
        except Exception as e:
            self.logger.error(f"Error extracting market cap: {str(e)}")
            return None

    def _extract_replies(self, card):
        try:
            replies_elem = card.find(text=lambda t: t and 'replies' in t.lower())
            if replies_elem:
                return replies_elem.split()[0].strip()
            return None
        except Exception as e:
            self.logger.error(f"Error extracting replies: {str(e)}")
            return None

    def _extract_description(self, card):
        try:
            desc_elem = card.find('div', class_=lambda x: x and 'description' in x.lower())
            return desc_elem.text.strip() if desc_elem else None
        except Exception as e:
            self.logger.error(f"Error extracting description: {str(e)}")
            return None

    def _extract_social_links(self, card):
        try:
            social_links = {}
            links = card.find_all('a', href=True)
            
            for link in links:
                href = link['href']
                if 'twitter.com' in href:
                    social_links['twitter'] = href
                elif 't.me' in href or 'telegram.org' in href:
                    social_links['telegram'] = href
                elif 'discord.com' in href:
                    social_links['discord'] = href
            
            return social_links
        except Exception as e:
            self.logger.error(f"Error extracting social links: {str(e)}")
            return {}

def main():
    print("=" * 50)
    print("🤖 PumpFun Scraper Starting")
    print("=" * 50)
    
    scraper = PumpFunScraper()
    tokens = scraper.scrape_tokens()
    
    if tokens:
        output_file = 'pump_fun_tokens.json'
        print(f"💾 Saving {len(tokens)} tokens to {output_file}")
        
        try:
            with open(output_file, 'w') as f:
                json.dump(tokens, f, indent=2)
            print("✅ Data successfully saved!")
            
            print("\n📊 Sample token data:")
            print(json.dumps(tokens[0], indent=2))
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")
    else:
        print("⚠️ No tokens were scraped")
    
    print("=" * 50)
    print("🏁 Scraping completed")
    print("=" * 50)

if __name__ == "__main__":
    main()