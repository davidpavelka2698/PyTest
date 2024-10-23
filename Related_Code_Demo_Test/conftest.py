import os
import subprocess
import pytest
from appium import webdriver
from appium.options.android import UiAutomator2Options
import pytest_html.extras
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import NoSuchElementException
from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.appium_service import AppiumService
from utils import basic_elements
from utils import helpers
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pages import settings_menu, transactions
import pytest_html
import json
import pandas as pd


def create_appium_driver():
    appium_server_url = 'http://localhost:4724'
    capabilities = dict(
        platformName='Android',
        automationName='uiautomator2',
        deviceName='Android',
        appPackage='com.payten.apos',
        appActivity='.gui.MainActivity',
        noReset=True
    )
    appium_driver = webdriver.Remote(appium_server_url, options=UiAutomator2Options().load_capabilities(capabilities))

    # Set implicit wait for 5 seconds
    appium_driver.implicitly_wait(5)

    return appium_driver


@pytest.fixture(scope="session", autouse=True)
def driver():
    # Start Appium service
    appium_service = AppiumService()
    appium_service.start(args=['--port', '4724'])

    # Ensure the 'temp' and 'screenshots' folders exist
    temp_folder = 'temp'
    screenshots_folder = 'screenshots'
    helpers.ensure_directory_exists(temp_folder)
    helpers.ensure_directory_exists(screenshots_folder)

    # Clean up the folders
    helpers.delete_folder_content(temp_folder)
    helpers.delete_folder_content(screenshots_folder)

    # Delete the content of the previous test session in the temporary folders
    helpers.delete_folder_content('temp')
    helpers.delete_folder_content('screenshots')

    # Initialize the Appium driver with error handling
    driver = None
    try:
        driver = create_appium_driver()
    except Exception as e:
        pytest.fail(f"Test setup failed: {e}")

    yield driver

    driver.quit()

    # Stop Appium service
    appium_service.stop()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()

    # Show test name (function name)
    test_name = item.name

    # Get description from the record_xml_attribute marker if present
    description = None
    marker = item.get_closest_marker("record_xml_attribute")
    if marker and marker.kwargs.get("name"):
        description = marker.kwargs.get("name")

    # You can append the description to the test name or just display the test name
    if description:
        rep.nodeid = f"{test_name} - {description}"  # Shows both test name and description
    else:
        rep.nodeid = test_name  # Show only the test name if no description

    # Handle test failure and add screenshot as before
    if rep.when == "call" and rep.failed:
        driver = item.funcargs['driver']
        screenshot_dir = 'screenshots'
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(screenshot_dir, f"{test_name}.png")
        driver.save_screenshot(screenshot_path)

        # Add screenshot to HTML report
        extras = getattr(rep, 'extras', [])
        extras.append(pytest_html.extras.image(screenshot_path))
        rep.extras = extras

        print(f"Screenshot saved as {screenshot_path}")


# Clicks on element with retry if the stale element exception is detected.

def click_element_with_retry(driver, element_locator, retries=3):
    for i in range(retries):
        try:
            element = driver.find_element(*element_locator)
            element.click()
            return
        except StaleElementReferenceException:
            if i < retries - 1:
                continue
            else:
                raise


# Returns a text of the element with retry if the stale element exception is detected.

def get_element_text_with_retry(driver, element_locator, retries=3):
    for i in range(retries):
        try:
            element = driver.find_element(*element_locator)
            return element.text
        except StaleElementReferenceException:
            if i < retries - 1:
                continue
            else:
                raise


# Returns if an element is displayed with retry if the stale element exception is detected.

def is_element_displayed_with_retry(driver, element_locator, retries=3):
    for i in range(retries):
        try:
            element = driver.find_element(*element_locator)
            return element.is_displayed
        except StaleElementReferenceException:
            if i < retries - 1:
                continue
            else:
                raise


# Returns True if element is not present with retry if the stale element exception is detected.
def is_element_not_present(driver, element_locator):
    try:
        elements = driver.find_elements(*element_locator)
        return len(elements) == 0
    except NoSuchElementException:
        return True


# Checks and changes profileID which is required for the test case. Needs to be called in test function.
@pytest.fixture
def init_profileID(driver, request):
    # Create a wait object with 30-second timeout
    wait = WebDriverWait(driver, 30)

    # Element ending with text
    succ_text = (AppiumBy.XPATH, '//*[ends-with(@text, "Profil úspěšně stažen")]')

    profileID_value = request.param if hasattr(request, 'param') else 'APOS0001'  # Check whether there is any
    # profile, if not, set APOS0001 as new profile.

    # If current profileID and profileID is the same, no change is needed
    if helpers.check_current_PID(driver, profileID_value):

        # Kills and starts the application to avoid the situation when the idle screen is not displayed
        driver.terminate_app(app_id="com.payten.apos")
        driver.activate_app(app_id="com.payten.apos")

        # Wait until the idle screen is displayed
        wait.until(EC.presence_of_element_located(basic_elements.side_menu_button))

    # If current profileID is different, change PID and do init
    else:
        helpers.change_PID_in_init_config(driver, profileID_value)

        # Kills and starts the application to avoid the situation when the idle screen is not displayed
        driver.terminate_app(app_id="com.payten.apos")
        driver.activate_app(app_id="com.payten.apos")

        # Wait until the idle screen is displayed
        wait.until(EC.presence_of_element_located(basic_elements.side_menu_button))

        # Perform initialization
        settings_menu.start_init_from_idle(driver)

        # Wait until successful text of init result is displayed
        wait.until(EC.presence_of_element_located(succ_text))

        wait.until(EC.presence_of_element_located(basic_elements.cancel_button))

        click_element_with_retry(driver, basic_elements.cancel_button)


