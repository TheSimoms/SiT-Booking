import re
import requests
import logging

from collections import defaultdict

from browser import Browser


class Court:
    def __init__(self, booked_self=False, available=False, session_id=None):
        self.booked_self = booked_self
        self.available = available
        self.session_id = session_id


class SitBooker:
    def __init__(self, username, password,
                 login_url='https://www.sit.no/trening/hall',
                 court_url='https://www.sit.no/ibooking-api/callback/get-sessions-court-multiple',
                 booking_url='https://www.sit.no/ibooking-api/callback/book-session'):
        self.username = username
        self.password = password

        self.url = login_url
        self.court_url = court_url
        self.booking_url = booking_url

        self.session = requests.Session()

        self.court_information = self.get_court_information()

    def make_post_request(self, url, parameters=None):
        if parameters is None:
            parameters = {}

        return self.session.post(url, data=parameters)

    # FIXME: Log in using requests
    def login(self):
        browser = Browser()
        cookies = {}

        for cookie in browser.login(self.url, self.username, self.password):
            cookies[cookie['name']] = cookie['value']

        return cookies

    @staticmethod
    def is_session_open(session):
        conditions = [
            re.match('Bane (\d)', session['tittel']) is None,
            session['brukerstatus'] in ['ikke_startet', 'reservert'],
        ]

        return True not in conditions

    def get_court_information(self):
        court_info = defaultdict(lambda: defaultdict(lambda: [Court(), Court(), Court()]))

        for session in self.make_post_request(self.court_url, {'sessions': '3'}).json():
            if not self.is_session_open(session):
                continue

            court = court_info[session['dato_id']][session['starter_kl']][int(session['tittel'][-1]) - 1]

            court.booked_self = session['er_booket'] == 'True'
            court.available = int(session['tilgjengelig']) > 0
            court.session_id = session['timeid']

        return court_info

    @staticmethod
    def find_court_layout(date_times, outer_iterator, inner_iterator, reversed_iterator_order):
        session_ids = None
        date_time_session_ids = [None] * len(date_times)

        for o in outer_iterator:
            if reversed_iterator_order:
                date_time_session_ids = [None] * len(date_times)

            for i in inner_iterator:
                if reversed_iterator_order:
                    date_time_index, court_index = i, o
                else:
                    date_time_index, court_index = o, i

                court = date_times[date_time_index][court_index]

                if court.booked_self:
                    date_time_session_ids[date_time_index] = court.session_id

                    logging.debug(
                        'You have already booked court %d at %s' % (court_index + 1, date_times[date_time_index])
                    )
                elif court.available:
                    date_time_session_ids[date_time_index] = court.session_id

                    logging.debug('Court %d is free at %s' % (court_index + 1, date_times[date_time_index]))
                else:
                    if reversed_iterator_order:
                        break

            if None not in date_time_session_ids:
                session_ids = date_time_session_ids

        return session_ids

    def find_best_court_layout(self, date, hours):
        date_time_courts = [self.court_information[date][hour] for hour in hours]

        session_ids = self.find_court_layout(date_time_courts, range(3), range(len(date_time_courts)), True)

        if session_ids is None:
            session_ids = self.find_court_layout(date_time_courts, range(len(date_time_courts)), range(3), False)

        return session_ids

    def book_session(self, session_id):
        r = self.make_post_request(self.booking_url, {
            'sessionID': str(session_id),
            'sendSMS': '0',
            'isGroup': 'true'
        }).json()

        try:
            return r['status'] == 'bestilt'
        except TypeError:
            return False

    def make_booking(self, date_and_hours):
        try:
            date, hours = date_and_hours

            logging.info('Starting booking courts at %s; %s' % (date, hours))

            available = True

            if date not in self.court_information:
                available = False
            else:
                for hour in hours:
                    if hour not in self.court_information[date]:
                        available = False

                        break

            if not available:
                logging.warning('Cannot book courts at %s; %s' % (date, hours))

                return None

            session_ids = self.find_best_court_layout(date, hours)

            if session_ids is not None:
                for session_id in session_ids:
                    self.book_session(session_id)
            else:
                logging.warning('No available courts found at %s; %s' % (date, hours))
        finally:
            logging.info('Booking complete')

    def make_bookings(self, dates_and_hours):
        try:
            self.session.cookies.update(self.login())

            for date_and_hours in dates_and_hours:
                self.make_booking(date_and_hours)
        finally:
            logging.info('Bookings complete')
