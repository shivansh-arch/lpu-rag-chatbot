from datetime import datetime
from playwright.sync_api import Page


# ============================================================
# REAL IDs
# ============================================================

TERM_ID = "ctl00_cphHeading_ddlLeaveTerm"
LEAVE_TYPE_ID = "ctl00_cphHeading_drpLeaveType"
VISIT_PLACE_ID = "ctl00_cphHeading_ddlVisitDay"

RELATIVE_MOBILE_ID = "ctl00_cphHeading_txtVisitingMobile"

START_PICKER_ID = "ctl00_cphHeading_startdateRadDateTimePicker1"
START_INPUT_ID = "ctl00_cphHeading_startdateRadDateTimePicker1_dateInput"

END_PICKER_ID = "ctl00_cphHeading_enddateRadDateTimePicker2"
END_INPUT_ID = "ctl00_cphHeading_enddateRadDateTimePicker2_dateInput"

REASON_ID = "ctl00_cphHeading_txtLeaveReason"


# ============================================================
# WAIT FOR ASP.NET AJAX POSTBACK, IF ONE IS OCCURRING
# ============================================================

def wait_for_async_postback(page: Page):
    """
    Wait for an ASP.NET UpdatePanel-style AJAX postback to finish.

    If the page does not use ASP.NET AJAX, this simply returns.
    """

    page.wait_for_function(
        """
        () => {
            // ASP.NET AJAX is not present.
            if (
                !window.Sys ||
                !Sys.WebForms ||
                !Sys.WebForms.PageRequestManager
            ) {
                return true;
            }

            const manager =
                Sys.WebForms.PageRequestManager.getInstance();

            return !manager.get_isInAsyncPostBack();
        }
        """,
        timeout=10000,
    )


# ============================================================
# SET TELERIK DATE/TIME
# ============================================================
def set_telerik_datetime(page, picker_id, value):
    date_string = value.strftime("%Y-%m-%dT%H:%M:%S")

    script = f"""
    (function() {{
        var picker = $find('{picker_id}');
        if (!picker) {{ throw new Error('Picker not found: {picker_id}'); }}
        var date = new Date('{date_string}');
        picker.set_selectedDate(date);
        picker.updateClientState();
    }})();
    """

    page.add_script_tag(content=script)

# ============================================================
# READ TELERIK DATE/TIME
# ============================================================

def get_telerik_datetime(
    page: Page,
    picker_id: str,
):
    """
    Read the actual selected date from Telerik.

    Returns an ISO-like datetime string or None.
    """

    return page.evaluate(
        """
        (pickerId) => {

            const picker = $find(pickerId);

            if (!picker) {
                throw new Error(
                    `RadDateTimePicker not found: ${pickerId}`
                );
            }

            const date = picker.get_selectedDate();

            if (!date) {
                return null;
            }

            return {
                timestamp: date.getTime(),
                iso: date.toISOString()
            };
        }
        """,
        picker_id,
    )


# ============================================================
# VERIFY DROPDOWN
# ============================================================

def verify_select(
    page: Page,
    element_id: str,
    expected_label: str,
):
    """
    Verify the currently selected <option>.
    """

    result = page.locator(
        f"#{element_id}"
    ).evaluate(
        """
        (select) => {

            const option =
                select.options[select.selectedIndex];

            return {
                value: select.value,
                label: option ? option.textContent.trim() : ""
            };
        }
        """
    )

    actual_label = result["label"]

    if actual_label != expected_label:
        raise AssertionError(
            f"{element_id} mismatch: "
            f"expected {expected_label!r}, "
            f"got {actual_label!r}"
        )

    return actual_label


# ============================================================
# VERIFY TELERIK DATE
# ============================================================

def verify_telerik_datetime(
    page: Page,
    picker_id: str,
    expected: datetime,
):
    """
    Compare Telerik's actual selected date/time
    against the datetime we intended to set.
    """

    actual = get_telerik_datetime(
        page,
        picker_id,
    )

    if actual is None:
        raise AssertionError(
            f"{picker_id}: Telerik has no selected date"
        )

    expected_timestamp = int(
        expected.timestamp() * 1000
    )

    actual_timestamp = actual["timestamp"]

    # Compare to the minute rather than requiring
    # millisecond-level equality.
    actual_dt = datetime.fromtimestamp(
        actual_timestamp / 1000
    )

    actual_key = (
        actual_dt.year,
        actual_dt.month,
        actual_dt.day,
        actual_dt.hour,
        actual_dt.minute,
    )

    expected_key = (
        expected.year,
        expected.month,
        expected.day,
        expected.hour,
        expected.minute,
    )

    if actual_key != expected_key:
        raise AssertionError(
            f"{picker_id} mismatch: "
            f"expected {expected}, "
            f"got {actual_dt}"
        )

    return actual_dt


# ============================================================
# VERIFY ALL FORM FIELDS
# ============================================================

