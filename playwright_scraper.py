import asyncio
from playwright.async_api import async_playwright

async def scrape_page(url: str, output_file: str = "scraped_content.txt"):
    """
    Minimal Playwright scraper that extracts text content from a webpage
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Navigate to the URL
            await page.goto(url, wait_until="domcontentloaded")
            
            # Extract page title
            title = await page.title()
            
            # Extract main text content
            content = await page.evaluate("""
                () => {
                    // Remove script and style elements
                    const scripts = document.querySelectorAll('script, style');
                    scripts.forEach(el => el.remove());
                    
                    // Get main content areas
                    const mainContent = document.querySelector('main, article, .content, .main-content') || document.body;
                    
                    return {
                        text: mainContent.innerText || mainContent.textContent || '',
                        html: mainContent.innerHTML
                    };
                }
            """)
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n")
                f.write(f"Title: {title}\n")
                f.write("=" * 50 + "\n\n")
                f.write(content['text'])
            
            print(f"Successfully scraped {url}")
            print(f"Title: {title}")
            print(f"Content saved to {output_file}")
            
            return {
                'url': url,
                'title': title,
                'content': content['text'],
                'output_file': output_file
            }
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
        finally:
            await browser.close()

async def scrape_multiple_pages(urls: list, output_dir: str = "."):
    """
    Scrape multiple URLs and save each to separate files
    """
    results = []
    for i, url in enumerate(urls, 1):
        output_file = f"{output_dir}/scraped_page_{i}.txt"
        result = await scrape_page(url, output_file)
        if result:
            results.append(result)
    
    return results

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        # Use URL from command line
        url = sys.argv[1]
        asyncio.run(scrape_page(url))
    else:
        # Default example
        print("Usage: python playwright_scraper.py <URL>")
        print("Example: python playwright_scraper.py https://example.com")
        
        # Demo with a test site
        print("\nRunning demo with https://example.com...")
        asyncio.run(scrape_page("https://example.com"))
