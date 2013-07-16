# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2013 Met Office.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------------
import re


DAYS_OF_MONTHS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
DAYS_OF_MONTHS_LEAP = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

WEEK_DAY_START_REFERENCE = {"calendar": (2000, 1, 3),
                            "ordinal": (2000, 3)}



class TimeRecurrenceParser(object):

    """Parser for ISO 8601 recurrence expressions."""

    RECURRENCE_REGEXES = [
         re.compile(r"^R(?P<reps>\d+)/(?P<start>[^P][^/]*)/(?P<end>[^P].*)$"),
         re.compile(r"^R(?P<reps>\d+)?/(?P<start>[^P][^/]*)/(?P<interval>P.+)$"),
         re.compile(r"^R(?P<reps>\d+)?/(?P<interval>P.+)/(?P<end>[^P].*)$")]

    def __init__(self, timepoint_parser=None, timeinterval_parser=None):
        if timepoint_parser is None:
            self.timepoint_parser = TimePointParser()
        else:
            self.timepoint_parser = timepoint_parser
        if timeinterval_parser is None:
            self.timeinterval_parser = TimeIntervalParser()
        else:
            self.timepoint_parser = timeinterval_parser

    def parse(self, expression):
        for regex in self.RECURRENCE_REGEXES:
            result = regex.search(expression)
            if not result:
                continue
            result_map = result.groupdict()
            repetitions = None
            start_point = None
            end_point = None
            duration = None
            if "reps" in result_map and result_map["reps"] is not None:
                repetitions = int(result_map["reps"])
            if "start" in result_map:
                start_point = self.timepoint_parser.parse(result_map["start"])
            if "end" in result_map:
                end_point = self.timepoint_parser.parse(result_map["end"])
            if "interval" in result_map:
                interval = self.timeinterval_parser.parse(
                                             result_map["interval"])
            return TimeRecurrence(repetitions=repetitions,
                                  start_point=start_point,
                                  end_point=end_point,
                                  interval=interval)
        return SyntaxError("Not a supported ISO 8601 recurrence pattern: %s" %
                           expression)


