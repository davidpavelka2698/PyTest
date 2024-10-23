import utils.basic_elements as bel
import conftest
from pages import transactions
from utils import helpers
from conftest import test_data


def initiate_manual_sale_cashback(driver, amount, card, cashback_amount, transaction_currency="CZK",
                                  cashback_option="yes", expect_approve="yes"):
    # Transaction data
    currency = test_data.get("currency")

    if cashback_option == "yes":
        button = bel.yes_button
        title = "Prodej + Cashback"
    else:
        button = bel.no_button
        title = "Prodej"

    chosen_currency = currency.get(transaction_currency)

    # Select currency
    helpers.select_currency(driver, transaction_currency)

    # Enter amount on numeric keyboard
    helpers.enter_value_on_numeric_keyboard(driver, amount)

    # Check if cashback offer is displayed
    assert "Přejete si cashback?" in conftest.get_element_text_with_retry(driver, bel.text_view)

    # Check if NO button contains correct text
    assert "NE" in conftest.get_element_text_with_retry(driver, bel.no_button)

    # Check if YES button contains correct text
    assert "ANO" in conftest.get_element_text_with_retry(driver, bel.yes_button)

    # Click on the button for cashback
    conftest.click_element_with_retry(driver, button)

    if cashback_option == "yes":
        # Check if a cashback text is displayed
        assert "Zadejte cashback" in conftest.get_element_text_with_retry(driver, bel.text_view)

        # Check the default amount for cashback in input field
        assert "0" == conftest.get_element_text_with_retry(driver, bel.input_text)

        # Check the default currency for cashback in input field
        assert f"{chosen_currency}" == conftest.get_element_text_with_retry(driver, bel.currency)

        # Enter cashback amount on numeric keyboard
        helpers.enter_value_on_numeric_keyboard(driver, cashback_amount)

        # Sum base sale amount + cashback
        total = helpers.sum_tip_and_base(amount, cashback_amount)

        # Convert amount for a string with an unbreakable gaps
        formatted_amount = helpers.format_number(total)
    else:
        formatted_amount = helpers.format_number(amount)

    if expect_approve == "yes":
        # Check if the card reading screen contains entered amount
        assert f"{formatted_amount}\xa0{chosen_currency}" in conftest.get_element_text_with_retry(
            driver, transactions.amount_text_view)
        # Check if the card reading screen contains transaction name in title
        assert f"{title}" in conftest.get_element_text_with_retry(driver, bel.title)

        # Check if the card reading screen contains text for card reading
        assert "Přiložte, vložte nebo protáhněte kartu" in conftest.get_element_text_with_retry(
            driver, transactions.card_text_view)

        # Entering card details
        transactions.enter_manual_PAN(driver, PAN=card["PAN"], expiry_date=card["expiration"], CVV=card["cvc"])


def no_original_currency_cashback(driver, amount, transaction_currency="CZK"):

    # Transaction data
    currency = test_data.get("currency")

    chosen_currency = currency.get(transaction_currency)

    # Select currency
    helpers.select_currency(driver, transaction_currency)

    # Enter amount on numeric keyboard
    helpers.enter_value_on_numeric_keyboard(driver, amount)

    formatted_amount = helpers.format_number(amount)

    # Check if the card reading screen contains entered amount
    assert f"{formatted_amount}\xa0{chosen_currency}" in conftest.get_element_text_with_retry(
        driver, transactions.amount_text_view)
    # Check if the card reading screen contains transaction name in title
    assert "Prodej" in conftest.get_element_text_with_retry(driver, bel.title)

    # Check if the card reading screen contains text for card reading
    assert "Přiložte, vložte nebo protáhněte kartu" in conftest.get_element_text_with_retry(
        driver, transactions.card_text_view)


def initiate_manual_sale_tip(driver, amount, transaction_currency, card, tip_amount, tip_option="yes"):
    # Transaction data
    currency = test_data.get("currency")

    if tip_option == "yes":
        button = bel.yes_button
    else:
        button = bel.no_button

    chosen_currency = currency.get(transaction_currency)

    # Select currency
    helpers.select_currency(driver, transaction_currency)

    # Enter amount on numeric keyboard
    helpers.enter_value_on_numeric_keyboard(driver, amount)

    # Check if tip offer is displayed
    assert "Přejete si spropitné?" in conftest.get_element_text_with_retry(driver, bel.text_view)

    # Check if NO button contains correct text
    assert "NE" in conftest.get_element_text_with_retry(driver, bel.no_button)

    # Check if YES button contains correct text
    assert "ANO" in conftest.get_element_text_with_retry(driver, bel.yes_button)

    # Click the button for tip
    conftest.click_element_with_retry(driver, button)

    if tip_option == "yes":
        # Check if a tip text is displayed
        assert "Zadejte spropitné" in conftest.get_element_text_with_retry(driver, bel.text_view)

        # Check the default amount for tip in input field
        assert "0" == conftest.get_element_text_with_retry(driver, bel.input_text)

        # Check the default currency for tip in input field
        assert f"{chosen_currency}" == conftest.get_element_text_with_retry(driver, bel.currency)

        # Enter tip amount on numeric keyboard
        helpers.enter_value_on_numeric_keyboard(driver, tip_amount)

        # Sum base sale amount + tip
        total = helpers.sum_tip_and_base(amount, tip_amount)

        # Convert amount for a string with an unbreakable gaps
        formatted_amount = helpers.format_number(total)
    else:
        formatted_amount = helpers.format_number(amount)

    # Check if the card reading screen contains entered amount
    assert f"{formatted_amount}\xa0{chosen_currency}" in conftest.get_element_text_with_retry(
        driver, transactions.amount_text_view)
    # Check if the card reading screen contains transaction name in title
    assert "Prodej" in conftest.get_element_text_with_retry(driver, bel.title)

    # Check if the card reading screen contains text for card reading
    assert "Přiložte, vložte nebo protáhněte kartu" in conftest.get_element_text_with_retry(
        driver, transactions.card_text_view)

    # Entering card details
    transactions.enter_manual_PAN(driver, PAN=card["PAN"], expiry_date=card["expiration"], CVV=card["cvc"])


def check_cashback_rejected(driver, cashback_amount):
    """Helper function to handle cashback rejection validation."""
    announcement = (
        f"Cashback překročil limit nastavený na terminálu\n\nZadána častka: {cashback_amount}.00\nMaximum: "
        "3000.00\nMinimum: 10.00\n"
    )
    transactions.automatically_declined(
        driver=driver,
        title="Prodej",
        announcement=announcement,
        button=bel.yes_button,
        button_text="POTVRDIT"
    )
