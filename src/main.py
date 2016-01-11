#!/usr/bin/python

import sys
import logging
import datetime

from selenium.webdriver.common.by import By

from browser import Browser


CONFIG_FILE_PATH = '/etc/default/sit-booking'
WEEKDAY_INDICES = {
    'Mon': 0,
    'Tue': 1,
    'Wed': 2,
    'Thu': 3,
    'Fri': 4,
    'Sat': 5,
    'Sun': 6,
}


class SitBooker:
    def __init__(self, email, password, url='https://www.sit.no/trening/hall', silent=True):
        self.browser = Browser(silent)

        self.email = email
        self.password = password
        self.url = url

    def enter_login_information(self, field_id, text):
        self.browser.enter_text_to_field(By.ID, field_id, text)

    def login(self):
        self.browser.load_page(self.url)

        if self.browser.find_element_by_id('loginbutton', terminal=False) is not None:
            logging.info('Logging in')

            self.browser.click_button('loginbutton', )

            self.enter_login_information('edit-name', self.email)
            self.enter_login_information('edit-pass', self.password)

            self.browser.click_button('edit-submit--3')

            logging.info('Logged in')

    def get_time_slots(self):
        days_outer_container = self.browser.find_element_by_attribute('div', 'class', 'ibooking-all-days')

        days_containers = [element for element in self.browser.find_element_by_css_selector(
            'div[class*="ibooking-complete-day ibooking-complete-day-court ibooking-complete-day-"]',
            root_element=days_outer_container,
            multiple=True
        ) if element.get_attribute('class').find('fade-entire-day') < 0]

        time_slots = dict()

        for day in days_containers:
            current_date = day.get_attribute('data-datetag')

            time_slots[current_date] = dict()

            for hour in self.browser.find_element_by_css_selector(
                'div[class*="ibooking-single-session ibooking-single-session-court-hover-box '
                'ibooking-single-session-court-hover-box-squash"]',
                root_element=day,
                multiple=True
            ):
                time_of_day = self.browser.get_time_slot_time_of_day(hour)
                courts = [Court(*court) for court in self.browser.get_time_slot_courts(hour)]

                time_slots[current_date][time_of_day] = TimeSlot(current_date, time_of_day, courts)

        return time_slots

    def wait_for_element_to_be_visible(self, tag_name, attribute_name, attribute_value, root_element=None):
        self.browser.find_element_by_attribute(tag_name, attribute_name, attribute_value, root_element=root_element)

        return self.browser.wait_for_element(
            By.CSS_SELECTOR, "%s[%s=\"%s\"]" % (tag_name, attribute_name, attribute_value), visibility=True
        )

    def open_booking_dialog(self, session_id):
        self.wait_for_element_to_be_visible('div', 'data-session-id', session_id).click()

    def close_booking_dialog(self):
        self.wait_for_element_to_be_visible('div', 'class', 'ibooking-dialog')

        self.wait_for_element_to_be_visible(
            'div',
            'class',
            'close-button'
        ).click()

    def book_session(self, session_id):
        if session_id is None:
            return

        self.open_booking_dialog(session_id)
        self.close_booking_dialog()

    @staticmethod
    def find_best_court_layout_same_court(date_times):
        session_ids = None

        for court_index in range(3):
            court_session_ids = [None] * len(date_times)

            available = True

            for date_time_index in range(len(date_times)):
                court = date_times[date_time_index][court_index]

                if court.available:
                    court_session_ids[date_time_index] = court.data_session_id

                    logging.debug('Court %d is free at %s' % (court_index+1, date_times[date_time_index]))
                elif court.booked_self:
                    logging.debug(
                        'You have already booked court %d at %s' % (court_index+1, date_times[date_time_index]))
                else:
                    available = False

                    break

            if available:
                session_ids = court_session_ids

        return session_ids

    @staticmethod
    def find_best_court_layout_different_courts(date_times):
        session_ids = None

        for date_time_index in range(len(date_times)):
            date_time_session_ids = [None] * len(date_times)

            available = True

            for court_index in range(3):
                court = date_times[date_time_index][court_index]

                if court.available:
                    date_time_session_ids[date_time_index] = court.data_session_id

                    logging.debug('Court %d is free at %s' % (court_index+1, date_times[date_time_index]))
                elif court.booked_self:
                    logging.debug(
                        'You have already booked court %d at %s' % (court_index+1, date_times[date_time_index]))
                else:
                    available = False

                    break

            if available:
                session_ids = date_time_session_ids

        return session_ids

    def find_best_court_layout(self, time_slots, date, hours):
        date_time_courts = [time_slots[date][hour].courts for hour in hours]
        session_ids = self.find_best_court_layout_same_court(date_time_courts)

        if session_ids is None:
            session_ids = self.find_best_court_layout_different_courts(date_time_courts)

        if session_ids is None:
            logging.warning('Couldn\'t find available courts at %s; %s' % (date, hours))

        return session_ids

    def make_booking(self, time_slots, date_and_hours):
        try:
            date, hours = date_and_hours

            logging.info('Starting booking courts at %s; %s' % (date, hours))

            if date not in time_slots:
                logging.warning('No available courts found at %s; %s' % (date, hours))

                return None

            session_ids = self.find_best_court_layout(time_slots, date, hours)

            if session_ids is not None:
                for session_id in session_ids:
                    self.book_session(session_id)
            else:
                logging.warning('No available courts found at %s; %s' % (date, hours))
        finally:
            logging.info('Booking complete')

    def make_bookings(self, dates_and_hours):
        try:
            self.login()

            time_slots = self.get_time_slots()

            for date_and_hours in dates_and_hours:
                self.make_booking(time_slots, date_and_hours)
        finally:
            logging.info('Bookings complete')