class TimePointParser(object):

    """Container for ISO 8601 date/time expressions.

    Keyword arguments:
    num_expanded_year_digits (default 2) specifies the extra year
    digits allowed by the ISO standard - for example, 1995 can be
    written as +001995 with 2 extra year digits.

    allow_truncated (default False) specifies that ISO 8601:2000
    truncations are allowed (not allowed in the ISO 8601:2004
    standard which supersedes it).
    """

    DATE_EXPRESSIONS = {"basic": {"complete": u"""
ccYYMMDD
±ΫccYYMMDD
ccYYDDD
±ΫccYYDDD
ccYYWwwD
±ΫccYYWwwD""",
                                  "reduced": u"""
ccYYMM       # Deviation (can technically be confused with hhmmss).
ccYY
cc
±ΫccYYMM     # Deviation (see above).
±ΫccYY
±Ϋcc
ccYYWww
±ΫccYYWww""",
                                  "truncated": u"""
-YYMM
-YY
--MMDD
--MM
---DD
YYDDD
-DDD
YYWwwD
YYWww
-YWwwD
-YWww
-WwwD
-Www
-W-D
"""},
                        "extended": {"complete": u"""
ccYY-MM-DD
±ΫccYY-MM-DD
ccYY-DDD
±ΫccYY-DDD
ccYY-Www-D
±ΫccYY-Www-D""",
                                     "reduced": u"""
ccYY-MM
±ΫccYY-MM
ccYY-Www
±ΫccYY-Www""",
                                     "truncated": u"""
-YY-MM
--MM-DD
YY-DDD
-DDD          # Deviation from standard ?
YY-Www-D
YY-Www
-Y-WwwD
-Y-Www
-Www-D
"""}}

    TIME_EXPRESSIONS = {"basic": {"complete": u"""
# No Time Zone
hhmmss

# No Time Zone - decimals
hhmmss,sṡ
hhmm,mṁ
hh,hḣ
""",
                                  "reduced": u"""
# No Time Zone
hhmm
hh

# No Time Zone - decimals
""",
                                  "truncated": u"""
# No Time Zone
-mmss
-mm
--ss

# No Time Zone - decimals
-mmss,sṡ
-mm,mṁ
--ss,sṡ
"""},
                        "extended": {"complete": u"""
# No Time Zone
hh:mm:ss

# No Time Zone - decimals
hh:mm:ss,sṡ
hh:mm,mṁ
hh,hḣ          # Deviation? Not allowed in standard ?
""",
                                     "reduced": u"""
# No Time Zone
hh:mm
hh             # Deviation? Not allowed in standard ?
""",
                                  "truncated": u"""
# No Time Zone
-mm:ss
-mm             # Deviation? Not allowed in standard ?
--ss            # Deviation? Not allowed in standard ?

# No Time Zone - decimals
-mm:ss,sṡ
-mm,mṁ          # Deviation? Not allowed in standard ?
--ss,sṡ         # Deviation? Not allowed in standard ?
"""}}

    TIMEZONE_EXPRESSIONS = {"basic": u"""
Z
±hh
±hhmm
""",
                            "extended": u"""
Z
±hh             # Deviation? Not allowed in standard?
±hh:mm
"""}

    DATE_CHAR_REGEXES = [(u"±", "(?P<year_sign>[+-])"),
                         (u"cc", "(?P<century>\d\d)"),
                         (u"YY", "(?P<year_of_century>\d\d)"),
                         (u"MM", "(?P<month_of_year>\d\d)"),
                         (u"DDD", "(?P<day_of_year>\d\d)"),
                         (u"DD", "(?P<day_of_month>\d\d)"),
                         (u"Www", "(?P<week_of_year>W\d\d)"),
                         (u"D", "(?P<day_of_week>\d)")]
    TIME_CHAR_REGEXES = [(u"(?<=^hh)mm", "(?P<minute_of_hour>\d\d)"),
                         (u"(?<=^hh:)mm", "(?P<minute_of_hour>\d\d)"),
                         (u"(?<=^-)mm", "(?P<minute_of_hour>\d\d)"),
                         (u"^hh", "(?P<hour_of_day>\d\d)"),
                         (u",hḣ", "[,.](?P<hour_of_day_decimal>\d+)"),
                         (u",mṁ", "[,.](?P<minute_of_hour_decimal>\d+)"),
                         (u"ss", "(?P<second_of_minute>\d\d)"),
                         (u",sṡ", "(?P<second_of_minute_decimal>\s+)")]
    TIMEZONE_CHAR_REGEXES = [
                         (u"(?<=±hh)mm", "(?P<time_zone_minute>\d\d)"),
                         (u"(?<=±hh:)mm", "(?P<time_zone_minute>\d\d)"),
                         (u"(?<=±)hh", "(?P<time_zone_hour>\d\d)"),
                         (u"±", "(?P<time_zone_sign>[+-])"),
                         (u"Z", "(?P<time_zone_utc>Z)")]
    TIME_DESIGNATOR = "T"

    def __init__(self, num_expanded_year_digits=2,
                 allow_truncated=False,
                 allow_only_basic=False,
                 format_function=None):
        expanded_year_digit_regex = "\d" * num_expanded_year_digits
        self.DATE_CHAR_REGEXES.append((u"Ϋ", "(?P<expanded_year>" +
                                             expanded_year_digit_regex + ")"))
        self.allow_truncated = allow_truncated
        self.allow_only_basic = allow_only_basic
        self.format_function = format_function
        self.generate_regexes()

    def generate_regexes(self):
        """Generate combined date time strings."""
        self.date_time_map = {}
        date_map = self.DATE_EXPRESSIONS
        time_map = self.TIME_EXPRESSIONS
        timezone_map = self.TIMEZONE_EXPRESSIONS
        date_ok_keys = ["complete"]
        if self.allow_truncated:
            date_ok_keys = ["complete", "truncated"]
        time_ok_keys = ["complete", "reduced"]
        self._date_regex_map = {}
        self._time_regex_map = {}
        self._timezone_regex_map = {}
        format_ok_keys = ["basic", "extended"]
        if self.allow_only_basic:
            format_ok_keys = ["basic"]
        for format_type in format_ok_keys:
            self.date_time_map.setdefault(format_type, [])
            self._date_regex_map.setdefault(format_type, [])
            self._time_regex_map.setdefault(format_type, [])
            self._timezone_regex_map.setdefault(format_type, [])
            for date_key in date_ok_keys:
                for date_expr in self.get_expressions(
                                          date_map[format_type][date_key]):
                    date_regex = self.parse_date_expression_to_regex(
                                                            date_expr)
                    self._date_regex_map[format_type].append(re.compile(
                                                                date_regex))
            for time_key in time_ok_keys:
                for time_expr in self.get_expressions(
                                          time_map[format_type][time_key]):
                    time_regex = self.parse_time_expression_to_regex(
                                                            time_expr)
                    self._time_regex_map[format_type].append(re.compile(
                                                                time_regex))
            for timezone_expr in self.get_expressions(
                                          timezone_map[format_type]):
                timezone_regex = self.parse_timezone_expression_to_regex(
                                                                timezone_expr)
                self._timezone_regex_map[format_type].append(
                                                re.compile(timezone_regex))
                                          
    def get_expressions(self, text):
        """Yield valid expressions from text."""
        for line in text.splitlines():
            line_text = line.strip()
            if not line_text or line_text.startswith("#"):
                continue
            expr_text = line_text.split("#", 1)[0].strip()
            yield expr_text

    def parse_date_expression_to_regex(self, expression):
        """Construct regular expressions for the date."""
        for expr_regex, substitute in self.DATE_CHAR_REGEXES:
            expression = re.sub(expr_regex, substitute, expression)
        expression = "^" + expression + "$"
        return expression

    def parse_time_expression_to_regex(self, expression):
        """Construct regular expressions for the time."""
        for expr_regex, substitute in self.TIME_CHAR_REGEXES:
            expression = re.sub(expr_regex, substitute, expression)
        expression = "^" + expression + "$"
        return expression

    def parse_timezone_expression_to_regex(self, expression):
        """Construct regular expressions for the timezone."""
        for expr_regex, substitute in self.TIMEZONE_CHAR_REGEXES:
            expression = re.sub(expr_regex, substitute, expression)
        expression = "^" + expression + "$"
        return expression

    def parse(self, timepoint_string):
        """Parse a user-supplied timepoint string."""
        date_time_timezone = timepoint_string.split(self.TIME_DESIGNATOR)
        if len(date_time_timezone) == 1:
            date = date_and_time[0]
            format_key, date_info = self.get_date_info(date)
            time_info = {}
        else:
            date, time_timezone = date_time_timezone    
            format_key, date_info = self.get_date_info(date)
            if time_timezone.endswith("Z"):
                time, timezone = time_timezone[:-1], "Z"
            else:
                if "+" in time_timezone:
                    time, timezone = time_timezone.split("+")
                    timezone = "+" + timezone
                elif "-" in time_timezone:
                    time, timezone = time_timezone.split("-")
                    timezone = "-" + timezone
                else:
                    time = time_timezone
                    timezone = None
            if timezone is None:
                timezone_info = {}
            else:
                timezone_info = self.get_timezone_info(
                                                  timezone,
                                                  format_ok_keys=[format_key])
                if timezone_info.pop("time_zone_sign", "+") == "-":
                    timezone_info["time_zone_hour"] = (
                             int(timezone_info["time_zone_hour"]) * -1)
            time_info = self.get_time_info(time, format_ok_keys=[format_key])
            time_info.update(timezone_info)
        info = {}
        year = int(date_info.get("year", 0))
        year += int(date_info.pop("year_of_century", 0))
        year += 100 * int(date_info.pop("century", 0))
        year += 10000 * int(date_info.pop("expanded_year", 0))
        if date_info.pop("year_sign", "+") == "-":
            year *= -1
        date_info["year"] = year
        for key, value in date_info.items():
            date_info[key] = int(value)
        info.update(date_info)
        for key, value in time_info.items():
            if key.endswith("_decimal"):
                value = "0." + value
            try:
                value = float(value)
            except (IOError, ValueError) as e:
                pass
            if key == "time_zone_utc" and value == "Z":
                value = True
            if key == "year_sign":
                if value == "+":
                    value = 1
                else:
                    value = -1
            time_info[key] = value
        info.update(time_info)
        if self.format_function is not None:
            info.update({"format_function": self.format_function})
        return TimePoint(**info)

    def get_date_info(self, date_string):
        """Return the format and properties from a date string."""
        for format_ok_key, regex_list in self._date_regex_map.items():
            for regex in regex_list:
                result = regex.match(date_string)
                if result:
                    return format_ok_key, result.groupdict()
        return None, {}

    def get_time_info(self, time_string, format_ok_keys=None):
        """Return the properties from a time string."""
        if format_ok_keys is None:
            format_ok_keys = self._time_regex_map.keys()
        for format_ok_key, regex_list in self._time_regex_map.items():
            for regex in regex_list:
                result = regex.match(time_string)
                if result:
                    return result.groupdict()
        return {}

    def get_timezone_info(self, timezone_string, format_ok_keys=None):
        """Return the properties from a timezone string."""
        if format_ok_keys is None:
            format_ok_keys = self._timezone_regex_map.keys()
        for format_ok_key, regex_list in self._timezone_regex_map.items():
            for regex in regex_list:
                result = regex.match(timezone_string)
                if result:
                    return result.groupdict()
        return {}


