import icalendar
import pytz
import datetime
import logging
import time
import ConfigParser

logger = logging.getLogger(__name__)


class Event(object):
    def __init__(self, section, config):
        self.config = config
        self.section = section

    def format(self):
        event = icalendar.Event()
        event.add('summary', self.section)
        event.add('dtstart', self.start)
        event.add('dtend', self.end)
        return event

    def __getattr__(self, attr):
        if attr in ('timezone', 'weekly', 'weekday', 'weekend'):
            logging.debug('Getting %s', attr)
            try:
                return self.config.get(self.section, attr)
            except ConfigParser.NoOptionError:
                return self.config.get('DEFAULT', attr)

    def __time(self, key, index):
        try:
            ts = self.config.get(self.section, key)
        except ConfigParser.NoOptionError:
            ts = self.duration()[index]
        try:
            return datetime.datetime.strptime(ts, "%a %b %d %H:%M:%S %Y")
        except ValueError:
            date = datetime.datetime.now(self.timezone)
            hour, minute = ts.split(':')
            return date.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)

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

    def duration(self):
        duration = self.config.get(self.section, 'duration')
        start, end = duration.split(' - ')
        logger.debug('Parsing duration [%s] [%s]', start, end)
        return start.strip(), end.strip()


class Calendar(object):
    def __init__(self, path):
        self.config = ConfigParser.SafeConfigParser()
        self.config.read(path)

    def format(self):
        cal = icalendar.Calendar()
        for section in self.config.sections():
            event = Event(section, self.config)
            cal.add_component(event.format())
        return cal.to_ical()
