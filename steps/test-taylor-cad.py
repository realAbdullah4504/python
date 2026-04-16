"""
Taylor CAD - Abilene Property Scraper (FINAL)
=============================================
Confirmed from debug:
  - Results table columns: Property ID | Geo ID | Type | Owner Name | Owner ID | Situs Address | Legal Description | Appraised
  - Property ID cell contains a LINK <a href="/Property/Details/105625"> 
  - Clicking that link opens detail page in SAME TAB
  - Detail page has Property Roll Value History table with Assessed 2025

Strategy:
  - For each property ID: navigate directly to /Property/Details/{id}
  - Wait for page to fully load, then scroll to bottom
  - Parse all required fields from the loaded HTML

Run: python taylor_cad_scraper.py
"""

import asyncio
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL        = "https://esearch.taylor-cad.org"
OUTPUT_XLSX     = "abilene_properties.xlsx"
CHECKPOINT_FILE = "checkpoint.json"
DELAY_SEC       = 1.5
TAX_YEARS       = [2025, 2024, 2023]
SEARCH_KEYWORD  = "abilene"
FIRST_PAGE_ONLY = True   # True = test with first modal page only; False = all pages

FIELDS = [
    "Owner Name", "Owner ID", "Property ID", "Type", "Situs Address", "Legal Description",
    "Mailing Address", "Assessed Value 2025", "Deed Date",
    "Living Area", "Year Built",
    "Amount Due 2025", "Amount Due 2024", "Amount Due 2023",
]

# ── Checkpoint ────────────────────────────────────────────────────────────────

def load_checkpoint() -> dict:
    if Path(CHECKPOINT_FILE).exists():
        with open(CHECKPOINT_FILE) as f:
            data = json.load(f)
        data.setdefault("done_subdivisions", [])
        data.setdefault("done_property_ids", [])
        return data
    return {"done_subdivisions": [], "done_property_ids": []}

def save_checkpoint(cp: dict):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(cp, f, indent=2)

# ── XLSX ──────────────────────────────────────────────────────────────────────

def append_to_xlsx(row: dict):
    path = Path(OUTPUT_XLSX)
    if path.exists():
        wb = openpyxl.load_workbook(path)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Abilene Properties"
        hfill = PatternFill("solid", fgColor="1F4E79")
        hfont = Font(bold=True, color="FFFFFF", size=11)
        for ci, f in enumerate(FIELDS, 1):
            c = ws.cell(1, ci, f)
            c.fill = hfill
            c.font = hfont
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.row_dimensions[1].height = 30
        for i, w in enumerate([30,12,6,12,35,40,40,16,12,14,10,15,15,15], 1):
            ws.column_dimensions[ws.cell(1,i).column_letter].width = w
    ws.append([row.get(f, "") for f in FIELDS])
    last = ws.max_row
    if last % 2 == 0:
        fill = PatternFill("solid", fgColor="D9E1F2")
        for ci in range(1, len(FIELDS)+1):
            ws.cell(last, ci).fill = fill
    wb.save(path)

# ── Parsers ───────────────────────────────────────────────────────────────────

def parse_mailing_address(soup: BeautifulSoup) -> str:
    for el in soup.find_all(["th", "td", "strong", "label", "span"]):
        if "mailing address" in el.get_text(strip=True).lower():
            sib = el.find_next_sibling("td")
            if sib:
                return sib.get_text(" ", strip=True)
            tr = el.find_parent("tr")
            if tr:
                cells = tr.find_all("td")
                if len(cells) >= 2:
                    return cells[-1].get_text(" ", strip=True)
    return ""

def parse_assessed_value_2025(soup: BeautifulSoup) -> str:
    """
    Find Property Roll Value History table.
    Headers: Year | Improvements | Land Market | Ag Valuation | Appraised | HS Cap Loss | Assessed
    Return Assessed for year 2025. Fall back to first non-N/A year.
    """
    for tbl in soup.find_all("table"):
        ths = [th.get_text(strip=True).lower() for th in tbl.find_all("th")]
        if "year" not in ths:
            continue
        if not any(h == "assessed" for h in ths):
            continue

        year_col     = ths.index("year")
        assessed_col = ths.index("assessed")

        print(f"      [Roll] headers={ths}")
        fallback = ""
        for tr in tbl.find_all("tr"):
            tds = tr.find_all("td")
            if not tds or len(tds) <= max(year_col, assessed_col):
                continue
            yr  = tds[year_col].get_text(strip=True)
            val = tds[assessed_col].get_text(strip=True)
            print(f"      [Roll] year={yr}  assessed={val}")
            if yr == "2025" and val and val.upper() != "N/A":
                return val
            if not fallback and val and val.upper() != "N/A":
                fallback = val
        if fallback:
            print(f"      [Roll] 2025 empty, using fallback={fallback}")
            return fallback
    return ""

