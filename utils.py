import datetime


def timesince(d, now=None):
    chunks = (
      (60 * 60 * 24 * 365, ('year', 'years')),
      (60 * 60 * 24 * 30, ('month', 'months')),
      (60 * 60 * 24 * 7, ('week', 'weeks')),
      (60 * 60 * 24, ('day', 'days')),
      (60 * 60, ('hour', 'hours')),
      (60, ('minute', 'minutes')),
      (1, ('second', 'seconds'))
    )

    # Convert int or float (unix epoch) to datetime.datetime for comparison
    if isinstance(d, int) or isinstance(d, float):
        d = datetime.datetime.fromtimestamp(d)

    # Convert datetime.date to datetime.datetime for comparison.
    if not isinstance(d, datetime.datetime):
        d = datetime.datetime(d.year, d.month, d.day)
    if now and not isinstance(now, datetime.datetime):
        now = datetime.datetime(now.year, now.month, now.day)

    if not now:
        now = datetime.datetime.now()

    # ignore microsecond part of 'd' since we removed it from 'now'
    delta = now - (d - datetime.timedelta(0, 0, d.microsecond))
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # d is in the future compared to now, stop processing.
        return u'0 ' + 'seconds'
    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            break

    if count == 1:
        s = '%(number)d %(type)s' % {'number': count, 'type': name[0]}
    else:
        s = '%(number)d %(type)s' % {'number': count, 'type': name[1]}

    if i + 1 < len(chunks):
        # now get the second item
        seconds2, name2 = chunks[i + 1]
        count2 = (since - (seconds * count)) // seconds2
        if count2 != 0:
            if count2 == 1:
                s += ', %d %s' % (count2, name2[0])
            else:
                s += ' and %d %s' % (count2, name2[1])
    return s
