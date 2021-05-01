# Disclaimer

This project has not been tested nor updated in several years. There is no guarantee that it still works.

# Sit Booking

A Python script that books squash hours at SiT.no automatically.

Tested with Python 2.7 and 3.4.

## Packages required
* PhantomJS

## Python packages required
* Selenium
* Requests

## Config file

The default location for the config file is ```/etc/default/sit-booking```.

The config file needs to contain three values; SiT username, SiT password, and the path to the booking time file (containing what weekdays and hours to book). Each variable should be on its own line in the config file.

## Booking time file

The booking time file keeps track of what hours to book for the different weekdays. Each line of the file specifies a booking.

Each booking has to match the following format:

```
[WEEKDAY] [START TIME]-[END TIME]
```

where the weekday is one of the following:

```
Mon, Tue, Wed, Thu, Fri, Sat, Sun
```

and the hours match the following format:

```
[HOUR]:[00|30]
```

### Booking time file example

```
Mon 13:30-15:00
Tue 16:00-17:00
Thu 19:00-20:00
Wed 19:00-12:30
```

## Running the script

The script can be run manually with the command ```python src/main.py```. For automation, setting up a Cron job is recommended.

SiT opens the booking for any given day at 21:00 two days before.

### Example of working Cron job

```
00,01,02,05,10 21 * * * [PATH TO SIT BOOKING]/src/main.py
```

This job makes sure the bookings take place as early as possible. It also includes a fail-safe mechanism for when the booking is not opened at the moment it is supposed to.