def parse_deed_date(soup: BeautifulSoup) -> str:
    for txt in soup.find_all(string=lambda s: s and "deed history" in s.lower()):
        tbl = txt.find_parent().find_next("table")
        if tbl:
            rows = tbl.find_all("tr")
            if len(rows) > 1:
                cells = rows[1].find_all("td")
                if cells:
                    return cells[0].get_text(strip=True)
    for tbl in soup.find_all("table"):
        ths = [th.get_text(strip=True).lower() for th in tbl.find_all("th")]
        if any("deed" in h for h in ths):
            rows = tbl.find_all("tr")
            if len(rows) > 1:
                cells = rows[1].find_all("td")
                if cells:
                    return cells[0].get_text(strip=True)
    return ""

def parse_improvements(html: str):
    soup = BeautifulSoup(html, "html.parser")
    living_area = year_built = ""
    for div in soup.find_all("div", class_="panel-table-info"):
        m = re.search(r"Living Area[:\s]+([\d,\.]+)\s*sqft", div.get_text(" "), re.I)
        if m:
            living_area = m.group(1) + " sqft"
            break
    if not living_area:
        m = re.search(r"Living Area[:\s]+([\d,\.]+)\s*sqft", soup.get_text(" "), re.I)
        if m:
            living_area = m.group(1) + " sqft"
    for tbl in soup.find_all("table"):
        for tr in tbl.find_all("tr")[1:]:
            tds = tr.find_all("td")
            if tds and tds[0].get_text(strip=True).upper().strip() == "MA":
                for td in tds:
                    v = td.get_text(strip=True)
                    if re.match(r"^(19|20)\d{2}$", v) and v != "0":
                        year_built = v
                        break
                break
        if year_built:
            break
    return living_area, year_built

def parse_taxes(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tbl in soup.find_all("table"):
        ths = [th.get_text(strip=True).lower() for th in tbl.find_all("th")]
        col = next((i for i, h in enumerate(ths) if "due" in h or "balance" in h or "amount" in h), None)
        if col is None:
            continue
        vals = []
        for tr in tbl.find_all("tr")[1:]:
            tds = tr.find_all("td")
            if len(tds) > col:
                v = tds[col].get_text(strip=True)
                if v and re.search(r"\d", v):
                    vals.append(v)
        if vals:
            return vals[-1]
    m = re.search(r"(?:total|amount|balance)[^\$\d]*\$([\d,\.]+)", soup.get_text(" "), re.I)
    return ("$" + m.group(1)) if m else "$0"

def parse_tax_totals(soup: BeautifulSoup) -> dict:
    """
    Extract Tax Information table - only totals from property detail page.
    Returns dict with years as keys and tax amounts as values.
    """
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
                            amount_due_cell = cells[6].get_text(strip=True)
                            tax_totals[year] = amount_due_cell
    
    return tax_totals

# ── Subdivision helpers ───────────────────────────────────────────────────────

async def go_to_by_address(page):
    await page.goto(BASE_URL, wait_until="networkidle")
    await asyncio.sleep(1.5)
    await page.click("a[data-filter='search-address']")
    await asyncio.sleep(1.5)

async def open_subdivision_modal(page) -> bool:
    try:
        await page.click("#searchSubdivision")
        await asyncio.sleep(2)
        if await page.locator("#subdivisionModal").is_visible():
            return True
        await page.evaluate("$('#subdivisionModal').modal('show')")
        await asyncio.sleep(2)
        return await page.locator("#subdivisionModal").is_visible()
    except Exception as e:
        print(f"  Modal error: {e}")
        return False

async def get_all_abilene_subdivisions(page) -> list:
    if not await open_subdivision_modal(page):
        return []
    await page.fill("#subdivisionSearch", SEARCH_KEYWORD)
    await asyncio.sleep(0.5)
    await page.click("#subdivisionModal button.btn-primary")
    await asyncio.sleep(2)

    subdivisions = []
    modal_page = 1
    while True:
        print(f"  Modal page {modal_page}...")
        await asyncio.sleep(1)
        items = await page.locator("#subdivisionListContainer p.subdivision-item").all()
        found = 0
        for item in items:
            txt = (await item.inner_text()).strip()
            if txt and txt not in subdivisions:
                subdivisions.append(txt)
                found += 1
        print(f"    +{found} subdivisions (total {len(subdivisions)})")

        if FIRST_PAGE_ONLY:
            print(f"  FIRST_PAGE_ONLY=True, stopping here")
            break

        nxt = page.locator("#subdivisionModal .modal-footer a:has-text('Next'), #subdivisionModal .pagination li.next:not(.disabled) a")
        if await nxt.count() > 0:
            await nxt.first.click()
            await asyncio.sleep(1.5)
            modal_page += 1
        else:
            break

    try:
        await page.click("#subdivisionModal button.close")
        await asyncio.sleep(1)
    except Exception:
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)
    return subdivisions

