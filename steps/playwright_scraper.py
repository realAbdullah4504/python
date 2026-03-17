from playwright.sync_api import sync_playwright
from typing import Tuple
from bs4 import BeautifulSoup

def setup_browser_context(headless: bool = True) -> Tuple:
    """Setup and return browser context and main page"""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context()
    return playwright, browser, context


def open_page(url: str):
    """Open a page in the browser"""
    playwright, browser, context = setup_browser_context()
    page = context.new_page()
    page.goto(url)
    page.wait_for_load_state("networkidle")
    return page

if __name__ == "__main__":
    page = open_page("https://www.csjn.gov.ar/transparencia/adquisiciones-y-contrataciones")
    html = page.content()
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a")
    print(links)