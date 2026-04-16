#!/usr/bin/env python3
"""
Check Search Results

This script examines the search results page to find the correct property IDs
and detail URL patterns.
"""

import asyncio
import sys
from playwright.async_api import async_playwright
import json

BASE_URL = "https://esearch.taylor-cad.org"

async def check_search_results():
    """Extract actual property IDs and detail links from search results"""
    browser = None
    context = None
    page = None
    
    try:
        print("[INFO] Starting browser to check search results...")
        
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # Navigate to main search page
            main_search_url = f"{BASE_URL}/"
            print(f"[INFO] Navigating to: {main_search_url}")
            
            response = await page.goto(main_search_url, wait_until="networkidle", timeout=60000)
            
            # Perform search for owner name "john"
            await page.evaluate('''() => {
                const keywordsInput = document.getElementById('keywords') || document.querySelector('input[name="keywords"]');
                if (keywordsInput) {
                    keywordsInput.value = 'OwnerName:john Year:2026';
                    keywordsInput.dispatchEvent(new Event('input', { bubbles: true }));
                    keywordsInput.dispatchEvent(new Event('change', { bubbles: true }));
                    return true;
                }
                return false;
            }''')
            
            await page.wait_for_timeout(1000)
            await page.mouse.move(100, 100)
            await page.wait_for_timeout(500)
            
            # Trigger search
            await page.evaluate('''() => {
                if (typeof Search === 'function') {
                    Search();
                    return true;
                }
                return false;
            }''')
            
            print("[INFO] Search triggered, waiting for results...")
            await page.wait_for_timeout(5000)
            
            # Wait for grid to load
            try:
                await page.wait_for_selector("#grid", timeout=15000)
                await page.wait_for_timeout(2000)
            except:
                pass
            
            # Extract property data using JavaScript
            property_data = await page.evaluate("""
            () => {
                try {
                    // Method 1: Try Kendo grid
                    const g = window.$('#grid').data('kendoGrid');
                    if (g && g.dataSource) {
                        const view = g.dataSource.view();
                        if (view && view.length) {
                            return view.map(r => {
                                const obj = (typeof r.toJSON === 'function') ? r.toJSON() : r;
                                return {
                                    method: 'kendo_grid',
                                    property_id: obj.propertyId || obj.PropertyId || obj.PropertyID || obj.prop_id,
                                    owner_name: obj.owner_name || obj.OwnerName || '',
                                    type: obj.type || obj.Type || '',
                                    situs_address: obj.situs_address || obj.SitusAddress || obj.situs_addr || '',
                                    year: obj.year || obj.Year || '',
                                    geo_id: obj.geo_id || obj.GeoId || ''
                                };
                            });
                        }
                    }
                    
                    // Method 2: Try to find detail links in the DOM
                    const detailLinks = document.querySelectorAll('a[href*="/Property/Details/"]');
                    if (detailLinks.length > 0) {
                        return Array.from(detailLinks).map(link => ({
                            method: 'dom_links',
                            href: link.href,
                            text: link.innerText.trim(),
                            property_id: link.href.split('/').pop()
                        }));
                    }
                    
                    // Method 3: Try to find table rows
                    const tableRows = document.querySelectorAll('table tbody tr');
                    if (tableRows.length > 1) {
                        return Array.from(tableRows).slice(1, 6).map((row, index) => {
                            const cells = row.querySelectorAll('td');
                            const text = Array.from(cells).map(cell => cell.innerText.trim());
                            return {
                                method: 'table_rows',
                                row_index: index + 1,
                                cells: text,
                                first_cell: text[0] || '',
                                second_cell: text[1] || '',
                                third_cell: text[2] || '',
                                fourth_cell: text[3] || ''
                            };
                        });
                    }
                    
                    return [];
                } catch (e) {
                    console.log('Error:', e.message);
                    return [];
                }
            }
            """)
            
            if property_data:
                print(f"[SUCCESS] Found {len(property_data)} property entries:")
                
                for i, prop in enumerate(property_data[:10], 1):
                    print(f"\n  {i}. Method: {prop['method']}")
                    if prop['method'] == 'kendo_grid':
                        print(f"     ID: {prop['property_id']}")
                        print(f"     Owner: {prop['owner_name']}")
                        print(f"     Type: {prop['type']}")
                        print(f"     Address: {prop['situs_address']}")
                    elif prop['method'] == 'dom_links':
                        print(f"     ID: {prop['property_id']}")
                        print(f"     Href: {prop['href']}")
                        print(f"     Text: {prop['text']}")
                    elif prop['method'] == 'table_rows':
                        print(f"     Row {prop['row_index']}: {prop['cells']}")
                
                # Save to file
                with open('search_results_analysis.json', 'w', encoding='utf-8') as f:
                    json.dump(property_data, f, indent=2, ensure_ascii=False)
                
                print(f"\n[INFO] Saved analysis to search_results_analysis.json")
                
                # Extract first valid property ID for testing
                first_valid_id = None
                for prop in property_data:
                    if prop['method'] == 'kendo_grid' and prop['property_id']:
                        first_valid_id = prop['property_id']
                        break
                    elif prop['method'] == 'dom_links' and prop['property_id']:
                        first_valid_id = prop['property_id']
                        break
                
                if first_valid_id:
                    print(f"\n[INFO] First valid property ID: {first_valid_id}")
                    print(f"[INFO] Test with: python steps/extract-detail.py {first_valid_id}")
                else:
                    print("\n[WARNING] No valid property IDs found")
                
                return property_data
            else:
                print("[WARNING] No property data found")
                return None
            
    except Exception as e:
        print(f"[ERROR] {e}")
        return None
        
    finally:
        if page:
            await page.close()
        if context:
            await context.close()
        if browser:
            await browser.close()

async def main():
    print("Search Results Checker")
    print("=" * 40)
    
    property_data = await check_search_results()
    
    if property_data:
        print(f"\n[SUCCESS] Analysis complete")
    else:
        print("\n[ERROR] Analysis failed")

if __name__ == "__main__":
    asyncio.run(main())
