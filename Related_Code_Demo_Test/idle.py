import conftest
from conftest import test_data
import utils.basic_elements as bel


def idle_screen_displayed(driver, default_currency="CZK", trans_title="Prodej"):
    currency = test_data.get("currency")
    chosen_currency = currency.get(default_currency)

    assert chosen_currency in conftest.get_element_text_with_retry(driver, bel.currency)
    assert "0" == conftest.get_element_text_with_retry(driver, bel.input_text)
    assert trans_title in conftest.get_element_text_with_retry(driver, bel.title)