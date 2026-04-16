import asyncio
import json
import logging
import sys
import aiofiles
from playwright.async_api import async_playwright
from datetime import datetime
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaylorCADScraper:
    def __init__(self):
        self.base_url = "https://esearch.taylor-cad.org/"
        self.search_params = "?_gl=11gmxrpb_gaMTE0MTA5NTA1LjE3NjgyNTMxMzk._ga_YKBM8D2TVN*czE3NzQzNjYwMzckbzExJGcwJHQxNzc0MzY2MDM3JGo2MCRsMCRoMA..&_ga=2.6105523.1446181522.1774361344-114109505.1768253139"
        self.full_url = self.base_url + self.search_params
        
    async def setup_browser(self):
        """Setup browser with proper configuration for VPN usage"""
        playwright = await async_playwright().start()
        
        # Launch browser with stealth settings
        browser = await playwright.chromium.launch(
            headless=True,  # Set to True for production
            args=[
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        # Create context with realistic user agent
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            locale='en-US'
        )
        
        return browser, context
    
    async def _perform_search(self, page, owner_name):
        """Perform search with specified owner name in owner name field with proper JavaScript flow"""
        try:
            # Wait for page to be fully loaded
            await page.wait_for_load_state('networkidle', timeout=10000)
            
            # Step 1: Move mouse to satisfy hasMovedMouse requirement
            logger.info("Moving mouse to satisfy anti-bot protection...")
            await page.mouse.move(100, 100)
            await page.wait_for_timeout(500)
            await page.mouse.move(200, 200)
            await page.wait_for_timeout(500)
            
            # Step 2: Find the keywords input field (based on JavaScript code)
            keywords_input = await page.query_selector('#keywords, input[name="keywords"], input[type="text"]')
            
            if not keywords_input:
                # Try to find any text input as fallback
                text_inputs = await page.query_selector_all('input[type="text"]')
                if text_inputs:
                    keywords_input = text_inputs[0]
                    logger.info("Using first text input found")
            
            if keywords_input:
                logger.info("Found keywords input field")
                
                # Step 3: Fill the search field using JavaScript to trigger events
                await page.evaluate(f'''() => {{
                    const input = document.querySelector('#keywords') || document.querySelector('input[type="text"]');
                    if (input) {{
                        input.value = 'OwnerName:{owner_name} Year:2026';
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                }}''')
                
                await page.wait_for_timeout(1000)
                
                # Step 4: Use JavaScript to call the Search() function
                logger.info("Executing JavaScript search function...")
                search_result = await page.evaluate('''() => {
                    try {
                        // Check if Search function exists and call it
                        if (typeof Search === 'function') {
                            Search();
                            return 'Search function executed';
                        } else if (typeof executeSearch === 'function') {
                            executeSearch(null, false, false);
                            return 'executeSearch function executed';
                        } else {
                            return 'Search function not found';
                        }
                    } catch (error) {
                        return 'Error: ' + error.message;
                    }
                }''')
                
                logger.info(f"JavaScript search result: {search_result}")
                
                # Step 5: Wait for navigation or results
                try:
                    # Wait for either navigation or results to appear
                    await page.wait_for_function(
                        '''() => {
                            return window.location.href.includes('/search/result') || 
                                   document.querySelector('.search-results, .result-item, table[data-testid]');
                        }''',
                        timeout=10000
                    )
                    logger.info("Search results detected")
                    await page.wait_for_timeout(3000)
                    return True
                    
                except Exception as wait_e:
                    logger.warning(f"Wait for results failed: {wait_e}")
                    # Fallback: wait a fixed time and check if URL changed
                    current_url = page.url
                    await page.wait_for_timeout(5000)
                    if current_url != page.url:
                        logger.info("Page navigation detected")
                        return True
                    else:
                        logger.warning("No navigation detected, but search may have completed")
                        return True  # Assume search worked even without navigation
                
            else:
                logger.warning("No suitable input field found")
                return False
                
        except Exception as e:
            logger.error(f"Error performing search: {e}")
            return False
    
    async def _extract_property_data(self, page):
        """Extract structured property data from the Kendo grid"""
        try:
            # Wait a bit for the grid to fully load
            await page.wait_for_timeout(2000)
            
            # Try to get data from Kendo grid using JavaScript
            js_code = '''
            () => {
                try {
                    // Try to get data from Kendo grid
                    var grid = $("#grid").data("kendoGrid");
                    if (grid && grid.dataSource) {
                        var data = grid.dataSource.data();
                        if (data && data.length > 0) {
                            return JSON.stringify(data);
                        }
                    }
                    
                    // Fallback: try to find any table with property data
                    var tables = document.querySelectorAll('table');
                    for (var i = 0; i < tables.length; i++) {
                        var rows = tables[i].querySelectorAll('tr');
                        if (rows.length > 1) {
                            var properties = [];
                            var headers = [];
                            
                            // Get headers from first row
                            var headerCells = rows[0].querySelectorAll('th, td');
                            for (var j = 0; j < headerCells.length; j++) {
                                headers.push(headerCells[j].innerText.trim());
                            }
                            
                            // Get data from remaining rows
                            for (var k = 1; k < rows.length; k++) {
                                var cells = rows[k].querySelectorAll('td');
                                var property = {};
                                
                                for (var l = 0; l < cells.length && l < headers.length; l++) {
                                    var header = headers[l];
                                    var value = cells[l].innerText.trim();
                                    if (value) {
                                        // Clean up header name for use as key
                                        var key = header.toLowerCase().replace(/[^a-z0-9]/g, '_');
                                        property[key] = value;
                                    }
                                }
                                
                                if (Object.keys(property).length > 0) {
                                    properties.push(property);
                                }
                            }
                            
                            if (properties.length > 0) {
                                return JSON.stringify(properties);
                            }
                        }
                    }
                    
                    return JSON.stringify([]);
                } catch (error) {
                    console.log('Error extracting data:', error.message);
                    return JSON.stringify([]);
                }
            }
            '''
            
            result = await page.evaluate(js_code)
            
            if result:
                try:
                    properties = json.loads(result)
                    logger.info(f"Successfully extracted {len(properties)} properties")
                    return properties
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse property data: {e}")
                    return []
            else:
                logger.warning("No property data extracted")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting property data: {e}")
            return []
    
    async def scrape_page(self, owner_name):
        """Main scraping function - extract plain HTML content"""
        browser = None
        context = None
        page = None
        
        try:
            logger.info("Setting up browser...")
            browser, context = await self.setup_browser()
            page = await context.new_page()
            
            logger.info(f"Navigating to: {self.full_url}")
            
            # Navigate to the page with extended timeout
            response = await page.goto(
                self.full_url,
                wait_until='networkidle',
                timeout=60000
            )
            
            if response.status != 200:
                logger.error(f"Failed to load page. Status: {response.status}")
                return None
            
            logger.info("Page loaded successfully")
            
            # Take screenshot for debugging
            await page.screenshot(path='taylor_cad_page.png')
            logger.info("Screenshot saved as taylor_cad_page.png")
            
            # Perform search with specified owner name in owner name field
            logger.info(f"Performing search with owner name '{owner_name}'...")
            search_performed = await self._perform_search(page, owner_name)
            
            if search_performed:
                # Wait for search results to load
                await page.wait_for_timeout(3000)
                logger.info("Search completed, extracting results...")
                
                # Take screenshot of search results (with shorter timeout)
                try:
                    await page.screenshot(path='taylor_cad_search_results.png', timeout=5000)
                    logger.info("Search results screenshot saved")
                except Exception as screenshot_e:
                    logger.warning(f"Screenshot failed: {screenshot_e}")
                
                # Extract search results HTML
                html_content = await page.content()
                body_text = await page.evaluate('() => document.body.innerText')
                
                # Extract structured property data using JavaScript
                logger.info("Extracting structured property data...")
                property_data = await self._extract_property_data(page)
                
                # Save results
                output_file = f"taylor_cad_search_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
                    data = {
                        'url': self.full_url,
                        'scraped_at': datetime.now().isoformat(),
                        'status_code': response.status,
                        'search_query': owner_name,
                        'html_content': html_content,
                        'visible_text': body_text,
                        'content_length': len(html_content),
                        'type': 'search_results',
                        'properties': property_data,
                        'property_count': len(property_data)
                    }
                    await f.write(json.dumps(data, indent=2, ensure_ascii=False))
                
                logger.info(f"Search results saved to {output_file}")
                logger.info(f"HTML content length: {len(html_content)} characters")
                logger.info(f"Visible text length: {len(body_text)} characters")
                logger.info(f"Properties extracted: {len(property_data)}")
                
                return {
                    'html_content': html_content,
                    'visible_text': body_text,
                    'file_path': output_file,
                    'search_performed': True,
                    'properties': property_data,
                    'property_count': len(property_data)
                }
            else:
                logger.warning("Search could not be performed")
                return None
        
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            return None
        
        finally:
            # Cleanup
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()

async def main(owner_name):
    """Main function to run the scraper"""
    scraper = TaylorCADScraper()
    
    logger.info("Starting Taylor CAD scraper...")
    
    try:
        results = await scraper.scrape_page(owner_name)
        
        if results:
            logger.info("Scraping completed successfully!")
            print("\nScraping completed successfully!")
            print("Initial page screenshot saved as: taylor_cad_page.png")
            print("Search results screenshot saved as: taylor_cad_search_results.png")
            print("Search results saved to JSON file with timestamp")
            print(f"Search query: OwnerName:{owner_name} Year:2026")
            print(f"HTML content length: {len(results['html_content'])} characters")
            print(f"Visible text length: {len(results['visible_text'])} characters")
            print(f"Properties extracted: {results['property_count']}")
            print(f"Data file: {results['file_path']}")
        else:
            logger.warning("Scraping completed but no data found")
            print("\nScraping completed but no data was found.")
            print("This might indicate:")
            print("   - VPN connection issue")
            print("   - Page structure has changed")
            print("   - Search form not found")
    
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        print("\nScraping failed: " + str(e))
        print("Please ensure:")
        print("   - VPN is connected and working")
        print("   - Internet connection is stable")
        print("   - Playwright browsers are installed (run: playwright install)")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        owner_name = sys.argv[1]
    else:
        print("Usage: python scrapper.py <owner_name>")
        print("Example: python scrapper.py john")
        sys.exit(1)
    
    print(f"Taylor CAD Property Scraper - Search with '{owner_name}'")
    print("=" * 50)
    print("Target: https://esearch.taylor-cad.org/")
    print("Note: This site requires VPN access")
    print("=" * 50)
    
    # Run the scraper
    asyncio.run(main(owner_name))