import icalendar
import pytz
import datetime
import logging
import ConfigParser

logger = logging.getLogger(__name__)

WEEKDAY = [1, 2, 3, 4, 5]
WEEKEND = [6, 7]


class Event(object):
    def __init__(self, section, config):
        self.config = config
        self.section = section

    def format(self):
        if any([self.until, self.begin]):
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
        else:
            event = icalendar.Event()
            event.add('summary', self.section)
            event.add('dtstart', self.start)
            event.add('dtend', self.end)
            yield event

    def __getattr__(self, attr):
        if attr in ('weekly', 'weekend', 'weekday'):
            func = self.config.getboolean
        else:
            func = self.config.get

        if attr in ('timezone', 'weekly', 'weekday', 'weekend', 'until', 'begin'):
            try:
                return func(self.section, attr)
            except ConfigParser.NoOptionError:
                try:
                    return func('DEFAULT', attr)
                except ConfigParser.NoOptionError:
                    return None

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

    def __date(self, key):
        date = self.__getattr__(key)
        year, month, day = map(int, date.split('-'))
        return datetime.date(year, month, day)

    @property
    def timezone(self):
        return pytz.timezone(self.__getattr__('timezone'))

    @property
    def start(self):
        return self.__time('start', 0)

    @property
    def end(self):
        return self.__time('end', 1)

    @property
    def repeat(self):
        try:
            return self.config.getboolean(self.section, 'repeat')
        except:
            return False

    @property
    def until(self):
        return self.__date('until')

    @property
    def begin(self):
        return self.__date('begin')

    def duration(self):
        duration = self.config.get(self.section, 'duration')
        start, end = duration.split(' - ')
        return start.strip(), end.strip()


class Calendar(object):
    def __init__(self, path):
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(path)

    def format(self):
        cal = icalendar.Calendar()
        for section in self.config.sections():
            event = Event(section, self.config)
            for e in event.format():
                cal.add_component(e)
        return cal.to_ical()