class TimeIntervalParser(object):

    """Parser for ISO 8601 Durations (time intervals)."""

    INTERVAL_EXPRESSIONS = u"""
PnY
PnYnM
PnYnMnD
PnYnD
PnH
P
±ΫccYYMMDD
ccYYDDD
±ΫccYYDDD
ccYYWwwD
±ΫccYYWwwD""",
             
    INTERVAL_REGEXES = [
             re.compile(r"""^P(?:(?P<years>\d+)Y)?
                              (?:(?P<months>\d+)M)?
                              (?:(?P<days>\d+)D)?$""", re.X),
             re.compile(r"""^P(?:(?P<years>\d+)Y)?
                              (?:(?P<months>\d+)M)?
                              (?:(?P<days>\d+)D)?
                              T(?:(?P<hours>\d.*)H)?
                               (?:(?P<minutes>\d.*)M)?
                               (?:(?P<seconds>\d.*)S)?$""", re.X),
             re.compile(r"""^P(?P<weeks>\d+)W$""", re.X)]

    def parse(self, expression):
        for rec_regex in self.INTERVAL_REGEXES:
            result = rec_regex.search(expression)
            if not result:
                continue
            result_map = result.groupdict()
            for key, value in result_map.items():
                if value is None:
                    result_map.pop(key)
                    continue
                if key in ["years", "months", "days", "weeks"]:
                    value = int(value)
                else:
                    value = float(value)
                result_map[key] = value
            return TimeInterval(**result_map)
        raise SyntaxError("Not an ISO 8601 duration representation: %s" %
                          expression)

class TimePointInputError(ValueError):

    """An error denoting invalid inputs to the TimePoint class."""


class TimeRecurrence(object):

    """Represent a recurring time interval."""

    def __init__(self, repetitions=None, start_point=None,
                 interval=None, end_point=None, min_point=None,
                 max_point=None):
        self.repetitions = repetitions
        self.start_point = start_point
        self.interval = interval
        self.end_point = end_point
        self.min_point = min_point
        self.max_point = max_point
        self.format_number = None
        if self.interval is None:
            # First form.
            self.format_number = 1
            start_year, start_days = self.start_point.get_ordinal_date()
            start_seconds = self.start_point.get_second_of_day()
            end_year, end_days = self.end_point.get_ordinal_date()
            end_seconds = self.start_point.get_second_of_day()
            diff_days = end_days - start_days
            while end_year != start_year:
                diff_days += get_days_in_year(start_year)
                start_year += 1
            diff_seconds = end_seconds - start_seconds
            while diff_seconds < 0:
                diff_days -= 1
                diff_seconds += 86400
            while diff_seconds >= 86400:
                diff_days += 1
                diff_seconds -= 86400
            self.interval = TimeInterval(days=diff_days,
                                         seconds=diff_seconds)
        elif self.end_point is None:
            # Third form.
            self.format_number = 3
            if self.repetitions is not None:
                point = self.start_point
                for i in range(self.repetitions - 1):
                    point += self.interval
                self.end_point = point
        elif self.start_point is None:
            # Fourth form.
            self.format_number = 4
            if self.repetitions is not None:
                point = self.end_point
                for i in range(self.repetitions - 1):
                    point -= self.interval
                self.start_point = point
        else:
            raise ValueError("Unsupported or invalid recurrence information.")

    def __iter__(self):
        if self.start_point is None:
            point = self.end_point
            in_reverse = True
        else:
            point = self.start_point
            in_reverse = False
        
        while point is not None:
            yield point
            if in_reverse:
                point = self.get_prev(point)
            else:
                point = self.get_next(point)

    def get_is_valid(self, timepoint):
        """Return whether the timepoint is within this recurrence series."""
        if self.start_point is not None and timepoint < self.start_point:
            return False
        if self.min_point is not None and timepoint < self.min_point:
            return False
        if self.max_point is not None and timepoint > self.max_point:
            return False
        if self.end_point is not None and timepoint > self.end_point:
            return False
        return True

    def get_next(self, timepoint):
        """Return the next timepoint after this timepoint, or None."""
        next_timepoint = timepoint + self.interval
        if self.get_is_valid(next_timepoint):
            return next_timepoint
        return None

    def get_prev(self, timepoint):
        """Return the previous timepoint before this timepoint, or None."""
        prev_timepoint = timepoint - self.interval
        if self.get_is_valid(prev_timepoint):
            return next_timepoint
        return None

    def __str__(self):
        if self.repetitions is None:
            prefix = "R/"
        else:
            prefix = "R" + str(self.repetitions) + "/"
        if self.format_number == 1:
            return prefix + str(self.start_point) + "/" + str(self.end_point)
        elif self.format_number == 3:
            return prefix + str(self.start_point) + "/" + str(self.interval)
        elif self.format_number == 4:
            return prefix + str(self.interval) + "/" + str(self.end_point)
        return "R/?/?"


class TimeInterval(object):

    """Represent a duration or period of time."""

    def __init__(self, years=0, months=0, weeks=0, days=0,
                 hours=0.0, minutes=0.0, seconds=0.0):
        self.years = years
        self.months = months
        self.days = days + 7 * weeks
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

    def copy(self):
        """Return an unlinked copy of this instance."""
        return TimeInterval(years=self.years, months=self.months,
                            days=self.days, hours=self.hours,
                            minutes=self.minutes, seconds=self.seconds)

    def __add__(self, other):
        new = self.copy()
        if isinstance(other, TimeInterval):
            new.years += other.years
            new.months += other.months
            new.days += other.days
            new.hours += other.hours
            new.minutes += other.minutes
            new.seconds += other.seconds
            return new
        if isinstance(other, TimePoint):
            return other + new
        raise TypeError(
                  "Invalid type for addition: " +
                  "'%s' should be TimeInterval or TimePoint." %
                  type(other).__name__)

    def __sub__(self, other):
        new = self.copy()
        if isinstance(other, TimeInterval):
            new.years -= other.years
            new.months -= other.months
            new.days -= other.days
            new.hours -= other.hours
            new.minutes -= other.minutes
            new.seconds -= other.seconds
            return new
        if isinstance(other, TimePoint):
            return other - new
        raise TypeError(
                  "Invalid type for subtraction: " +
                  "'%s' should be TimeInterval or TimePoint." %
                  type(other).__name__)

    def __mul__(self, other):
        # TODO: support float multiplication?
        new = self.copy()
        if not isinstance(other, int):
            raise TypeError(
                  "Invalid type for multiplication: " +
                  "'%s' should be integer." %
                  type(other).__name__)
        new.years *= other
        new.months *= other
        new.days *= other
        new.hours *= other
        new.minutes *= other
        new.seconds *= other
        return new

    def __floordiv__(self, other):
        # TODO: support float division?
        new = self.copy()
        if not isinstance(other, int):
            raise TypeError(
                  "Invalid type for division: " +
                  "'%s' should be integer." %
                  type(other).__name__)
        new.years //= other
        new.months //= other
        new.days //= other
        new.hours //= other
        new.minutes //= other
        new.seconds //= other

    def __str__(self):
        start_string = "P"
        date_string = ""
        time_string = ""
        if self.years:
            date_string += str(self.years) + "Y"
        if self.months:
            date_string += str(self.months) + "M"
        if self.days:
            date_string += str(self.days) + "D"
        if self.hours:
            if int(self.hours) == self.hours:
                time_string += str(int(self.hours)) + "H"
            else:
                time_string += str(self.hours) + "H"
        if self.minutes:
            if int(self.minutes) == self.minutes:
                time_string += str(int(self.minutes)) + "M"
            else:
                time_string += str(self.minutes) + "M"
        if self.seconds:
            if int(self.seconds) == self.seconds:
                time_string += str(int(self.seconds)) + "S"
            else:
                time_string += str(self.seconds) + "S"
        if time_string:
            time_string = "T" + time_string
        elif not date_string:
            # Zero duration.
            date_string = "0Y"
        return start_string + date_string + time_string