def verify_hostel_leave_form(
    page: Page,
    leave_type: str,
    visit_place: str,
    start_datetime: datetime,
    end_datetime: datetime,
    reason: str,
    relative_mobile: str,
):
    """
    Read the LIVE page state and verify it against
    the values we intended to enter.
    """

    # --------------------------------------------------------
    # Leave Type
    # --------------------------------------------------------

    actual_leave_type = verify_select(
        page,
        LEAVE_TYPE_ID,
        leave_type,
    )

    # --------------------------------------------------------
    # Visit Place
    # --------------------------------------------------------

    actual_visit_place = verify_select(
        page,
        VISIT_PLACE_ID,
        visit_place,
    )

    # --------------------------------------------------------
    # Relative Mobile
    # --------------------------------------------------------

    actual_mobile = page.locator(
        f"#{RELATIVE_MOBILE_ID}"
    ).input_value()

    if actual_mobile != relative_mobile:
        raise AssertionError(
            f"Relative mobile mismatch: "
            f"expected {relative_mobile!r}, "
            f"got {actual_mobile!r}"
        )

    # --------------------------------------------------------
    # Reason
    # --------------------------------------------------------

    actual_reason = page.locator(
        f"#{REASON_ID}"
    ).input_value()

    if actual_reason != reason:
        raise AssertionError(
            f"Reason mismatch: "
            f"expected {reason!r}, "
            f"got {actual_reason!r}"
        )

    # --------------------------------------------------------
    # Start Date/Time
    # --------------------------------------------------------

    actual_start = verify_telerik_datetime(
        page,
        START_PICKER_ID,
        start_datetime,
    )

    # --------------------------------------------------------
    # End Date/Time
    # --------------------------------------------------------

    actual_end = verify_telerik_datetime(
        page,
        END_PICKER_ID,
        end_datetime,
    )

    # --------------------------------------------------------
    # Acknowledgement
    # --------------------------------------------------------

    acknowledgement_row = page.locator(
        "tr",
        has_text="By submitting this hostel leave application"
    )

    checkbox = acknowledgement_row.locator(
        'input[type="checkbox"]'
    )

    if checkbox.count() != 1:
        raise AssertionError(
            "Could not uniquely locate acknowledgement checkbox"
        )

    if not checkbox.is_checked():
        raise AssertionError(
            "Acknowledgement checkbox is NOT checked"
        )

    # --------------------------------------------------------
    # REAL verification output
    # --------------------------------------------------------

    print("\n========== FORM VERIFICATION ==========")
    print(f"Leave Type      : {actual_leave_type}")
    print(f"Visit Place     : {actual_visit_place}")
    print(f"Relative Mobile : {actual_mobile}")
    print(f"Start Date/Time  : {actual_start}")
    print(f"End Date/Time    : {actual_end}")
    print(f"Reason           : {actual_reason}")
    print("Acknowledgement  : CHECKED")
    print("=======================================\n")

    return True


# ============================================================
# FILL FORM
# ============================================================

def fill_hostel_leave_form(
    page: Page,
    leave_type: str,
    visit_place: str,
    start_datetime: datetime,
    end_datetime: datetime,
    reason: str,
    relative_mobile: str,
):
    """
    Fill the hostel leave form.

    IMPORTANT:
    This function NEVER submits the application.
    """

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if end_datetime <= start_datetime:
        raise ValueError(
            "End datetime must be later than start datetime."
        )

    # --------------------------------------------------------
    # Leave Type
    # --------------------------------------------------------

    page.locator(
        f"#{LEAVE_TYPE_ID}"
    ).select_option(
        label=leave_type
    )

    # Give the ASP.NET postback time to begin/finish
    # if it is an AJAX UpdatePanel request.
    wait_for_async_postback(page)

    # --------------------------------------------------------
    # Visit Place
    # --------------------------------------------------------

    page.locator(
        f"#{VISIT_PLACE_ID}"
    ).select_option(
        label=visit_place
    )

    wait_for_async_postback(page)

    # --------------------------------------------------------
    # Relative Mobile
    # --------------------------------------------------------

    page.locator(
        f"#{RELATIVE_MOBILE_ID}"
    ).fill(relative_mobile)

    # --------------------------------------------------------
    # Start Date/Time
    # --------------------------------------------------------

    set_telerik_datetime(
        page,
        START_PICKER_ID,
        start_datetime,
    )

    # --------------------------------------------------------
    # End Date/Time
    # --------------------------------------------------------

    set_telerik_datetime(
        page,
        END_PICKER_ID,
        end_datetime,
    )

    # --------------------------------------------------------
    # Reason
    # --------------------------------------------------------

    page.locator(
        f"#{REASON_ID}"
    ).fill(reason)

    # --------------------------------------------------------
    # Acknowledgement checkbox
    # --------------------------------------------------------

    acknowledgement_row = page.locator(
        "tr",
        has_text="By submitting this hostel leave application"
    )

    checkbox = acknowledgement_row.locator(
        'input[type="checkbox"]'
    )

    if checkbox.count() != 1:
        raise RuntimeError(
            "Could not uniquely locate acknowledgement checkbox."
        )

    if not checkbox.is_checked():
        checkbox.check()

    # --------------------------------------------------------
    # ACTUAL READBACK VERIFICATION
    # --------------------------------------------------------

    verify_hostel_leave_form(
        page=page,
        leave_type=leave_type,
        visit_place=visit_place,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        reason=reason,
        relative_mobile=relative_mobile,
    )

    print("Form filled and verified.")
    print("SUBMIT WAS NOT CLICKED.")


# ============================================================
# SUBMIT -- DELIBERATELY SEPARATE
# ============================================================

def submit_hostel_leave_form(page: Page):
    """
    Explicit submit operation.

    This is intentionally separate from filling.
    """

    submit_button = page.locator(
        'input[type="submit"][value="Submit"], '
        'input[type="button"][value="Submit"], '
        'button:has-text("Submit")'
    ).first

    if not submit_button.is_visible():
        raise RuntimeError(
            "Submit button not found."
        )

    submit_button.click()