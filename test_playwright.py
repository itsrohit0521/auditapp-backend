from playwright.sync_api import sync_playwright
import threading

def test():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com")
        print(page.title())
        browser.close()

t = threading.Thread(target=test)
t.start()
t.join()