class TimeZone(TimeInterval):

    """Represent a time zone offset."""

    def copy(self):
        """Return an unlinked copy of this instance."""
        return TimeZone(hours=self.hours, minutes=self.minutes)

    def __str__(self):
        if self.hours == 0 and self.minutes == 0:
            return "Z"
        else:
            if self.hours > 0:
                time_string = "+%02d" % self.hours
            else:
                time_string = "-%02d" % abs(self.hours)
            return time_string + ":%02d" % self.minutes


class TimePoint(object):

    """Represent an instant in time."""

    def __init__(self, **kwargs):
        self.format_function = kwargs.get("format_function")
        self.expanded_year_digits = kwargs.get("expanded_year_digits", 0)
        self.year = kwargs.get("year")
        self.month_of_year = kwargs.get("month_of_year")
        self.day_of_year = kwargs.get("day_of_year")
        self.day_of_month = kwargs.get("day_of_month")
        self.day_of_week = kwargs.get("day_of_week")
        self.week_of_year = kwargs.get("week_of_year")
        self.hour_of_day = kwargs.get("hour_of_day", 0)
        if "hour_of_day_decimal" in kwargs:
            if self.hour_of_day is None:
                raise TimePointInputError(
                          "Invalid input: hour decimal points - but not hours")
            self.hour_of_day += kwargs.get("hour_of_day_decimal")
            if "minute_of_hour" in kwargs:
                raise TimePointInputError(
                          "Invalid input: minutes - already have hour decimals")
            if "second_of_minute" in kwargs:
                raise TimePointInputError(
                          "Invalid input: seconds - already have hour decimals")
        if "minute_of_hour_decimal" in kwargs:
            if "minute_of_hour" not in kwargs:
                raise TimePointInputError(
                          "Invalid input: minute decimal points - but not minutes")
            self.minute_of_hour = kwargs["minute_of_hour"]
            self.minute_of_hour += kwargs["minute_of_hour_decimal"]
            if "second_of_minute" in kwargs:
                raise TimePointInputError(
                          "Invalid input: seconds - already have minute decimals")
        else:
            self.minute_of_hour = kwargs.get("minute_of_hour", 0)
        if "second_of_minute_decimal" in kwargs:
            if "second_of_minute" not in kwargs:
                raise TimePointInputError(
                          "Invalid input: second decimal points - but not seconds")
            self.second_of_minute = kwargs["second_of_minute"]
            self.second_of_minute += kwargs["second_of_minute_decimal"]
        else:
            self.second_of_minute = kwargs.get("second_of_minute", 0)
        self.time_zone = TimeZone()
        if "time_zone_hour" in kwargs:
            self.time_zone.hours = kwargs.get("time_zone_hour")
        if "time_zone_minute" in kwargs:
            self.time_zone.minutes = kwargs.get("time_zone_minute")

    def get_is_calendar_date(self):
        """Return whether this is in years, month-of-year, day-of-month."""
        return self.month_of_year is not None

    def get_is_ordinal_date(self):
        """Return whether this is in years, day-of-the year format."""
        return self.day_of_year is not None

    def get_is_week_date(self):
        """Return whether this is in years, week-of-year, day-of-week."""
        return self.week_of_year is not None

    def get_calendar_date(self):
        """Return the year, month-of-year and day-of-month for this date."""
        if self.get_is_calendar_date():
            return self.year, self.month_of_year, self.day_of_month
        if self.get_is_ordinal_date():
            return get_calendar_date_from_ordinal_date(self.year,
                                                       self.day_of_year)
        if self.get_is_week_date():
            return get_calendar_date_from_week_date(self.year,
                                                    self.week_of_year,
                                                    self.day_of_week)

    def get_hour_minute_second(self):
        """Return the time of day expressed in hours, minutes, seconds."""
        hour_of_day = self.hour_of_day
        minute_of_hour = self.minute_of_hour
        second_of_minute = self.second_of_minute
        if second_of_minute is None:
            if minute_of_hour is None:
                hour_decimals = hour_of_day - int(hour_of_day)
                hour_of_day = float(int(hour_of_day))
                minute_of_hour = 60 * hour_decimals
            minute_decimals = minute_of_hour - int(minute_of_hour)
            minute_of_hour = float(int(minute_of_hour))
            second_of_minute = 60 * minute_decimals
        return hour_of_day, minute_of_hour, second_of_minute

    def get_ordinal_date(self):
        """Return the year, day-of-year for this date."""
        if self.get_is_calendar_date():
            return get_ordinal_date_from_calendar_date(self.year,
                                                       self.month_of_year,
                                                       self.day_of_month)
        if self.get_is_ordinal_date():
            return self.year, self.day_of_year
        if self.get_is_week_date():
            return get_ordinal_date_from_week_date(self.year,
                                                   self.week_of_year,
                                                   self.day_of_week)

    def get_second_of_day(self):
        """Return the seconds elapsed since the start of the day."""
        second_of_day = 0
        if self.second_of_minute is not None:
            second_of_day += self.second_of_minute
        if self.minute_of_hour is not None:
            second_of_day += self.minute_of_hour * 60
        second_of_day += self.hour_of_day * 3600
        return second_of_day

    def get_time_zone(self):
        """Return the time_zone offset from UTC as a duration."""
        return self.time_zone

    def get_time_zone_utc(self):
        """Return whether the time zone is explicitly in UTC."""
        return self.time_zone.hours == 0 and self.time_zone.minutes == 0

    def get_week_date(self):
        """Return the year, week-of-year, day-of-week for this date."""
        if self.get_is_calendar_date():
            return get_week_date_from_calendar_date(self.year,
                                                    self.month_of_year,
                                                    self.day_of_month)
        if self.get_is_ordinal_date():
            return get_week_date_from_ordinal_date(self.year,
                                                   self.day_of_year)
        if self.get_is_week_date():
            return self.year, self.week_of_year, self.day_of_week

    def set_time_zone(self, dest_time_zone):
        """Adjust to the new time zone.

        dest_time_zone should be a TimeZone instance expressing difference
        from UTC, if any.

        """
        offset = dest_time_zone - self.time_zone
        if offset.minutes:
            if self.minute_of_hour is None:
                self.hour_of_day += offset.minutes / 3600.0
            else:
                self.minute_of_hour += offset.minutes
            self._tick_over()
        if offset.hours:
            self.hour_of_day += offset.hours
            self._tick_over()
        self.time_zone = dest_time_zone          

    def to_calendar_date(self):
        """Reformat the date in years, month-of-year, day-of-month."""
        year, month, day = self.get_calendar_date()
        self.year, self.month_of_year, self.day_of_month = year, month, day
        self.day_of_year = None
        self.week_of_year = None
        self.day_of_week = None
        return self

    def to_hour_minute_second(self):
        """Expand time fractions into hours, minutes, seconds."""
        hour, minute, second = self.get_hour_minute_second()
        self.hour_of_day = hour
        self.minute_of_hour = minute
        self.second_of_day = second

    def to_week_date(self):
        """Reformat the date in years, week-of-year, day-of-week."""
        self.year, self.week_of_year, self.day_of_week = self.get_week_date()
        self.day_of_year = None
        self.month_of_year = None
        self.day_of_month = None
        return self

    def to_ordinal_date(self):
        """Reformat the date in years and day-of-the-year."""
        self.year, self.day_of_year = self.get_ordinal_date()
        self.month_of_year = None
        self.day_of_month = None
        self.week_of_year = None
        self.day_of_week = None
        return self

    def add_truncated(self, year_of_century=None, month_of_year=None,
                      week_of_year=None, day_of_year=None, day_of_month=None,
                      day_of_week=None, hour_of_day=None, minute_of_hour=None,
                      second_of_minute=None):
        new = self.copy()
        if hour_of_day is not None and minute_of_hour is None:
            minute_of_hour = 0
        if ((hour_of_day is not None or minute_of_hour is not None) and
            second_of_minute is None):
            second_of_minute = 0
        if second_of_minute is not None or minute_of_hour is not None:
            new.to_hour_minute_second()
        if second_of_minute is not None:
            while new.second_of_minute != second_of_minute:
                new.second_of_minute += 1.0
                new._tick_over()
        if minute_of_hour is not None:
            while new.minute_of_hour != minute_of_hour:
                new.minute_of_hour += 1.0
                new._tick_over()
        if hour_of_day is not None:
            while new.hour_of_day != hour_of_day:
                new.hour_of_day += 1.0
                new._tick_over()
        if day_of_week is not None:
            new.to_week_date()
            while new.day_of_week != day_of_week:
                new.day_of_week += 1
                new._tick_over()
        if day_of_month is not None:
            new.to_calendar_date()
            while new.day_of_month != day_of_month:
                new.day_of_month += 1
                new._tick_over()
        if day_of_year is not None:
            new.to_ordinal_date()
            while new.day_of_year != day_of_year:
                new.day_of_year += 1
                new._tick_over()
        if week_of_year is not None:
            new.to_week_date()
            while new.week_of_year != week_of_year:
                new.week_of_year += 1
                new._tick_over()
        if month_of_year is not None:
            new.to_calendar_date()
            while new.month_of_year != month_of_year:
                new.month_of_year += 1
                new._tick_over()
        if year_of_century is not None:
            new.to_calendar_date()
            new_year_of_century = new.year % 100
            while new_year_of_century != year_of_century:
                new.year += 1
                new_year_of_century = new.year % 100
        return new

    def __add__(self, other, no_copy=False):
        if not isinstance(other, TimeInterval):
            raise TypeError(
                      "Invalid addition type '%s' - should be TimeInterval." %
                      type(other).__name__)
        duration = other
        if no_copy:
            new = self
        else:
            new = self.copy()
        if duration.seconds:
            if new.second_of_minute is None:
                if new.minute_of_hour is None:
                    new.hour_of_day += duration.seconds / 3600.0
                else:
                    new.minute_of_hour += duration.seconds / 60.0
            else:
                new.second_of_minute += duration.seconds
            new._tick_over()
        if duration.minutes:
            if new.minute_of_hour is None:
                new.hour_of_day += duration.minutes / 3600.0
            else:
                new.minute_of_hour += duration.minutes
            new._tick_over()
        if duration.hours:
            new.hour_of_day += duration.hours
            new._tick_over()
        if duration.days:
            if new.get_is_calendar_date():
                new.day_of_month += duration.days
            elif new.get_is_ordinal_date():
                new.day_of_year += duration.days
            else:
                new.day_of_week += duration.days
            new._tick_over()
        if duration.months:
            # This is the dangerous one...
            new._add_months(duration.months)
        if duration.years:
            new.year += duration.years
            month_index = (self.month_of_year - 1) % 12
            if get_is_leap_year(new.year):
                max_day_in_new_month = DAYS_OF_MONTHS_LEAP[month_index]
            else:
                max_day_in_new_month = DAYS_OF_MONTHS[month_index]
            if new.day_of_month > max_day_in_new_month:
                # For example, when Feb 29 - 1 year = Feb 28.
                new.day_of_month = max_day_in_new_month
        return new

    def copy(self):
        dummy_timepoint = TimePoint()
        for attr in ["expanded_year_digits", "year", "month_of_year",
                     "day_of_year", "day_of_month", "day_of_week",
                     "week_of_year", "hour_of_day", "minute_of_hour",
                     "second_of_minute"]:
            setattr(dummy_timepoint, attr, getattr(self, attr))
        dummy_timepoint.time_zone = self.time_zone.copy()
        return dummy_timepoint

    def __cmp__(self, other):
        if not isinstance(other, TimePoint):
            raise TypeError(
                      "Invalid comparison type '%s' - should be TimePoint." %
                      type(other).__name__)
        other = other.copy()
        other.set_time_zone(self.get_time_zone())
        if self.get_is_calendar_date():
            my_date = self.get_calendar_date()
            other_date = other.get_calendar_date()
        else:
            my_date = self.get_ordinal_date()
            other_date = other.get_ordinal_date()
        my_datetime = list(my_date) + [self.get_second_of_day()]
        other_datetime = list(other_date) + [self.get_second_of_day()]
        return cmp(my_datetime, other_datetime)

    def __sub__(self, other):
        if isinstance(other, TimePoint):
            other = other.copy().set_time_zone(self.get_time_zone())
            my_year, my_day_of_year = self.get_ordinal_date()
            other_year, other_day_of_year = other.get_ordinal_date()
            diff_year = my_year - other_year
            diff_day = my_day_of_year - other_day_of_year
            if my_year > other_year:
                for year in range(other_year, my_year):
                    diff_day += get_days_in_year(year)
            else:
                for year in range(my_year, other_year):
                    diff_day += get_days_in_year(year)
            my_time = self.get_time()
            other_time = other.get_time()
            diff_hour = my_time[0] - other_time[0]
            diff_minute = my_time[1] - other_time[1]
            diff_second = my_time[2] - other_time[2]
            return TimeInterval(years=diff_year, days=diff_day,
                                hours=diff_hour, minutes=diff_minute,
                                seconds=diff_second)
        if not isinstance(other, TimeInterval):
            raise TypeError(
                      "Invalid subtraction type " +
                      "'%s' - should be TimeInterval." %
                      type(other).__name__)
        duration = other
        return self.__add__(duration * -1)

    def _add_months(self, num_months):
        if num_months == 0:
            return
        was_ordinal_date = False
        was_week_date = False
        if not self.get_is_calendar_date():
            if self.get_is_ordinal_date():
                was_ordinal_date = True
            if self.get_is_week_date():
                was_week_date = True
            self.to_calendar_date()
        for i in range(abs(num_months)):
            if num_months > 0:
                self.month_of_year += 1
                if self.month_of_year > 12:
                    self.month_of_year -= 12
                    self.year += 1
            if num_months < 0:
                self.month_of_year -= 1
                if self.month_of_year < 1:
                    self.month_of_year += 12
                    self.year -= 1
            month_index = (self.month_of_year - 1) % 12
            if get_is_leap_year(self.year):
                max_day_in_new_month = DAYS_OF_MONTHS_LEAP[month_index]
            else:
                max_day_in_new_month = DAYS_OF_MONTHS[month_index]
            if self.day_of_month > max_day_in_new_month:
                # For example, when 31 March + 1 month = 30 April.
                self.day_of_month = max_day_in_new_month
        self._tick_over()
        if was_ordinal_date:
            self.to_ordinal_date()
        if was_week_date:
            self.to_week_date()

    def _tick_over(self):
        """Correct all the units going from smallest to largest."""
        if self.second_of_minute is not None:
            num_minutes, seconds = divmod(self.second_of_minute, 60)
            self.minute_of_hour += num_minutes
            self.second_of_minute = seconds
        if self.minute_of_hour is not None:
            num_hours, minutes = divmod(self.minute_of_hour, 60)
            self.hour_of_day += num_hours
            self.minute_of_hour = minutes
        if self.hour_of_day is not None:
            num_days, hours = divmod(self.hour_of_day, 24)
            if self.day_of_week is not None:
                self.day_of_week += num_days
            elif self.day_of_month is not None:
                self.day_of_month += num_days
            elif self.day_of_year is not None:
                self.day_of_year += num_days
            self.hour_of_day = hours
        if self.day_of_week is not None:
            num_weeks, days = divmod(self.day_of_week - 1, 7)
            self.week_of_year += num_weeks
            self.day_of_week = days + 1
        if self.day_of_month is not None:
            self._tick_over_day_of_month()
        if self.day_of_year is not None:
            while self.day_of_year < 1:
                days_in_last_year = get_days_in_year(self.year - 1)
                self.day_of_year += days_in_last_year
                self.year -= 1
            while self.day_of_year > get_days_in_year(self.year):
                days_in_next_year = get_days_in_year(self.year + 1)
                self.day_of_year -= days_in_next_year
                self.year += 1
        if self.week_of_year is not None:
            while self.week_of_year < 1:
                weeks_in_last_year = get_weeks_in_year(self.year - 1)
                self.week_of_year += weeks_in_last_year
                self.year -= 1
            while self.week_of_year > get_weeks_in_year(self.year):
                weeks_in_this_year = get_weeks_in_year(self.year)
                self.week_of_year -= weeks_in_this_year
                self.year += 1
        if self.month_of_year is not None:
            while self.month_of_year < 1:
                self.month_of_year += 12
                self.year -= 1
            while self.month_of_year > 12:
                self.month_of_year -= 12
                self.year += 1

    def _tick_over_day_of_month(self):
        if self.day_of_month < 1:
            num_days = 2
            for month, day in iter_months_days(
                                    self.year,
                                    month_of_year=self.month_of_year,
                                    day_of_month=1, in_reverse=True):
                num_days -= 1
                if num_days == self.day_of_month:
                    self.month_of_year = month
                    self.day_of_month = day
                    break
            else:
                start_year = self.year
                while num_days != self.day_of_month:
                    start_year -= 1
                    for month, day in iter_months_days(
                                            start_year, in_reverse=True):
                        num_days -= 1
                self.year = start_year
                self.month_of_year = month
                self.day_of_month = day
        else:
            month_index = (self.month_of_year - 1) % 12
            if get_is_leap_year(self.year):
                max_day_in_month = DAYS_OF_MONTHS_LEAP[month_index]
            else:
                max_day_in_month = DAYS_OF_MONTHS[month_index]
            if self.day_of_month > max_day_in_month:
                num_days = 0
                for month, day in iter_months_days(
                                        self.year,
                                        month_of_year=self.month_of_year,
                                        day_of_month=1):
                    num_days += 1
                    if num_days == self.day_of_month:
                        self.month_of_year = month
                        self.day_of_month = day
                        break
                else:
                    start_year = self.year
                    while num_days != self.day_of_month:
                        start_year += 1
                        for month, day in iter_months_days(start_year):
                            num_days += 1
                            if num_days == self.day_of_month:
                                self.year = start_year
                                self.month_of_year = month
                                self.day_of_month = day
                                return

    def __str__(self):
        if self.format_function is not None:
            return self.format_function(self)
        year_digits = 4 + self.expanded_year_digits
        year_string = "%0" + str(year_digits) + "d"
        if self.expanded_year_digits:
            if self.year < 0:
                year_string = "-" + year_string % abs(self.year)
            else:
                year_string = "+" + year_string % abs(self.year)
        elif self.year < 0:
            raise OverflowError(
                      "Year %s can only be represented in expanded format" %
                      self.year)
        else:
            year_string = year_string % self.year
        if self.get_is_calendar_date():
            date_string = year_string + "-%02d-%02d" % (self.month_of_year,
                                                        self.day_of_month)
        if self.get_is_ordinal_date():
            date_string = year_string + "-%03d" % self.day_of_year
        if self.get_is_week_date():
            date_string = year_string + "-W%02d-%01d" % (self.week_of_year,
                                                         self.day_of_week)
        time_string = ""
        if self.hour_of_day is not None:
            time_string = "T%02d" % int(self.hour_of_day)
            if int(self.hour_of_day) != self.hour_of_day:
                time_string += "," + str(self.hour_of_day - int(self.hour_of_day))[2:]
            else:
                time_string += ":%02d" % int(self.minute_of_hour)
                if int(self.minute_of_hour) != self.minute_of_hour:
                    time_string += "," + str(self.minute_of_hour - int(self.minute_of_hour))[2:]
                else:
                    time_string += ":%02d" % int(self.second_of_minute)
                    if int(self.second_of_minute) != self.second_of_minute:
                        time_string += "," + str(self.second_of_minute - int(self.second_of_minute))[2:]
        if time_string:
            time_string += str(self.time_zone)
        return date_string + time_string

    __repr__ = __str__


