import asyncio
import os
from playwright.async_api import async_playwright


class AspNetTenderCrawler:
    def __init__(self, base_url: str, output_dir: str = "outputs"):
        self.base_url = base_url
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    async def extract_listing_rows(self, page):
        """
        Extract structured data from listing table rows
        """
        rows = await page.query_selector_all("tr")

        tenders = []

        for row in rows:
            try:
                link = await row.query_selector("a[id*='lnkNumeroProceso']")
                if not link:
                    continue

                cells = await row.query_selector_all("td")
                if len(cells) < 5:
                    continue

                tender_data = {
                    "number": await link.inner_text(),
                    "description": await cells[1].inner_text(),
                    "type": await cells[2].inner_text(),
                    "date": await cells[3].inner_text(),
                    "status": await cells[4].inner_text(),
                }

                tenders.append(tender_data)

            except:
                continue

        return tenders

    async def extract_detail_page(self, page):
        """
        Extract clean text from detail page
        """
        content = await page.evaluate("""
            () => {
                const scripts = document.querySelectorAll('script, style');
                scripts.forEach(el => el.remove());
                return document.body.innerText;
            }
        """)
        return content

    async def process_page(self, page, page_number):
        print(f"\nProcessing listing page {page_number}")

        tenders = await self.extract_listing_rows(page)
        print(f"Found {len(tenders)} tenders on this page")

        for i in range(len(tenders)):
            # Re-fetch links (important after navigation)
            links = await page.query_selector_all("a[id*='lnkNumeroProceso']")
            if i >= len(links):
                break

            link = links[i]
            tender_info = tenders[i]

            print(f"Opening tender: {tender_info['number']}")

            await link.click()
            await page.wait_for_load_state("networkidle")

            detail_text = await self.extract_detail_page(page)

            filename = f"{self.output_dir}/page{page_number}_tender_{i+1}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("TENDER SUMMARY\n")
                f.write("=" * 50 + "\n")
                for k, v in tender_info.items():
                    f.write(f"{k.upper()}: {v}\n")

                f.write("\n\nFULL DETAIL PAGE\n")
                f.write("=" * 50 + "\n")
                f.write(detail_text)

            print(f"Saved: {filename}")

            # Go back to listing
            await page.go_back()
            await page.wait_for_selector("a[id*='lnkNumeroProceso']")

    async def has_next_page(self, page):
        """
        Detect if pagination exists
        """
        next_button = await page.query_selector("a:has-text('Siguiente'), a:has-text('Next')")
        return next_button is not None

    async def go_to_next_page(self, page):
        """
        Click next pagination button
        """
        next_button = await page.query_selector("a:has-text('Siguiente'), a:has-text('Next')")
        if next_button:
            await next_button.click()
            await page.wait_for_load_state("networkidle")
            return True
        return False

    async def run(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            print(f"Opening: {self.base_url}")
            await page.goto(self.base_url, wait_until="domcontentloaded")
            await page.wait_for_selector("a[id*='lnkNumeroProceso']")

            page_number = 1

            while True:
                await self.process_page(page, page_number)

                if await self.has_next_page(page):
                    print("Moving to next page...")
                    await self.go_to_next_page(page)
                    page_number += 1
                else:
                    print("No more pages.")
                    break

            await browser.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        print("Usage: python aspnet_crawler.py <URL>")
        exit()

    crawler = AspNetTenderCrawler(url)
    asyncio.run(crawler.run())