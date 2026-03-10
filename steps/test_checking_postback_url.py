from playwright.sync_api import sync_playwright

URL = "https://comprar.gob.ar/Compras.aspx?qs=W1HXHGHtH10="
target = "ctl00$CPH1$GridListaPliegosAperturaProxima$ctl02$lnkNumeroProceso"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL, wait_until="networkidle")
    
    # Check if the element exists
    elem_id = target.replace('$', '_')
    print("Element ID:", elem_id)
    
    link = page.locator(f"#{elem_id}")
    
    if link.count() > 0:
        with page.expect_navigation():
            link.click()
        print("New URL:", page.url)
    else:
        print("Element not found")
    browser.close()
