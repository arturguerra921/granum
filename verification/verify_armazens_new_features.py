from playwright.sync_api import sync_playwright, expect

def test_armazens_kpi_and_filter(page):
    # Set a large viewport to minimize scrolling issues
    page.set_viewport_size({"width": 1280, "height": 1024})

    # 1. Arrange: Go to the app
    page.goto("http://127.0.0.1:8050/")

    # 2. Act: Click on "Armazéns" tab
    page.get_by_role("tab", name="Armazéns").click()

    # Wait for the tab content to be visible
    expect(page.locator("#table-armazens")).to_be_visible()

    # 3. Debug: Scroll to bottom
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    # 4. Assert: Check for new KPI cards
    # Use scroll_into_view_if_needed() just to be sure
    public_kpi = page.locator("#metric-armazens-public")
    public_kpi.scroll_into_view_if_needed()

    # Check visibility
    expect(public_kpi).to_be_visible()
    expect(page.locator("#metric-armazens-private")).to_be_visible()

    # 5. Assert: Check for filter inputs in the table
    # Dash DataTable native filtering adds inputs to the headers
    # We can check for the presence of input elements inside the table header/filter cells
    # The class usually involves 'dash-filter'
    expect(page.locator(".dash-filter input").first).to_be_visible()

    page.screenshot(path="verification/armazens_kpi_filter.png")
    print("Screenshot saved to verification/armazens_kpi_filter.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            test_armazens_kpi_and_filter(page)
        except Exception as e:
            print(f"Test failed: {e}")
            page.screenshot(path="verification/error.png")
        finally:
            browser.close()