async def search_subdivision(page, subdiv_name: str) -> bool:
    if not await open_subdivision_modal(page):
        return False
    await page.fill("#subdivisionSearch", SEARCH_KEYWORD)
    await asyncio.sleep(0.5)
    await page.click("#subdivisionModal button.btn-primary")
    await asyncio.sleep(2)

    # Click the matching item via JS
    try:
        item = page.locator(f"#subdivisionListContainer p.subdivision-item[data-name='{subdiv_name}']").first
        if await item.count() > 0:
            did  = await item.get_attribute("data-id")
            dname = await item.get_attribute("data-name")
            safe = dname.replace("'", "\\'")
            await page.evaluate(f"selectSubdivision('{did}', '{safe}')")
            await asyncio.sleep(1)
        else:
            await page.keyboard.press("Escape")
            return False
    except Exception as e:
        print(f"  Select error: {e}")
        await page.keyboard.press("Escape")
        return False

    # Set Property Type = Real via Select2
    # await page.evaluate("""
    #     var s = document.getElementById('PropertyType');
    #     s.value = 'Real'; $(s).trigger('change');
    # """)
    # await asyncio.sleep(0.5)
    await page.click("button[onclick='AdvancedSearch();']")
    await asyncio.sleep(3)
    return True

async def collect_property_ids(page) -> list:
    """
    Collect property IDs and basic info from results using onclick attributes.
    This method works with the Kendo UI grid that uses onclick handlers.
    """
    all_props = []
    page_num  = 1

    while True:
        print(f"    Page {page_num}...")
        # Check current URL
        current_url = page.url
        print(f"    Current URL: {current_url}")
        
        # Wait for the grid to be visible
        try:
            await page.wait_for_selector("#grid", timeout=10000)
            print(f"    Grid found, waiting for data...")
            await asyncio.sleep(3)
        except PlaywrightTimeout:
            print(f"    Grid not found on page {page_num}")
            break

        # Extract all properties using onclick attributes
        try:
            properties = await page.evaluate("""
            () => {
                const props = [];
                try {
                    // Look for table rows with onclick attributes containing redirectToPropertyDetails
                    const rows = document.querySelectorAll('tr[onclick*="redirectToPropertyDetails"]');
                    console.log('Found rows with onclick:', rows.length);
                    
                    rows.forEach((row, index) => {
                        const onclickAttr = row.getAttribute('onclick');
                        console.log('Row', index, 'onclick:', onclickAttr);
                        
                        // Extract property ID from onclick="redirectToPropertyDetails('10370','2026','10330', 'false')"
                        const match = onclickAttr.match(/redirectToPropertyDetails\\('(\\d+)'/);
                        if (match) {
                            const cells = row.querySelectorAll('td');
                            const texts = Array.from(cells).map(cell => cell.innerText.trim());
                            console.log('Row', index, 'cells:', texts);
                            console.log('Column mapping:');
                            texts.forEach((text, idx) => {
                                console.log(`  [${idx}]: "${text}"`);
                            });
                            
                            // Based on actual HTML structure, the correct mapping is:
                            // 0=PropertyID, 1=Year(hidden), 2=GeoID, 3=NeighborhoodCode(hidden), 4=Type, 5=OwnerName, 6=OwnerID, 7=SitusAddr(hidden), 8=LegalDesc(hidden), 9=Appraised
                            props.push({
                                prop_id: match[1],
                                type: texts[4] || "",  // Type is at index 4
                                owner_name: texts[5] || "",  // Owner Name is at index 5
                                owner_id: texts[6] || "",  // Owner ID is at index 6
                                situs_addr: texts[7] || "",  // Situs Address is at index 7 (hidden)
                                legal_desc: texts[8] || "",  // Legal Description is at index 8 (hidden)
                                detail_url: window.location.origin + '/Property/View/' + match[1] + '?year=2026&ownerId=' + (texts[6] || ''),
                                method: 'onclick_parser'
                            });
                        }
                    });
                    
                    // Fallback: look for any elements with Property ID class
                    if (props.length === 0) {
                        const propertyIdCells = document.querySelectorAll('td._propertyId');
                        console.log('Fallback: found _propertyId cells:', propertyIdCells.length);
                        
                        propertyIdCells.forEach((cell, index) => {
                            const row = cell.closest('tr');
                            const cells = row.querySelectorAll('td');
                            const texts = Array.from(cells).map(cell => cell.innerText.trim());
                            
                            props.push({
                                prop_id: cell.innerText.trim(),
                                type: texts[2] || "",
                                owner_name: texts[3] || "",
                                situs_addr: texts[5] || "",
                                legal_desc: texts[6] || "",
                                detail_url: window.location.origin + '/Property/View/' + cell.innerText.trim() + '?year=2026&ownerId=' + (texts[4] || ''),
                                method: 'class_selector'
                            });
                        });
                    }
                    
                    return props;
                } catch (e) {
                    console.log('JavaScript error:', e.message);
                    return [];
                }
            }
            """)
            
            if properties:
                print(f"    Found {len(properties)} properties using onclick method")
                for prop in properties:
                    prop_type = prop["type"].strip().upper()
                    print(f"      Found: {prop['prop_id']} | Type: {prop_type} | {prop['owner_name']} | {prop['situs_addr']}")
                    all_props.append(prop)
            else:
                print(f"    No properties found with onclick method")
                
                # Debug: check if redirectToPropertyDetails exists in page
                page_content = await page.content()
                if 'redirectToPropertyDetails' in page_content:
                    print(f"    DEBUG: redirectToPropertyDetails found in page content")
                    # Save debug HTML
                    with open(f"debug_page_{page_num}_onclick.html", "w", encoding="utf-8") as f:
                        f.write(page_content)
                    print(f"    Debug HTML saved to debug_page_{page_num}_onclick.html")
                else:
                    print(f"    DEBUG: redirectToPropertyDetails not found in page content")
                break
                
        except Exception as e:
            print(f"    Error extracting properties: {e}")
            break

        # Check for next page
        try:
            nxt = page.locator("li.next:not(.disabled) a, .pagination a[aria-label='Next']")
            if await nxt.count() > 0:
                await nxt.first.click()
                await asyncio.sleep(2)
                page_num += 1
            else:
                break
        except Exception as e:
            print(f"    Error checking for next page: {e}")
            break

    return all_props

