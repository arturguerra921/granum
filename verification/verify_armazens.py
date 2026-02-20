from playwright.sync_api import sync_playwright, expect
import time
import os

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    # 1. Navigate to the app
    print("Navigating to app...")
    page.goto("http://127.0.0.1:8050/")

    # Wait for the page to load
    page.wait_for_selector("#main-tabs")

    # 2. Click on "Armazéns" tab
    print("Clicking Armazéns tab...")
    page.locator("#main-tabs a:has-text('Armazéns')").click()

    # Wait for the content to load
    page.wait_for_selector("#btn-load-base")

    # 3. Verify Buttons exist
    print("Verifying buttons...")
    expect(page.locator("#btn-load-base")).to_be_visible()
    expect(page.locator("#btn-restore-base")).to_be_visible()
    expect(page.locator("#btn-reconstruct-base")).to_be_visible()
    expect(page.locator("#btn-save-base")).to_be_visible()

    # Take screenshot of the tab
    if not os.path.exists("verification"):
        os.makedirs("verification")
    page.screenshot(path="verification/armazens_tab.png")
    print("Screenshot saved: verification/armazens_tab.png")

    # 4. Test "Reconstruir a Base" Workflow
    print("Testing Reconstruct Workflow...")
    # Click "Reconstruir a Base" -> Should open Tutorial Modal
    page.click("#btn-reconstruct-base")

    # Wait for Modal
    page.wait_for_selector("#modal-tutorial")
    expect(page.locator("#modal-tutorial .modal-title")).to_have_text("Como Atualizar a Base")

    # Take screenshot of Modal
    page.screenshot(path="verification/tutorial_modal.png")
    print("Screenshot saved: verification/tutorial_modal.png")

    # Close Modal -> Should show Upload
    print("Closing modal...")
    page.click("#close-modal-tutorial")

    # Wait for Upload to be visible
    # The container has id="upload-reconstruct-container"
    page.wait_for_selector("#upload-reconstruct-container", state="visible")
    expect(page.locator("#upload-reconstruct-container")).to_be_visible()

    # Take screenshot of Upload visible
    page.screenshot(path="verification/upload_visible.png")
    print("Screenshot saved: verification/upload_visible.png")

    # 5. Test "Salvar na Base" Workflow
    print("Testing Save Workflow...")
    page.click("#btn-save-base")

    # Wait for Modal
    page.wait_for_selector("#modal-confirm-save")
    expect(page.locator("#modal-confirm-save .modal-body")).to_contain_text("irreversível")

    # Take screenshot of Save Modal
    page.screenshot(path="verification/save_modal.png")
    print("Screenshot saved: verification/save_modal.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