def cache_results(func):
    """Decorator to store results for given inputs.

    func is the decorated function.

    A maximum of 100000 arg-value pairs are stored.

    """
    cache = {}
    def wrap_func(*args, **kwargs):
        key = (str(args), str(kwargs))
        if key in cache:
            return cache[key]
        else:
            results = func(*args, **kwargs)
            if len(cache) < 100000:
                cache[key] = results
            return results
    return wrap_func


@cache_results
def get_is_leap_year(year):
    """Return if year is a leap year in the proleptic Gregorian calendar."""
    if year % 4 == 0:
        # A multiple of 4.
        if year % 100 == 0 and year % 400 != 0:
            # A centennial leap year must be a multiple of 400.
            return False
        return True
    return False


@cache_results
def get_days_in_year(year):
    """Return 366 if year is a leap year, otherwise 365."""
    if get_is_leap_year(year):
        return 366
    return 365


@cache_results
def get_weeks_in_year(year):
    """Return the number of calendar weeks in this week date year."""
    cal_year, cal_ord_days = get_ordinal_date_week_date_start(year)
    cal_year_next, cal_ord_days_next = get_ordinal_date_week_date_start(
                                                             year + 1)
    diff_days = cal_ord_days_next - cal_ord_days
    while cal_year_next != cal_year:
        diff_days += get_days_in_year(cal_year)
        cal_year += 1
    return diff_days / 7