async def scrape_detail(page, prop: dict, context) -> dict:
    """
    Navigate directly to the confirmed detail URL.
    Scroll down to load all sections including Property Roll Value History.
    """
    result = {
        "mailing_address": "",
        "assessed_value":  "",
        "deed_date":       "",
        "living_area":     "",
        "year_built":      "",
        "tax_totals":      {},
    }

    detail_url = prop["detail_url"]
    print(f"      -> {detail_url}")

    try:
        await page.goto(detail_url, wait_until="domcontentloaded", timeout=20000)
        # Wait for the page content to appear
        await page.wait_for_selector(".panel, table, #property-detail", timeout=10000)
        await asyncio.sleep(1)

        # Scroll down slowly to trigger lazy loading
        for scroll_pct in [0.3, 0.6, 1.0]:
            await page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {scroll_pct})")
            await asyncio.sleep(1)
        # Final scroll to absolute bottom
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        result["mailing_address"] = parse_mailing_address(soup)
        result["assessed_value"]  = parse_assessed_value_2025(soup)
        result["deed_date"]       = parse_deed_date(soup)
        result["tax_totals"]      = parse_tax_totals(soup)

        if result["assessed_value"]:
            print(f"      Assessed 2025: {result['assessed_value']}")
        else:
            print(f"      Assessed 2025 not found")

        # Improvements (living area + year built)
        try:
            r = await context.request.get(
                f"{BASE_URL}/Property/GetImprovements?propertyId={prop['prop_id']}&year=2026&hideValue=False"
            )
            if r.status == 200:
                result["living_area"], result["year_built"] = parse_improvements(await r.text())
        except Exception as e:
            print(f"      Improvements: {e}")

    except Exception as e:
        print(f"      Detail error: {e}")

    return result

