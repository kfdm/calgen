import icalendar
import csv
import pytz
import datetime
import logging
import ConfigParser

logger = logging.getLogger(__name__)

WEEKDAY = [1, 2, 3, 4, 5]
WEEKEND = [6, 7]


class GlobalProperty(object):
    func = 'get'

    def __init__(self, key, default=None):
        self.key = key
        self.default = default

    def __get__(self, instance, owner):
        func = getattr(instance.config, self.func)
        try:
            return func(instance.section, self.key)
        except ConfigParser.NoOptionError:
            try:
                return func('DEFAULT', self.key)
            except ConfigParser.NoOptionError:
                return self.default


class BooleanProperty(GlobalProperty):
    func = 'getboolean'


class DateProperty(object):
    def __init__(self, key, default=None):
        self.key = key
        self.default = default

    def __get__(self, instance, owner):
        try:
            date = instance.config.get(instance.section, self.key)
            year, month, day = map(int, date.split('-'))
            return datetime.date(year, month, day)
        except ConfigParser.NoOptionError:
            return self.default


class RangeProperty(object):
    def __init__(self, key, index):
        self.key = key
        self.index = index

    def __get__(self, instance, owner):
        try:
            ts = instance.config.get(instance.section, self.key)
        except ConfigParser.NoOptionError:
            ts = instance.duration()[self.index]

        try:
            return datetime.datetime.strptime(ts, "%a %b %d %H:%M:%S %Y")
        except ValueError:
            if instance.begin:
                date = instance.begin
                date = datetime.datetime(date.year, date.month, date.day)
            elif instance.day:
                date = instance.day
                date = datetime.datetime(date.year, date.month, date.day)
            else:
                date = datetime.datetime.now(instance.timezone)
            hour, minute = map(int, ts.split(':'))
            return date.replace(hour=hour, minute=minute, second=0, microsecond=0)


class Event(object):
    timezones = GlobalProperty('timezone')
    timezone = GlobalProperty('timezone')
    weekday = BooleanProperty('weekday')
    weekend = BooleanProperty('weekend')
    weekly = BooleanProperty('weekly')
    until = DateProperty('until')
    begin = DateProperty('begin')
    day = DateProperty('date')
    start = RangeProperty('start', 0)
    end = RangeProperty('end', 1)

    def __init__(self, section, config):
        self.config = config
        self.section = section

    def format(self):
        if any([self.until, self.begin]):
            return self.format_repeat()
        else:
            return self.format_single()

    def format_single(self):
        event = icalendar.Event()
        event.add('summary', self.section)
        event.add('dtstart', self.start)
        event.add('dtend', self.end)
        yield event

    def format_repeat(self):
        for offset in range(0, (self.until - self.begin).days + 1):
            offset = datetime.timedelta(offset)
            start = self.start + offset

            if not self.weekly:
                if self.weekday and start.isoweekday() not in WEEKDAY:
                    continue
                if self.weekend and start.isoweekday() not in WEEKEND:
                    continue

            event = icalendar.Event()
            event.add('summary', self.section)
            event.add('dtstart', start)
            event.add('dtend', self.end + offset)
            yield event

    def __time(self, key, index):
        try:
            ts = self.config.get(self.section, key)
        except ConfigParser.NoOptionError:
            ts = self.duration()[index]
        try:
            return datetime.datetime.strptime(ts, "%a %b %d %H:%M:%S %Y")
        except ValueError:
            if self.begin:
                date = self.begin
                date = datetime.datetime(date.year, date.month, date.day)
            else:
                date = datetime.datetime.now(self.timezone)
            hour, minute = map(int, ts.split(':'))
            return date.replace(hour=hour, minute=minute, second=0, microsecond=0)

    @property
    def timezone(self):
        return pytz.timezone(self.timezones)

    @property
    def repeat(self):
        try:
            return self.config.getboolean(self.section, 'repeat')
        except:
            return False

    def duration(self):
        duration = self.config.get(self.section, 'duration')
        start, end = duration.split(' - ')
        return start.strip(), end.strip()


class CSVEvent(object):
    def __init__(self, row):
        self.row = row

    @property
    def summary(self):
        return self.row['Summary']

    @property
    def start(self):
        year, month, day = map(int, self.row['Date'].split('-'))
        start, end = self.row['Time'].split('-')
        hour, minute = map(int, start.split(':'))
        return datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)

    @property
    def end(self):
        year, month, day = map(int, self.row['Date'].split('-'))
        start, end = self.row['Time'].split('-')
        hour, minute = map(int, end.split(':'))
        return datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute)

    def format(self):
        event = icalendar.Event()
        event.add('summary', self.summary)
        event.add('dtstart', self.start)
        event.add('dtend', self.end)
        return event


class CommentStripper(object):
    def __init__(self, fp):
        self.fp = fp

    def __iter__(self):
        for line in self.fp:
            if line.startswith(';'):
                continue
            if line.startswith('#'):
                continue
            if line.strip() == '':
                continue
            yield line


class Calendar(object):
    def __init__(self, paths):
        self.cal = icalendar.Calendar()
        for path in paths:
            logger.info('Parsing: %s', path)
            if path.endswith('.ini'):
                self.parse_ini(path)
            elif path.endswith('.csv'):
                self.parse_csv(path)

    def parse_ini(self, path):
        config = ConfigParser.SafeConfigParser()
        config.read(path)
        for section in config.sections():
            event = Event(section, config)
            for e in event.format():
                self.cal.add_component(e)

    def parse_csv(self, path):
        with open(path, 'rb') as csvfile:
            csvreader = csv.DictReader(CommentStripper(csvfile))
            for row in csvreader:
                self.cal.add_component(CSVEvent(row).format())

    def format(self):
        return self.cal.to_ical()