def get_calendar_date_from_ordinal_date(year, day_of_year):
    """Translate an ordinal date into a calendar date.

    Returns the calendar year, calendar month, calendar day-of-month.

    Arguments:
    year is an integer that denotes the ordinal date year
    day_of_year is an integer that denotes the ordinal day in the year.

    """
    iter_num_days = 0
    for iter_month, iter_day in iter_months_days(year):
        iter_num_days += 1
        if iter_num_days == day_of_year:
            return year, iter_month, iter_day
    raise ValueError("Bad ordinal date: %s-%03d" % (year, day_of_year))


def get_calendar_date_from_week_date(year, week_of_year, day_of_week):
    """Translate a week date into a calendar date.

    Returns the calendar year, calendar month, calendar day-of-month.

    Arguments:
    year is an integer that denotes the week date year (may differ
    from calendar year)
    week_of_year is an integer that denotes the week number in the year
    day_of_week is an integer that denotes the day of the week (1-7).

    """
    num_days_week_year = (week_of_year - 1) * 7 + day_of_week - 1
    start_year, start_month, start_day = get_calendar_date_week_date_start(year)
    if num_days_week_year == 0:
        return start_year, start_month, start_day
    total_iter_days = 0
    # Loop over the months and days left in the start year.
    for iter_month, iter_day in iter_months_days(
                                        start_year,
                                        month_of_year=start_month,
                                        day_of_month=start_day + 1):
        total_iter_days += 1
        if num_days_week_year == total_iter_days:
            return start_year, iter_month, iter_day
    if start_year < year:
        # We've only looped over the last year - now the current one.
        for iter_month, iter_day in iter_months_days(year):
            total_iter_days += 1
            if num_days_week_year == total_iter_days:
                return year, iter_month, iter_day                
    for iter_month, iter_day in iter_months_days(year + 1):
        # Loop over the following year.
        total_iter_days += 1
        if num_days_week_year == total_iter_days:
            return year + 1, iter_month, iter_day
    raise ValueError("Bad week date: %s-W%02d-%s" % (year,
                                                     week_of_year,
                                                     day_of_week))


