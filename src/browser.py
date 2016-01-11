import logging

from selenium.webdriver import PhantomJS, Firefox
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


MAX_WAITING_TIME = 30


class Browser:
    def __init__(self, silent):
        self.driver = PhantomJS() if silent else Firefox()
        self.driver.set_window_size(1920, 1080)

    def load_page(self, url):
        self.driver.get(url)

    def close(self):
        self.driver.close()

    def wait_for_element(self, attribute_name, attribute_value, root_element=None,
                         terminal=True, multiple=False, visibility=False):
        if root_element is None:
            root_element = self.driver

        try:
            if visibility:
                ec_wait = ec.visibility_of_element_located
            else:
                ec_wait = ec.presence_of_all_elements_located if multiple else ec.presence_of_element_located

            return WebDriverWait(root_element, MAX_WAITING_TIME).until(
                ec_wait((attribute_name, attribute_value))
            )
        except TimeoutException:
            if terminal:
                logging.error('Object not found; %s %s' % (attribute_name, attribute_value))

                raise Exception

            return None

    def enter_text_to_field(self, attribute_name, attribute_value, text, root_element=None):
        field = self.wait_for_element(attribute_name, attribute_value, root_element=root_element)

        field.send_keys(text)

    def find_element_by_attribute(self, tag_name, attribute_name, attribute_value, root_element=None):
        return self.wait_for_element(
            By.CSS_SELECTOR,
            "%s[%s=\"%s\"]" % (tag_name, attribute_name, attribute_value),
            root_element=root_element
        )

    def find_element_by_id(self, element_id, root_element=None, terminal=True):
        return self.wait_for_element(By.ID, element_id, root_element=root_element, terminal=terminal)

    def find_element_by_class(self, class_name, root_element=None, terminal=True):
        return self.wait_for_element(By.CLASS_NAME, class_name, root_element=root_element, terminal=terminal)

    def find_element_by_css_selector(self, element_css, root_element=None, multiple=False):
        return self.wait_for_element(By.CSS_SELECTOR, element_css, root_element=root_element, multiple=multiple)

    def click_button(self, button_id, root_element=None):
        self.find_element_by_id(button_id, root_element=root_element).click()

    def get_time_slot_time_of_day(self, time_slot):
        wrapper_left = self.find_element_by_css_selector(
            'div[class="wrapper-left"]', root_element=time_slot
        )

        time_field = self.find_element_by_css_selector(
            'div[class^="favorite favorite-"]', root_element=wrapper_left
        )

        return time_field.get_attribute('data-favorite-tod')

    def get_time_slot_courts(self, time_slot):
        wrapper_right = self.find_element_by_css_selector(
            'div[class="wrapper-right"]', root_element=time_slot
        )

        court_elements = self.find_element_by_css_selector(
            'div[class^="action single-session"]', root_element=wrapper_right, multiple=True
        )

        courts = []

        for court in court_elements:
            booked_self = court.get_attribute('data-action-type') == 'status'
            available = court.get_attribute('data-can-be-booked') == '1' or booked_self

            data_session_id = court.get_attribute('data-session-id')

            courts.append((available, booked_self, data_session_id))

        return courts
