from playwright.sync_api import sync_playwright
from typing import Tuple
import time


def setup_browser_context(headless: bool = True) -> Tuple:
    """Setup and return browser context and main page"""
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context()
    return playwright, browser, context


def navigate_to_main_page(context, url: str):
    """Navigate to the main listing page and return the page object"""
    page = context.new_page()
    page.goto(url)
    page.wait_for_load_state("networkidle")
    return page


def open_page(url: str):
    """Open a page in the browser"""
    playwright, browser, context = setup_browser_context()
    page = context.new_page()
    page.goto(url)
    page.wait_for_load_state("networkidle")
    return page


def simulate_postback(page, target: str, argument: str = "", retries: int = 3) -> str:
    """Simulate a postback event on the page"""
    print(f"Executing postback: target={target}, argument={argument}")

    old_url = page.url

    page.evaluate(f"__doPostBack('{target}','{argument}')")

    try:
        page.wait_for_url(lambda url: url != old_url, timeout=5000)
        print("Navigation happened")
    except Exception as e:
        print(f"No navigation, waiting for DOM update: {e}")
        page.wait_for_load_state("networkidle")

    return page.content()


def simulate_postback_with_retry(page, target, argument="", retries=3):
    """Simulate postback with retry logic and return HTML and real URL"""
    print(f"Executing postback: target={target}, argument={argument}")

    for attempt in range(1, retries + 1):
        try:
            print(f"Attempt {attempt}/{retries}")

            old_url = page.url

            # Execute the postback
            page.evaluate(f"__doPostBack('{target}','{argument}')")

            try:
                page.wait_for_url(lambda url, old=old_url: url != old, timeout=5000)
                print("Navigation happened")
            except Exception:
                print("No navigation, waiting for DOM update")
                page.wait_for_load_state("networkidle")

            time.sleep(1)

            html = page.content()
            real_url = page.url

            return html, real_url

        except Exception as e:
            print(f"Postback failed: {e}")

            if attempt == retries:
                print("Max retries reached. Raising error.")
                raise

            print("Retrying...\n")
            time.sleep(2)


def cleanup_browser_resources(playwright, browser) -> None:
    """Clean up browser resources with proper error handling"""
    try:
        if browser:
            browser.close()
        if playwright:
            playwright.stop()
    except Exception as e:
        print(f"Warning: Error during browser cleanup: {e}")
        # Try to force cleanup if normal close fails
        try:
            if 'playwright' in locals():
                playwright.stop()
        except RuntimeError:
            pass
