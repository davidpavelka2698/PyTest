import pytest
from pages.idle import idle_screen_displayed
from pages.sale_helpers import *
from pages.transactions import *
from conftest import test_data


@pytest.mark.record_xml_attribute(name="Verify approving manual sale+tip in various currencies. Terminal default - "
                                       "CZK.")
@pytest.mark.parametrize("init_profileID", ["APOS0015"], indirect=True)
def test_sale_tip_multicurrency(driver, init_profileID, delete_batch):

    # Transaction data
    card = test_data.get("cards").get("mastercard")
    currency = test_data.get("currency")
    tip_amounts = test_data.get("amounts_tips").values()
    amount = "1"

    for transaction_currency in currency:
        for tip_amount in tip_amounts:
            # Initiate sale and enter card data
            initiate_manual_sale_tip(driver, amount, transaction_currency, card, tip_amount)

            # Approve manual transaction
            approve_manual_transaction(driver)

            # Check if the idle screen is displayed
            idle_screen_displayed(driver=driver)


@pytest.mark.record_xml_attribute(name="Verify manual sale + declining tip in various currencies. Terminal default - "
                                       "CZK.")
@pytest.mark.parametrize("init_profileID", ["APOS0015"], indirect=True)
def test_sale_tip_declined(driver, init_profileID, delete_batch):

    # Transaction data
    amount = "1"
    tip_amount = "0"
    card = test_data.get("cards").get("mastercard")
    currency = test_data.get("currency")

    for transaction_currency in currency:
        # Initiate sale and enter card data
        initiate_manual_sale_tip(driver, amount, transaction_currency, card, tip_amount, tip_option="no")

        # Approve manual transaction
        approve_manual_transaction(driver)

        # Check if the idle screen is displayed
        idle_screen_displayed(driver=driver)


@pytest.mark.record_xml_attribute(name="Verify manual sale + declining tip in CZK. Terminal default - CZK.")
@pytest.mark.parametrize("init_profileID", ["APOS0015"], indirect=True)
def test_sale_tip_expiredcard(driver, init_profileID, delete_batch):

    # Transaction data
    card = test_data.get("cards").get("expired")
    amount = "1"
    tip_amount = "1"
    transaction_currency = "CZK"

    # Initiate sale and enter card data
    initiate_manual_sale_tip(driver, amount, transaction_currency, card, tip_amount)

    # Asserting card read correctly
    assert "Expirovaná karta" in conftest.get_element_text_with_retry(driver, bel.text_view)

    WebDriverWait(driver, 30).until(EC.presence_of_element_located(bel.no_button))
    declined = driver.find_element(*bel.no_button).text
    assert declined == "BERU NA VĚDOMÍ", f"Expected 'BERU NA VĚDOMÍ', got '{declined}'."

    # Confirm an expired card announcement
    conftest.click_element_with_retry(driver, bel.no_button)

    # Check if the idle screen is displayed
    idle_screen_displayed(driver=driver)


@pytest.mark.record_xml_attribute(name="Verify declining manual sale+tip with invalidPAN. Terminal default - CZK.")
@pytest.mark.parametrize("init_profileID", ["APOS0015"], indirect=True)
def test_sale_tip_invalidPAN(driver, init_profileID, delete_batch):

    # Transaction data
    amount = "1"
    tip_amount = "1"
    card = test_data.get("cards").get("invalid_PAN")
    transaction_currency = "CZK"

    # Initiate sale and enter card data
    initiate_manual_sale_tip(driver, amount, transaction_currency, card, tip_amount)

    # Asserting card read correctly
    card_read_correctly = WebDriverWait(driver, 30).until(
        EC.text_to_be_present_in_element(bel.text_view, "Nepodporovaná karta"))
    assert card_read_correctly

    WebDriverWait(driver, 30).until(EC.presence_of_element_located(bel.no_button))
    declined = driver.find_element(*bel.no_button).text
    assert declined == "BERU NA VĚDOMÍ", f"Expected 'BERU NA VĚDOMÍ', got '{declined}'."

    # Confirm an expired card announcement
    conftest.click_element_with_retry(driver, bel.no_button)

    # Check if the idle screen is displayed
    idle_screen_displayed(driver=driver)
