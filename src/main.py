#!/usr/bin/python

import sys
import logging
import datetime


from booker import SitBooker


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


def weekday_to_date(weekday):
    today = datetime.date.today()
    difference = WEEKDAY_INDICES[weekday] - today.weekday()

    if difference < 0:
        difference += 7

    target_date = today + datetime.timedelta(difference)

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
    try:
        logging_level = logging.DEBUG if debug else logging.INFO

        logging.basicConfig(level=logging_level)

        try:
            with open(CONFIG_FILE_PATH, 'r') as config_file:
                username = config_file.readline().strip()
                password = config_file.readline().strip()
                booking_times_file_path = config_file.readline().strip()
        except IOError:
            logging.error('Could not read config file')

            sys.exit()

        try:
            with open(booking_times_file_path) as booking_times_file:
                booker = SitBooker(username, password)

                booking_times = [line.strip().split(' ') for line in booking_times_file.readlines()]
                dates_and_hours = []

                for booking_time in booking_times:
                    date = weekday_to_date(booking_time[0])
                    hours = time_interval_to_half_hours(booking_time[1])

                    dates_and_hours.append([date, hours])

                booker.make_bookings(dates_and_hours)
        except IOError:
            logging.error('Could not open booking times file' % booking_times_file_path)

            sys.exit()

    finally:
        logging.info('Done')


if __name__ == '__main__':
    main()
