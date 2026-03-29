from utils.config_resolver import load_config_with_refs, get_portal_config
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple, Set
from utils.playwright_utils import setup_browser_context, navigate_to_main_page, simulate_postback, cleanup_browser_resources
from utils.file_utils import load_existing_tender_numbers, save_tender_to_ndjson
from utils.bs4_utils import extract_pagination_links, extract_listing_rows
from models.tender import TenderModel

def process_page_tenders(tenders: List[Dict], seen_tender_numbers: Set[str], portal_name: str) -> Tuple[int, List[TenderModel]]:
    """Process tenders from a page and return count of new tenders and new tenders list"""
    new_count = 0
    new_tenders = []
    for tender_dict in tenders:
        # Convert to TenderModel
        tender = TenderModel.from_table_tender(tender_dict, portal_name)
        
        if tender.number not in seen_tender_numbers:
            seen_tender_numbers.add(tender.number)
            save_tender_to_ndjson(tender.to_dict())
            new_count += 1
            new_tenders.append(tender)
    return new_count, new_tenders


def crawl_all_tenders(url: str, portal_config: Dict, portal_name: str) -> List[TenderModel]:
    selectors = portal_config["selectors"]
    column_mapping = portal_config.get("column_mapping", {})
    pagination = portal_config.get("pagination", {})
    all_tenders = []
    seen_tender_numbers = load_existing_tender_numbers()

    playwright, browser, context = setup_browser_context()
    
    try:
        page = navigate_to_main_page(context, url)
        current_page = 1
        max_pages = pagination.get("max_pages", 10)  # Get max_pages from config
        
        # Extract pagination links and target
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")
        _, pagination_target = extract_pagination_links(soup, selectors, return_target=True)
        
        # Use fallback target if none found
        if not pagination_target:
            pagination_target = pagination.get("target", "ctl00$CPH1$GridListaPliegos")
            print(f"Using fallback pagination target: {pagination_target}")
        else:
            print(f"Extracted pagination target: {pagination_target}")

        while current_page <= max_pages:
            print(f"Crawling page: {current_page}")

            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # 🔹 SAME logic for every page (including page 1)
            tenders = extract_listing_rows(
                soup,
                url,
                selectors,
                column_mapping,
                page_no=current_page
            )

            if not tenders:
                print("No tenders found, stopping crawl")
                break

            new_count, new_tenders = process_page_tenders(tenders, seen_tender_numbers, portal_name)
            all_tenders.extend(new_tenders)

            print(f"Added {new_count} new tenders from page {current_page}")

            if new_count == 0:
                print("No new tenders found, stopping crawl")
                break

            current_page += 1

            # Handle pagination based on portal config
            if pagination.get("type") == "postback":
                if current_page > max_pages:
                    print(f"Reached maximum pages limit ({max_pages}), stopping crawl")
                    break
                target = pagination_target  # Use extracted target
                argument = f"Page${current_page}"
                simulate_postback(page, target, argument)
            else:
                # For other pagination types, break for now
                print("Pagination handling not implemented for this type")
                break

    finally:
        cleanup_browser_resources(playwright, browser)

    return all_tenders
    
def main() -> None:
    """Main function to orchestrate the tender crawling workflow"""
    config = load_config_with_refs("config/portals.json")
    
    all_tenders = []
    
    # Loop over all portals
    for portal in config["portals"]:
        if not portal.get("active", True):
            print(f"Skipping inactive portal: {portal['name']}")
            continue
            
        print(f"Processing portal: {portal['name']} ({portal['country']})")
        
        # Loop over all listing URLs for this portal
        for url in portal["listing_urls"]:
            print(f"Crawling URL: {url}")
            
            portal_config = get_portal_config(portal)
            tenders = crawl_all_tenders(url, portal_config, portal['name'])
            all_tenders.extend(tenders)
            print(f"Found {len(tenders)} tenders from {url}")
    
    print(f"Total tenders found across all portals: {len(all_tenders)}")
    
    # Display first 5 tenders
    for t in all_tenders[:5]:
        print(t.to_dict())


if __name__ == "__main__":
    main()