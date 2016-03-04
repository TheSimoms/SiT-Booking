import logging

from selenium.webdriver import PhantomJS, Firefox
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities


MAX_WAITING_TIME = 10


class Browser:
    def __init__(self, silent):
        if silent:
            user_agent = (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) " +
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.57 Safari/537.36"
            )

            d_cap = dict(DesiredCapabilities.PHANTOMJS)
            d_cap["phantomjs.page.settings.userAgent"] = user_agent

            self.driver = PhantomJS(desired_capabilities=d_cap)
        else:
            self.driver = Firefox()

        self.driver.set_window_size(1920, 1080)

    def load_page(self, url):
        self.driver.get(url)

    def close(self):
        self.driver.close()

    def find_element(self, attribute_name, attribute_value, root_element=None, multiple=False, visibility=False):
        if root_element is None:
            root_element = self.driver

        try:
            if visibility:
                ec_wait = ec.visibility_of_element_located
            else:
                if multiple:
                    ec_wait = ec.presence_of_all_elements_located
                else:
                    ec_wait = ec.presence_of_element_located

            return WebDriverWait(root_element, MAX_WAITING_TIME).until(
                ec_wait((attribute_name, attribute_value))
            )
        except TimeoutException:
            logging.error('Object not found; %s %s' % (attribute_name, attribute_value))

    def wait_for_element_to_be_visible(self, tag_name, attribute_name, attribute_value, root_element=None):
        return self.find_element(
            By.CSS_SELECTOR, "%s[%s=\"%s\"]" % (tag_name, attribute_name, attribute_value), visibility=True,
            root_element=root_element
        )

    def find_element_by_attribute(self, tag_name, attribute_name, attribute_value, root_element=None):
        return self.find_element(
            By.CSS_SELECTOR,
            "%s[%s=\"%s\"]" % (tag_name, attribute_name, attribute_value), root_element=root_element
        )

    def find_element_by_id(self, element_id, root_element=None):
        return self.find_element(By.ID, element_id, root_element=root_element)

    def find_element_by_class(self, class_name, root_element=None):
        return self.find_element(By.CLASS_NAME, class_name, root_element=root_element)

    def find_element_by_css_selector(self, element_css, root_element=None, multiple=False):
        return self.find_element(By.CSS_SELECTOR, element_css, root_element=root_element, multiple=multiple)

    def click_button_by_id(self, button_id, root_element=None):
        button = self.find_element_by_id(button_id, root_element=root_element)

        if button is not None:
            button.click()

    def click_button(self, tag_name, attribute_name, attribute_value):
        button = self.wait_for_element_to_be_visible(tag_name, attribute_name, attribute_value)

        if button is not None:
            button.click()

    def enter_text_to_field(self, attribute_name, attribute_value, text, root_element=None):
        field = self.find_element(attribute_name, attribute_value, root_element=root_element)

        if field is not None:
            field.send_keys(text)

    def get_time_slot_time_of_day(self, time_slot):
        time_field = self.find_element_by_css_selector(
            'div[class*="favorite favorite-"]', root_element=time_slot
        )

        return time_field.get_attribute('data-favorite-tod')

    def get_time_slot_courts(self, time_slot):
        court_elements = self.find_element_by_css_selector(
            'div[class*="action single-session"]', root_element=time_slot, multiple=True
        )

        courts = []

        for court in court_elements:
            booked_self = court.get_attribute('class').find('session-is-booked') >= 0
            available = court.get_attribute('class').find('session-is-active') >= 0 or booked_self

            data_session_id = court.get_attribute('data-session-id')

            courts.append((available, booked_self, data_session_id))

        return courts