# Performs automatic handshake after starting session to sync EPAS exchangeID with BPnode
# @pytest.fixture(scope='session', autouse=True)
# def perform_handshake(driver, acquirer='SIA'):
#     def terminate_and_activate_app():
#         """Terminate and reactivate the app to ensure it starts in the correct state."""
#         driver.terminate_app(app_id="com.payten.apos")
#         driver.activate_app(app_id="com.payten.apos")
#         wait.until(EC.presence_of_element_located(basic_elements.side_menu_button))
#
#     def initialize_application():
#         """Handle application initialization after a failure."""
#         succ_text = (AppiumBy.XPATH, '//*[ends-with(@text, "Profil úspěšně stažen")]')
#
#         click_element_with_retry(driver, basic_elements.cancel_button)
#         helpers.delete_batch(driver)
#         click_element_with_retry(driver, basic_elements.cancel_button)
#         helpers.change_PID_in_init_config(driver, "APOS0001")
#
#         terminate_and_activate_app()
#
#         # Start initialization
#         settings_menu.start_init_from_idle(driver)
#
#         # Wait until successful initialization message is displayed
#         wait.until(EC.presence_of_element_located(succ_text))
#         wait.until(EC.presence_of_element_located(basic_elements.cancel_button))
#         click_element_with_retry(driver, basic_elements.cancel_button)
#
#     def start_handshake():
#         """Start the handshake process."""
#         transactions.start_handshake_from_menu(driver)
#         acquirer_button = (AppiumBy.XPATH, f'//*[@text= "{acquirer}"]')
#         click_element_with_retry(driver, acquirer_button)
#         WebDriverWait(driver, 5).until(EC.presence_of_element_located(basic_elements.confirm_button))
#         click_element_with_retry(driver, basic_elements.confirm_button)
#
#     # Create a wait object with 30-second timeout
#     wait = WebDriverWait(driver, 30)
#
#     # Initial app setup
#     terminate_and_activate_app()
#
#     # Perform handshake
#     try:
#         start_handshake()
#     except Exception as e:
#         # Handle initialization failure and retry handshake
#         initialize_application()
#         start_handshake()


# Delete batch after finishing test case. Needs to be called in test function
@pytest.fixture
def delete_batch(driver):
    yield
    helpers.delete_batch(driver)


def load_test_data(file_path='test_data.json'):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# Load data once and make it available as a global variable
test_data = load_test_data()


# Changes display and font scaling at the start of testing
@pytest.fixture(scope='session', autouse=True)
def set_device_display_and_font_scale():
    # Fixture to set the display size and font scale at the start of the session.
    display_size()
    font_scale()


# Runs adb command in android software directly
def run_adb_command(command):
    # to get settings properties:  adb shell settings list system
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        if result.stderr:
            print(f"Command Error: {result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}")


# Sets scaling of font on specified parameter
def font_scale():
    font_scales = {
        "small": "0.85",
        "default": "1",
        "large": "1.15",
        "very_large": "1.3"
    }
    run_adb_command(f'adb shell settings put system font_scale {font_scales["default"]}')


# Sets scaling of screen on specified parameter
def display_size():
    density = {
        "small": "180",
        "default": "213",
        "large": "240"
    }
    run_adb_command(f'adb shell wm density {density["default"]}')


def pytest_configure(config):
    # Register the custom marker for record_xml_attribute
    config.addinivalue_line(
        "markers", "record_xml_attribute(name): Add a description to the test."
    )


# Do not change function name (pytest_collection_modifyitems)!
# Hook to modify the collected test items and write to an Excel file
def pytest_collection_modifyitems(config, items):
    # Define the Excel file name
    excel_file_name = "TestList.xlsx"

    # Prepare a list to hold the test data
    test_data = []

    # Loop through the collected test items
    for index, item in enumerate(items, start=1):
        # Choosing data to be imported to CSV
        test_path = os.path.relpath(item.location[0])
        test_name = item.name

        # Extract the PID from the test name
        try:
            test_PID = test_name.split("[")[1].strip("]")  # Extract PID and remove the trailing ']'
        except IndexError:
            test_PID = "APOS0001"  # Default value if no PID is found

        # Initialize the description variable
        description = "NO DESCRIPTION ADDED"

        # Check if the test has the "record_xml_attribute" marker
        if "record_xml_attribute" in item.keywords:
            # Get the marker and retrieve the "name" argument from it
            marker = item.get_closest_marker("record_xml_attribute")
            if marker and marker.kwargs.get("name"):
                name = marker.kwargs.get("name")
                description = name  # Use the name from the marker as the description
                item._nodeid = name

        test_name = test_name.split('[')[0]
        # Append the data to the list, regardless of whether the marker is present
        test_data.append([index, test_name, test_PID, description, test_path])

    # Create a DataFrame from the test data
    df = pd.DataFrame(test_data, columns=["No.", "Name", "PID", "Description", "Path"])

    # Save the DataFrame to an Excel file
    df.to_excel(excel_file_name, index=False)  # Save without the index