# ── Main ──────────────────────────────────────────────────────────────────────

async def scrape():
    cp                = load_checkpoint()
    done_subdivisions = set(cp.get("done_subdivisions", []))
    done_property_ids = set(str(x) for x in cp.get("done_property_ids", []))

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context()
        page    = await context.new_page()

        # Step 1: Collect subdivisions
        print("Opening Taylor CAD...")
        await go_to_by_address(page)
        print(f"Collecting subdivisions (first_page_only={FIRST_PAGE_ONLY})...")
        all_subdivisions = await get_all_abilene_subdivisions(page)

        if not all_subdivisions:
            print("No subdivisions found.")
            await browser.close()
            return

        print(f"\n{len(all_subdivisions)} subdivisions to process.\n")

        # Step 2: Loop subdivisions - TEST: Only first subdivision
        test_subdivisions = all_subdivisions  # Only first subdivision for testing
        for idx, subdiv_name in enumerate(test_subdivisions, 1):
            if subdiv_name in done_subdivisions:
                print(f"Skip [{idx}/{len(test_subdivisions)}]: {subdiv_name}")
                continue

            print(f"\n[TEST - {idx}/{len(test_subdivisions)}] {subdiv_name}")

            # Search this subdivision
            await go_to_by_address(page)
            ok = await search_subdivision(page, subdiv_name)
            if not ok:
                print(f"  Search failed. Skipping.")
                continue

            # Collect all property IDs from results table
            props = await collect_property_ids(page)
            print(f"  {len(props)} R-type properties found")

            # Step 3: For each property, open detail page and scrape
            for prop in props:
                pid = prop["prop_id"]
                if pid in done_property_ids:
                    print(f"    Skip: {pid}")
                    continue

                print(f"    {pid} | {prop['owner_name']}")

                detail = await scrape_detail(page, prop, context)
                await asyncio.sleep(DELAY_SEC)

                # Use tax totals from detail page extraction
                taxes = detail.get("tax_totals", {})

                append_to_xlsx({
                    "Owner Name":          prop["owner_name"],
                    "Owner ID":            prop.get("owner_id", ""),
                    "Property ID":         pid,
                    "Type":                "R",
                    "Situs Address":       prop["situs_addr"],
                    "Legal Description":   prop["legal_desc"],
                    "Mailing Address":     detail["mailing_address"],
                    "Assessed Value 2025": detail["assessed_value"],
                    "Deed Date":           detail["deed_date"],
                    "Living Area":         detail["living_area"],
                    "Year Built":          detail["year_built"],
                    "Amount Due 2025":     taxes.get("2025", "$0"),
                    "Amount Due 2024":     taxes.get("2024", "$0"),
                    "Amount Due 2023":     taxes.get("2023", "$0"),
                })
                done_property_ids.add(pid)
                cp["done_property_ids"] = list(done_property_ids)
                save_checkpoint(cp)
                print(f"    Saved: {prop['owner_name']} | {pid}")

            done_subdivisions.add(subdiv_name)
            cp["done_subdivisions"] = list(done_subdivisions)
            save_checkpoint(cp)
            print(f"  Done: {subdiv_name}")

        print(f"\nComplete! File: {OUTPUT_XLSX}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape())