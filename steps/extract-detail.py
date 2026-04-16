#!/usr/bin/env python3
"""
Extract Property Details Script

This script demonstrates how to navigate to a property detail page
by extracting the first property from search results and navigating to its detail page.

Usage: python extract-detail.py
Example: python extract-detail.py
"""

import asyncio
import sys
import re
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import json

BASE_URL = "https://esearch.taylor-cad.org"

async def extract_first_property_from_results(page):
    """
    Extract the first property ID from the search results table by parsing onclick attributes.
    """
    try:
        # Extract property ID from the first table row with onclick attribute
        first_property_id = await page.evaluate("""
        () => {
            try {
                // Look for table rows with onclick attributes containing redirectToPropertyDetails
                const rows = document.querySelectorAll('tr[onclick*="redirectToPropertyDetails"]');
                if (rows.length > 0) {
                    const firstRow = rows[0];
                    const onclickAttr = firstRow.getAttribute('onclick');
                    
                    // Extract property ID from onclick="redirectToPropertyDetails('10370','2026','10330', 'false')"
                    const match = onclickAttr.match(/redirectToPropertyDetails\('(\d+)'/);
                    if (match) {
                        return {
                            property_id: match[1],
                            method: 'onclick_parser',
                            onclick: onclickAttr
                        };
                    }
                }
                
                // Fallback: look for any elements with Property ID class
                const propertyIdCells = document.querySelectorAll('td._propertyId');
                if (propertyIdCells.length > 0) {
                    const firstCell = propertyIdCells[0];
                    return {
                        property_id: firstCell.innerText.trim(),
                        method: 'class_selector'
                    };
                }
                
                return null;
            } catch (e) {
                console.log('Error:', e.message);
                return null;
            }
        }
        """)
        
        if first_property_id and first_property_id['property_id']:
            property_id = str(first_property_id['property_id'])
            method = first_property_id['method']
            
            print(f"[SUCCESS] Found first property ID: {property_id}")
            print(f"[INFO] Using method: {method}")
            
            if method == 'onclick_parser':
                print(f"[DEBUG] onclick attribute: {first_property_id['onclick']}")
            
            return property_id
        else:
            print("[ERROR] No property ID found in search results")
            
            # Debug: show page structure
            page_content = await page.content()
            if 'redirectToPropertyDetails' in page_content:
                print("[DEBUG] Found redirectToPropertyDetails in page content")
            else:
                print("[DEBUG] redirectToPropertyDetails not found in page content")
            
            return None
            
    except Exception as e:
        print(f"[ERROR] Failed to extract first property: {e}")
        return None

async def extract_property_detail(property_id=None):
    """
    Navigate to search results and then to the first property detail page
    using the same navigation pattern as the site's redirectToPropertyDetails function.
    """
    browser = None
    context = None
    page = None
    
    try:
        if property_id:
            print(f"[INFO] Starting browser to extract details for property ID: {property_id}")
        else:
            print("[INFO] Starting browser to extract first property details")
        
        # Setup browser
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            # First, navigate to the main search page to establish session
            main_search_url = f"{BASE_URL}/"
            print(f"[INFO] Navigating to main search page: {main_search_url}")
            
            response = await page.goto(main_search_url, wait_until="networkidle", timeout=60000)
            
            if response.status != 200:
                print(f"[ERROR] Failed to load main search page. Status: {response.status}")
                return None
            
            print("[INFO] Main search page loaded successfully")
            
            # Wait for page to be fully interactive
            await page.wait_for_timeout(2000)
            
            # Now perform the search by setting keywords and submitting
            print("[INFO] Performing search for owner name 'john'...")
            
            # Set the search keywords
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
            
            # Wait a moment for the input to be set
            await page.wait_for_timeout(1000)
            
            # Move mouse to satisfy anti-bot protection
            await page.mouse.move(100, 100)
            await page.wait_for_timeout(500)
            
            # Click search button or trigger search
            search_performed = await page.evaluate('''() => {
                // Try to find and click search button
                const searchBtn = document.querySelector('button[onclick*="Search()"]') || 
                                 document.querySelector('input[type="submit"]') ||
                                 document.querySelector('button[type="submit"]') ||
                                 document.querySelector('.btn-primary');
                
                if (searchBtn) {
                    searchBtn.click();
                    return true;
                }
                
                // Try to call Search() function directly
                if (typeof Search === 'function') {
                    Search();
                    return true;
                }
                
                return false;
            }''')
            
            if search_performed:
                print("[INFO] Search triggered, waiting for results...")
                # Wait for search results to load
                await page.wait_for_timeout(5000)
                
                # Check if we're on results page
                current_url = page.url
                print(f"[INFO] Current URL after search: {current_url}")
                
                if 'search/result' in current_url:
                    print("[SUCCESS] Navigated to search results page")
                else:
                    print("[WARNING] May not be on results page, attempting to continue...")
            else:
                print("[WARNING] Could not trigger search, trying direct navigation...")
                # Fallback to direct URL navigation
                search_url = f"{BASE_URL}/search/result?keywords=Subdivision%3A%2200700%20-%20ACCO%20ADDN%22%20"
                print(f"[INFO] Trying direct navigation: {search_url}")
                response = await page.goto(search_url, wait_until="networkidle", timeout=60000)
            
            if response.status != 200:
                print(f"[ERROR] Failed to load search results. Status: {response.status}")
                return None
            
            print("[INFO] Search results loaded successfully")
            
            # Wait for the grid to load
            try:
                await page.wait_for_selector("#grid", timeout=15000)
                print("[INFO] Grid found, waiting for data...")
                await page.wait_for_timeout(2000)
            except Exception as e:
                print(f"[WARNING] Grid selector not found: {e}")
            
            # Take screenshot for debugging
            await page.screenshot(path='search_results_page.png')
            print("[INFO] Screenshot saved as search_results_page.png")
            
            # Extract first property from search results if no property_id provided
            if not property_id:
                print("[INFO] Extracting first property from search results...")
                property_id = await extract_first_property_from_results(page)
                
                if not property_id:
                    print("[ERROR] Failed to extract first property from search results")
                    return None
            
            # Direct navigation using the correct detail URL pattern
            # Based on the site's actual URL structure: /Property/View/{property_id}?year=2026&ownerId={ownerId}
            detail_url = f"{BASE_URL}/Property/View/{property_id}?year=2026&ownerId=153282"
            print(f"[INFO] Attempting direct navigation to: {detail_url}")
            
            try:
                detail_response = await page.goto(detail_url, wait_until="domcontentloaded", timeout=20000)
                
                if detail_response.status == 200:
                    print(f"[SUCCESS] Successfully navigated to detail page for property {property_id}")
                    
                    # Wait for detail page content to load
                    await page.wait_for_timeout(2000)
                    
                    # Take screenshot of detail page
                    await page.screenshot(path=f'property_detail_{property_id}.png')
                    print(f"[INFO] Detail page screenshot saved as property_detail_{property_id}.png")
                    
                    # Extract the page content
                    html_content = await page.content()
                    soup = BeautifulSoup(html_content, "html.parser")
                    
                    # Extract specific fields
                    extracted_data = {}
                    
                    # Extract Living Area
                    living_area = None
                    living_area_selectors = [
                        'th:contains("Living Area") + td',
                        'td:contains("Living Area")',
                        '[class*="living"]',
                        '[class*="area"]'
                    ]
                    
                    for selector in living_area_selectors:
                        try:
                            element = soup.select_one(selector)
                            if element:
                                living_area = element.get_text(strip=True)
                                if living_area and living_area != 'Living Area':
                                    break
                        except:
                            continue
                    
                    # Extract Deed Date
                    deed_date = None
                    
                    # Look for Property Deed History table
                    deed_table = None
                    for table in soup.find_all('table'):
                        table_text = table.get_text()
                        if 'Property Deed History' in table_text or 'Deed Date' in table_text:
                            deed_table = table
                            break
                    
                    if deed_table:
                        # Find the first row with a date in the Deed Date column
                        rows = deed_table.find_all('tr')
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 1:
                                first_cell = cells[0].get_text(strip=True)
                                # Check if this looks like a date (MM/DD/YYYY format)
                                date_match = re.match(r'^(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', first_cell)
                                if date_match:
                                    deed_date = date_match.group(1)
                                    break
                    
                    # Fallback: try other selectors if table approach didn't work
                    if not deed_date:
                        deed_date_selectors = [
                            'th:contains("Deed") + td',
                            'td:contains("Deed")',
                            '[class*="deed"]',
                            '[class*="date"]'
                        ]
                        
                        for selector in deed_date_selectors:
                            try:
                                element = soup.select_one(selector)
                                if element:
                                    deed_date = element.get_text(strip=True)
                                    if deed_date and 'Deed' not in deed_date:
                                        break
                            except:
                                continue
                    
                    # Extract Mailing Address
                    mailing_address = None
                    
                    # Look for the Mailing Address row in the Property Details table
                    for table in soup.find_all('table'):
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all(['th', 'td'])
                            if len(cells) >= 2:
                                header_text = cells[0].get_text(strip=True)
                                if header_text == 'Mailing Address:':
                                    # Get the content from the second cell (index 1)
                                    mailing_address = cells[1].get_text(separator='\n', strip=True)
                                    break
                            if mailing_address:
                                break
                        if mailing_address:
                            break
                    
                    # Fallback: try regex pattern if table approach didn't work
                    if not mailing_address:
                        page_text = soup.get_text()
                        mailing_match = re.search(r'Mailing Address:\s*(.*?)(?=\n\s*\n|\n\s*[A-Z][a-z]+:)', page_text, re.DOTALL)
                        if mailing_match:
                            mailing_address = mailing_match.group(1).strip()
                    
                    # Clean up the mailing address format
                    if mailing_address:
                        # Remove extra whitespace and normalize line breaks
                        mailing_address = '\n'.join(line.strip() for line in mailing_address.split('\n') if line.strip())
                    
                    # Also try to find in text using regex patterns
                    page_text = soup.get_text()
                    
                    if not living_area:
                        living_area_match = re.search(r'Living Area[:\s]+([0-9,\.]+\s*(?:sqft|sq\.?ft\.?|sf))', page_text, re.IGNORECASE)
                        if living_area_match:
                            living_area = living_area_match.group(1)
                    
                    if not deed_date:
                        deed_date_match = re.search(r'Deed[:\s]+([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})', page_text, re.IGNORECASE)
                        if deed_date_match:
                            deed_date = deed_date_match.group(1)
                    
                    # Extract Building Information table
                    building_info = []
                    
                    # Look for the Property Improvement - Building table
                    building_table = None
                    for table in soup.find_all('table'):
                        table_text = table.get_text()
                        if 'Property Improvement - Building' in table_text or ('Type' in table_text and 'Description' in table_text and 'Year Built' in table_text):
                            building_table = table
                            break
                    
                    if building_table:
                        rows = building_table.find_all('tr')
                        # Skip header row and process data rows
                        for row in rows[1:]:  # Skip first row (header)
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 5:  # Ensure we have enough columns
                                type_cell = cells[0].get_text(strip=True)
                                desc_cell = cells[1].get_text(strip=True)
                                year_built_cell = cells[4].get_text(strip=True)  # Year Built is 5th column (index 4)
                                
                                # Only add if we have meaningful data
                                if type_cell and desc_cell and year_built_cell and year_built_cell != 'N/A':
                                    building_info.append({
                                        'type': type_cell,
                                        'description': desc_cell,
                                        'year_built': year_built_cell
                                    })
                    
                    # Extract Property Roll Value History table - get 2025 Assessed value
                    assessed_2025 = None
                    
                    # Look for the Property Roll Value History table
                    roll_value_table = None
                    for table in soup.find_all('table'):
                        table_text = table.get_text()
                        # Look for table with Year, Improvements, Land Market, and Assessed columns
                        if 'Year' in table_text and 'Improvements' in table_text and 'Assessed' in table_text:
                            roll_value_table = table
                            break
                    
                    if roll_value_table:
                        rows = roll_value_table.find_all('tr')
                        # Look for the 2025 row
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 7:  # Ensure we have enough columns
                                year_cell = cells[0].get_text(strip=True)
                                if year_cell == '2025':
                                    # Assessed value is in the last column (index 6)
                                    assessed_2025 = cells[6].get_text(strip=True)
                                    break
                    
                    # Extract Tax Information table - only totals
                    tax_totals = {}
                    
                    # Look for the Property Tax Bill Data table
                    tax_table = None
                    for table in soup.find_all('table'):
                        table_text = table.get_text()
                        # Look for table with Year, Taxing Jurisdiction, and Amount Due columns
                        if 'Year' in table_text and 'Taxing Jurisdiction' in table_text and 'Amount Due' in table_text:
                            tax_table = table
                            break
                    
                    if tax_table:
                        rows = tax_table.find_all('tr')
                        target_years = ['2025', '2024', '2023']
                        
                        # Look for rows that contain "Total:" in the second column (index 1)
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 11:
                                # Check if this is a total row by looking at the second column
                                second_cell = cells[1].get_text(strip=True)
                                if 'Total:' in second_cell:
                                    # Extract year from the total row (e.g., "2025 Total:" -> "2025")
                                    year_match = re.search(r'(\d{4})', second_cell)
                                    if year_match:
                                        year = year_match.group(1)
                                        if year in target_years:
                                            amount_due_cell = cells[10].get_text(strip=True)
                                            tax_totals[year] = amount_due_cell
                    
                    # Add extracted data
                    if living_area:
                        extracted_data['living_area'] = living_area
                    if deed_date:
                        extracted_data['deed_date'] = deed_date
                    if mailing_address:
                        extracted_data['mailing_address'] = mailing_address
                    if building_info:
                        extracted_data['building_info'] = building_info
                    if assessed_2025:
                        extracted_data['assessed_2025'] = assessed_2025
                    if tax_totals:
                        extracted_data['tax_totals'] = tax_totals
                    
                    # Save the extracted information
                    output_file = f"property_detail_{property_id}.json"
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'raw_html': html_content,
                            'extracted_data': extracted_data
                        }, f, indent=2, ensure_ascii=False)
                    
                    print(f"[SUCCESS] Property details saved to: {output_file}")
                    
                    return html_content
                else:
                    print(f"[ERROR] Detail page returned status: {detail_response.status}")
                    
            except Exception as e:
                print(f"[ERROR] Failed to navigate to detail page: {e}")
                print("[ERROR] Failed to navigate to detail page")
            return None
            
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return None
        
    finally:
        # Cleanup
        if page:
            await page.close()
        if context:
            await context.close()
        if browser:
            await browser.close()

async def main():
    """Main function"""
    # Allow optional property_id argument for backward compatibility
    property_id = None
    if len(sys.argv) >= 2:
        property_id = sys.argv[1]
        print(f"Property Detail Extractor - Property ID: {property_id}")
    else:
        print("Property Detail Extractor - Extracting first property from search results")
    
    print("=" * 60)
    
    try:
        result = await extract_property_detail(property_id)
        
        if result:
            print("\n[SUCCESS] Property detail extraction completed!")
            print("Files created:")
            print("  - search_results_page.png (search results screenshot)")
            if property_id:
                print(f"  - property_detail_{property_id}.png (detail page screenshot)")
                print(f"  - property_detail_{property_id}.json (extracted data)")
            else:
                print("  - property_detail_{extracted_id}.png (detail page screenshot)")
                print("  - property_detail_{extracted_id}.json (extracted data)")
        else:
            print("\n[ERROR] Failed to extract property details")
            print("Possible reasons:")
            if property_id:
                print("  - Invalid property ID")
            print("  - VPN connection issue")
            print("  - Site structure changed")
            print("  - Network connectivity problems")
            print("  - No properties found in search results")
    
    except Exception as e:
        print(f"\n[ERROR] Extraction failed: {e}")
        print("Please ensure:")
        print("  - VPN is connected and working")
        if property_id:
            print("  - Property ID is valid")
        print("  - Internet connection is stable")

if __name__ == "__main__":
    asyncio.run(main())