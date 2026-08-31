from playwright.sync_api import sync_playwright
from automation import fill_hostel_leave_form
from datetime import datetime, timedelta

FORM_URL = "https://ums.lpu.in/lpuums/frmStudentHostelLeaveApplicationTermWise.aspx"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    context = browser.contexts[0]
    page = context.pages[0]

    # ALWAYS start fresh on the form page — don't assume
    # the tab is already in the right state from a previous run
    page.goto(FORM_URL)
    page.wait_for_load_state("domcontentloaded")

    # Sanity check: if this redirected to login, stop immediately
    # instead of failing confusingly deep inside select_option later
    if "Login" in page.url:
        raise RuntimeError(
            f"Session expired or not logged in — landed on {page.url}. "
            "Log in manually in the Chrome window, then re-run."
        )

    fill_hostel_leave_form(
        page=page,
        leave_type="Night Leave",
        visit_place="Home",
        start_datetime=datetime.now() + timedelta(days=1),
        end_datetime=datetime.now() + timedelta(days=2),
        reason="Test run",
        relative_mobile="9264232328",
    )

    input("Check the browser window, then press Enter to close this script...")