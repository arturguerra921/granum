import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://127.0.0.1:8050')
    time.sleep(2) # wait for load

    page.evaluate("document.querySelector('.modal-content .btn').click()")
    time.sleep(1)

    print("Initial check:", page.is_visible('#modal-model-running .modal-content'))

    page.evaluate("document.getElementById('lang-en').click()")
    time.sleep(2)
    print("Modal visible after en click?", page.is_visible('#modal-model-running .modal-content'))

    # Try doing it again
    page.evaluate("document.getElementById('lang-en').click()")
    time.sleep(2)
    print("Modal visible after en click again?", page.is_visible('#modal-model-running .modal-content'))

    page.evaluate("document.getElementById('lang-pt').click()")
    time.sleep(2)
    print("Modal visible after pt click?", page.is_visible('#modal-model-running .modal-content'))

    browser.close()
