from playwright.sync_api import sync_playwright

USER_DATA_DIR = "playwright_profile"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        USER_DATA_DIR,
        headless=False,   # must be visible — you need to see and interact with it
    )
    page = context.new_page()
    page.goto("https://ums.lpu.in/lpuums/")

    input("Log in manually in the browser window, then press Enter here once you're on the dashboard...")

    context.close()