def get_ordinal_date_from_calendar_date(year, month_of_year, day_of_month):
    """Translate a calendar date into an ordinal date.

    Returns the ordinal year, calendar month, calendar day-of-month.

    Arguments:
    year is an integer that denotes the year
    month_of_year is an integer that denotes the month number in the
    year.
    day_of_month is an integer that denotes the day number in the
    month_of_year.

    """
    iter_num_days = 0
    for iter_month, iter_day in iter_months_days(year):
        iter_num_days += 1
        if iter_month == month_of_year and iter_day == day_of_month:
            return year, iter_num_days
    raise ValueError("Bad calendar date: %s-%02d-%02d" % (year,
                                                          month_of_year,
                                                          day_of_month))


def get_ordinal_date_from_week_date(year, week_of_year, day_of_week):
    """Translate a week date into an ordinal date.

    Returns the ordinal year, ordinal day-of-year.

    Arguments:
    year is an integer that denotes the week date year (which may
    differ from the ordinal or calendar year)
    week_of_year is an integer that denotes the week number in the
    year.
    day_of_week is an integer that denotes the day number in the
    week_of_year.

    """
    cal_year, cal_month, cal_day_of_month = get_calendar_date_from_week_date(
                                            year, week_of_year, day_of_week)
    return get_ordinal_date_from_calendar_date(
                                 cal_year, cal_month, cal_day_of_month)


def get_week_date_from_calendar_date(year, month_of_year, day_of_month):
    """Translate a calendar date into an week date.

    Returns the week date year, week-of-year, day-of-week.

    Arguments:
    year is an integer that denotes the calendar year, which may
    differ from the week date year.
    month_of_year is an integer that denotes the month number in the
    above year.
    day_of_month is an integer that denotes the day number in the
    above month_of_year.

    """
    prev_start = get_calendar_date_week_date_start(year - 1)
    this_start = get_calendar_date_week_date_start(year)
    next_start = get_calendar_date_week_date_start(year + 1)

    cal_date = (year, month_of_year, day_of_month)
    
    if prev_start <= cal_date < this_start:
        # This calendar date is in the previous week date year.
        start_year, start_month, start_day = prev_start
        week_date_start_year = year - 1
    elif this_start <= cal_date < next_start:
        # This calendar date is in the same week date year.
        start_year, start_month, start_day = this_start
        week_date_start_year = year
    else:
        # This calendar date is in the next week date year.
        start_year, start_month, start_day = next_start
        week_date_start_year = year + 1

    total_iter_days = -1
    # A week date year can theoretically span 3 calendar years...
    for iter_month, iter_day in iter_months_days(start_year,
                                                 month_of_year=start_month,
                                                 day_of_month=start_day):
        total_iter_days += 1
        if (start_year == year and
            iter_month == month_of_year and
            iter_day == day_of_month):
            week_of_year = (total_iter_days / 7) + 1
            day_of_week = (total_iter_days % 7) + 1
            return week_date_start_year, week_of_year, day_of_week

    for iter_start_year in [start_year + 1, start_year + 2]:
        # Look at following year when the calendar date is e.g. very early Jan.
        for iter_month, iter_day in iter_months_days(iter_start_year):
            total_iter_days += 1
            if (iter_start_year == year and
                iter_month == month_of_year and
                iter_day == day_of_month):
                week_of_year = (total_iter_days / 7) + 1
                day_of_week = (total_iter_days % 7) + 1
                return week_date_start_year, week_of_year, day_of_week
    raise ValueError("Bad calendar date: %s-%02d-%02d" % (year,
                                                          month_of_year,
                                                          day_of_month))


def get_week_date_from_ordinal_date(year, day_of_year):
    """Translate an ordinal date into a week date.

    Returns the week date year, week-of-year, day-of-week.

    Arguments:
    year is an integer that denotes the ordinal date year, which
    may differ from the week date year.
    day_of_year is an integer that denotes the ordinal day in the year.

    """
    year, month, day = get_calendar_date_from_ordinal_date(year, day_of_year)
    return get_week_date_from_calendar_date(year, month, day)


