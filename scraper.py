import asyncio
import os
from datetime import datetime
# it is used to scrap async data using the playwright library
from playwright.async_api import async_playwright
# it is used to parse the html data(beautifulsoup used to parse the web scrap data)
from bs4 import BeautifulSoup
import json 
import re
from utils.config import Config, WorkflowState


class ContentScraper:
    def __init__(self, base_url = "https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1"):
        self.base_url = base_url
        self.screenshots_dir = "screenshots"
        self.content_dir = "content"

    # asynq keyword in python referes to the function can run asynqronously
    # with other fns
    async def setup_directories(self):
        """Create necessary directories"""
        os.makedirs(self.screenshots_dir, exist_ok=True)
        os.makedirs(self.content_dir, exist_ok=True)
        print("Directories created")

    def clean_text(self, text: str) -> str:
        """
        Remove HTML navigation artifacts like arrows, layout, and footnotes.
        """
        # Remove arrows and navigation cues
        text = re.sub(r"[←→]", "", text)
        
        # Remove layout references like "Layout 2"
        text = re.sub(r"Layout\s*\d+", "", text)

        # Remove footnote references like [1], [2], etc.
        text = re.sub(r"\[\d+\]", "", text)

        # Remove excessive whitespace
        text = re.sub(r"\s{2,}", " ", text).strip()

        text_content = re.sub(r"\[\s*\d+\s*\]", "", text)

        return text_content 

    async def scrape_content(self, state: WorkflowState) -> WorkflowState:
        """Scrape content and take screenshots, content"""
        async with async_playwright() as p:
            # launch the browser with now browser window
            # as we dont want to open browser window
            browser = await p.chromium.launch(headless=False)
            # opens the new page
            page = await browser.new_page()

            try:
                # navigate to the url
                await page.goto(self.base_url)
                # wait for the page to load
                # await lets it wait until the network idle state is reached. ro until fn executes
                await page.wait_for_load_state("networkidle")

                # take screenshot
                # format the time string
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                # define path of the screenshot
                screenshot_path = f"{self.screenshots_dir}/chapter_1_{timestamp}.png"
                # take the screenshot and save in the defined path
                await page.screenshot(path=screenshot_path, full_page=True)

                # Extract content
                # extract the content using oage content
                content = await page.content()
                # parse the html content using bs4
                soup = BeautifulSoup(content, 'html.parser')

                # Find the main content area
                main_content = soup.find('div', {'class': 'mw-parser-output'})
                
                if main_content:
                    text_content = self.clean_text(main_content.get_text(separator='\n', strip=True))

                    # save content
                    content_data = {
                        'url': self.base_url,
                        'timestamp': timestamp,
                        'title': 'The Gates of Morning - Book 1 - Chapter 1',
                        'content': text_content,
                        'screenshot_path': screenshot_path,
                    }

                    content_path = f"{self.content_dir}/chapter_1_{timestamp}.json"
                    with open(content_path, 'w', encoding='utf-8') as file:
                        json.dump(content_data, file, indent=2, ensure_ascii=False)

                    return {
                        **state,
                        'original_content': content_data,
                        'current_content': content_data,
                        'status': 'scraped',
                    }
                
            
            except Exception as e:
                print(f"Error scraping content: {e}")
                return None
            
            finally:
                # close the browser
                await browser.close()
        


# async def main():
#     """Main entry point used for testing purposes."""
#     scraper = ContentScraper()
#     await scraper.setup_directories()
#     content_data = await scraper.scrape_content()

        
# asyncio.run(main())
        