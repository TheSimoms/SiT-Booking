import logging

from selenium.webdriver import PhantomJS
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


MAX_WAITING_TIME = 10


class Browser:
    def __init__(self):
        logging.info('Starting browser')

        user_agent = (
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 ' +
            '(KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'
        )

        d_cap = dict(DesiredCapabilities.PHANTOMJS)
        d_cap["phantomjs.page.settings.userAgent"] = user_agent

        self.driver = PhantomJS(
            desired_capabilities=d_cap,
            service_args=['--ssl-protocol=any']
        )

        self.driver.set_window_size(1360, 768)

        logging.info('Browser started')

    def load_page(self, url):
        logging.info('Loading page: %s' % url)

        self.driver.get(url)

        logging.info('Page loaded')

    def close(self):
        self.driver.close()

    def find_element(self, attribute_name, attribute_value):
        try:
            return WebDriverWait(self.driver, MAX_WAITING_TIME).until(
                ec.presence_of_element_located((attribute_name, attribute_value))
            )
        except TimeoutException:
            logging.error('Object not found; %s %s' % (attribute_name, attribute_value))

    def find_element_by_id(self, element_id):
        return self.find_element(By.ID, element_id)

    def click_button_by_id(self, button_id):
        button = self.find_element_by_id(button_id)

        if button is not None:
            button.click()

    def enter_text_to_field(self, attribute_name, attribute_value, text):
        field = self.find_element(attribute_name, attribute_value)

        if field is not None:
            field.send_keys(text)

    def enter_login_information(self, field_id, text):
        self.enter_text_to_field(By.ID, field_id, text)

    def login(self, url, username, password):
        self.load_page(url)

        if self.find_element_by_id('loginbutton') is not None:
            logging.info('Logging in')

            self.click_button_by_id('loginbutton')

            self.enter_login_information('edit-name', username)
            self.enter_login_information('edit-pass', password)

            self.click_button_by_id('edit-submit--3')

            logging.info('Logged in')

        cookies = self.driver.get_cookies()

        self.close()

        return cookies