@cache_results
def get_calendar_date_week_date_start(year):
    """Return the calendar date of the start of (week date) year."""
    ref_year, ref_month, ref_day = WEEK_DAY_START_REFERENCE["calendar"]
    ref_year, ref_ordinal_day = WEEK_DAY_START_REFERENCE["ordinal"]
    if year == ref_year:
        return ref_year, ref_month, ref_day
    # Calculate the weekday for 1 January in this calendar year.
    if year > ref_year:
        years = range(ref_year, year)
        days_diff = 1 - ref_ordinal_day
    else:
        years = range(ref_year - 1, year - 1, -1)
        days_diff = ref_ordinal_day - 2
    for intervening_year in years:
        days_diff += get_days_in_year(intervening_year)
    weekdays_diff = (days_diff) % 7
    if year > ref_year:
        day_of_week_start_year = weekdays_diff + 1
    else:
        day_of_week_start_year = 7 - weekdays_diff # Jan 1 as day of week.       
    if day_of_week_start_year == 1:
        return year, 1, 1
    if day_of_week_start_year > 4:
        # This week belongs to the previous year; get the next Monday.
        day = 1 + (8 - day_of_week_start_year)
        return year, 1, day
    # The week starts in the previous year - get the previous Monday.
    for month, day in iter_months_days(year - 1, in_reverse=True):
        day_of_week_start_year -= 1
        if day_of_week_start_year == 1:
            return year - 1, month, day


@cache_results
def get_days_since_1_ad(year):
    """Return the number of days since Jan 1, 1 A.D. to the year end."""
    if year == 1:
        return get_days_in_year(year)
    elif year < 1:
        return 0
    return get_days_since_1_ad(year - 1) + get_days_in_year(year)


@cache_results
def get_ordinal_date_week_date_start(year):
    """Return the week date start for year in year, day-of-year."""
    cal_year, cal_month, cal_day = get_calendar_date_week_date_start(year)
    total_days = 0
    for iter_month, iter_day in iter_months_days(cal_year):
        total_days += 1
        if iter_month == cal_month and iter_day == cal_day:
            return cal_year, total_days


def iter_months_days(year, month_of_year=None, day_of_month=None,
                     in_reverse=False):
    """Iterate over each day in each month of year.

    year is an integer specifying the year to use.
    month_of_year is an optional integer, specifying a start month.
    day_of_month is an optional integer, specifying a start day.
    in_reverse is an optional boolean that reverses the iteration if
    True (default False).

    """
    source = DAYS_OF_MONTHS
    if get_is_leap_year(year):
        source = DAYS_OF_MONTHS_LEAP
    if day_of_month is not None and month_of_year is None:
        raise ValueError("Need to specify start month as well as day.")
    if in_reverse:
        if month_of_year is None:
            for i, days in enumerate(reversed(source)):
                day_range = range(days, 0, -1)
                j = len(source) - i
                for day in day_range:
                    yield j, day
        else:
            for i, days in enumerate(reversed(source)):
                j = len(source) - i
                if j > month_of_year:
                    continue
                elif j == month_of_year and day_of_month is not None:
                    day_range = range(day_of_month, 0, -1)
                else:
                    day_range = range(days, 0, -1)
                for day in day_range:
                    yield j, day
    else:
        if month_of_year is None:
            for i, days in enumerate(source):
                day_range = range(1, days + 1)
                for day in day_range:
                    yield i + 1, day
        else:
            for i, days in enumerate(source):
                if i + 1 < month_of_year:
                    continue
                elif i + 1 == month_of_year and day_of_month is not None:
                    day_range = range(day_of_month, days + 1)
                else:
                    day_range = range(1, days + 1)
                for day in day_range:
                    yield i + 1, day


def parse_timepoint_expression(timepoint_expression):
    parser = TimePointParser()
    return parser.parse_timepoint_expression(timepoint_expression)


def test():
    import datetime
    import random
    my_date = datetime.datetime(100, 11, 1)
    while my_date <= datetime.datetime(111, 2, 1):
        ctrl_data = my_date.isocalendar()
        test_date = TimePoint(year=my_date.year, month_of_year=my_date.month,
                              day_of_month=my_date.day)
        test_data = test_date.get_week_date()
        if ctrl_data == test_data:
            pass
        else:
            print "DIFF", my_date.isoformat(), ctrl_data, test_data
            raise ValueError("week date conversion test failed for %s" % my_date.isoformat())
        ctrl_data = (my_date.year, my_date.month, my_date.day)
        test_data = test_date.to_week_date().get_calendar_date()
        if ctrl_data == test_data:
            pass
        else:
            print "DIFF", my_date.isoformat(), ctrl_data, test_data
            raise ValueError("calendar->week->calendar test failed for %s" % my_date.isoformat())
        ctrl_data = my_date.toordinal()
        year, day_of_year = test_date.get_ordinal_date()
        test_data = day_of_year
        test_data += get_days_since_1_ad(year - 1)
        if test_data == ctrl_data:
            pass
        else:
            print "DIFF", my_date.isoformat(), ctrl_data, test_data
            raise ValueError("ordinal test failed for %s" % my_date.isoformat())
        for attribute, attr_max in [("weeks", 110),
                                    ("days", 770),
                                    ("hours", 770*24),
                                    ("minutes", 770 * 24 * 60),
                                    ("seconds", 770 * 24 * 60 * 60)]:
            delta_attr = random.randrange(0, attr_max)
            kwargs = {attribute: delta_attr}
            ctrl_data = my_date + datetime.timedelta(**kwargs)
            ctrl_data = (ctrl_data.year, ctrl_data.month, ctrl_data.day)
            test_data = (test_date + TimeInterval(**kwargs)).get_calendar_date()
            if test_data == ctrl_data:
                pass
            else:
                print "DIFF", my_date.isoformat(), ctrl_data, test_data
                raise ValueError("add num test failed for %s + %s" % my_date.isoformat(), datetime.timedelta(**kwargs))
            ctrl_data = (my_date - datetime.timedelta(**kwargs))
            ctrl_data = (ctrl_data.year, ctrl_data.month, ctrl_data.day)
            test_data = (test_date - TimeInterval(**kwargs)).get_calendar_date()
            if test_data == ctrl_data:
                pass
            else:
                print "DIFF", my_date.isoformat(), ctrl_data, test_data
                raise ValueError("subtract num test failed for %s" % my_date.isoformat(), datetime.timedelta(**kwargs))
        ctrl_data = (my_date + datetime.timedelta(minutes=450) +
                     datetime.timedelta(hours=5) -
                     datetime.timedelta(seconds=500, weeks=5))
        ctrl_data = [(ctrl_data.year, ctrl_data.month, ctrl_data.day),
                     (ctrl_data.hour, ctrl_data.minute, ctrl_data.second)]
        test_data = (test_date + TimeInterval(minutes=450) +
                     TimeInterval(hours=5) - TimeInterval(weeks=5, seconds=500))
        test_data = [test_data.get_calendar_date(),
                     test_data.get_hour_minute_second()]
        if test_data == ctrl_data:
            pass
        else:
            print "DIFF", my_date.isoformat(), ctrl_data, test_data
            raise ValueError("complex duration test failed for %s" % my_date.isoformat())
        print my_date.isoformat()
        timedelta = datetime.timedelta(days=1)
        my_date += timedelta
        


def test_and_profile():
    import cProfile, pstats
    import tempfile
    f = tempfile.NamedTemporaryFile()
    cProfile.runctx("test()", globals(), locals(), f.name)
    stats = pstats.Stats(f.name)
    stats.strip_dirs().sort_stats('cumulative').print_stats(200)
