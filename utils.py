from datetime import datetime, timedelta
from time import timezone

def calculate_next_run(start_time_utc, interval_seconds, from_time=None):
    if from_time is None:
        from_time = datetime.now(timezone.utc)
    if from_time < start_time_utc:
        return start_time_utc
    elapsed = (from_time - start_time_utc).total_seconds()
    intervals_passed = int(elapsed // interval_seconds) + 1
    next_run = start_time_utc + timedelta(seconds=intervals_passed * interval_seconds)
    return next_run