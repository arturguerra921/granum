import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('http://127.0.0.1:8050')
    time.sleep(2) # wait for load

    page.evaluate("document.querySelector('.modal-content .btn').click()")
    time.sleep(1)

    # Find the "Configuração do Modelo" tab and click
    page.locator("text=Configuração do Modelo").click()
    time.sleep(2)

    # Click the "Rodar Modelo" button
    page.locator("#btn-run-model").click()
    time.sleep(0.5)

    # Verify the modal is visible immediately after click
    print("Modal visible after Run click?", page.is_visible('#modal-model-running .modal-content'))

    # Let the error message show up ("Faltam dados") and wait for modal to close
    time.sleep(2)
    print("Modal visible after error?", page.is_visible('#modal-model-running .modal-content'))

    browser.close()