class TimeSlot:
    def __init__(self, date, time_of_day, courts):
        self.date = date
        self.time_of_day = time_of_day
        self.courts = courts


class Court:
    def __init__(self, available, booked_self, data_session_id):
        self.available = available
        self.booked_self = booked_self
        self.data_session_id = data_session_id


def weekday_to_date(weekday):
    today = datetime.date.today()
    target_date = today + datetime.timedelta(abs(today.weekday() - WEEKDAY_INDICES[weekday]))

    return str(target_date).replace('-', '')


def time_interval_to_half_hours(time_interval):
    start_time, end_time = time_interval.split('-')

    hours = []

    current_time = start_time

    while current_time != end_time:
        hours.append(current_time)

        hour, minute = map(int, current_time.split(':'))

        minute = (minute + 30) % 60

        if minute == 0:
            hour = (hour + 1) % 24

        current_time = '%s%d:%s%d' % ('' if hour > 9 else '0', hour, '' if minute > 9 else '0', minute)

    return hours


def main(debug=False):
    booker = None

    try:
        logging_level = logging.DEBUG if debug else logging.INFO

        logging.basicConfig(level=logging_level)

        try:
            with open(CONFIG_FILE_PATH, 'r') as config_file:
                email = config_file.readline().strip()
                password = config_file.readline().strip()
                booking_times_file_path = config_file.readline().strip()
        except IOError:
            logging.error('Could not read config file')

            sys.exit()

        booker = SitBooker(email, password)

        try:
            with open(booking_times_file_path) as booking_times_file:
                booking_times = [line.strip().split(' ') for line in booking_times_file.readlines()]
                dates_and_hours = []

                for booking_time in booking_times:
                    date = weekday_to_date(booking_time[0])
                    hours = time_interval_to_half_hours(booking_time[1])

                    dates_and_hours.append([date, hours])
        except IOError:
            logging.error('Couldn\'t open booking times file' % booking_times_file_path)

            sys.exit()

        booker.make_bookings(dates_and_hours)

    finally:
        if booker is not None:
            booker.browser.close()

        logging.info('Done')


if __name__ == '__main__':
    main()