import icalendar
import pytz
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
        #event.add('dtstart', self.start)
        #event.add('dtstop', self.stop)
        return event

    @property
    def timezone(self):
        try:
            return pytz.timezone(self.config.get(self.section, 'timezone'))
        except ConfigParser.NoOptionError:
            return pytz.timezone(self.config.get('DEFAULT', 'timezone'))

    @property
    def start(self):
        try:
            start = self.config.get(self.section, 'start')
        except ConfigParser.NoOptionError:
            start, _ = self.duration()
        return time.strptime(start)

    @property
    def end(self):
        try:
            end = self.config.get(self.section, 'end')
        except ConfigParser.NoOptionError:
            _, end = self.duration()
        return time.strptime(end)

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
