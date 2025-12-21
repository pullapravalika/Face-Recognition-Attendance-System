import datetime
from collections import defaultdict

def calculate_attendance_percentage(attendance_records, total_sessions):
    """
    Calculate attendance percentage.
    attendance_records: list or count of attended sessions
    total_sessions: total number of sessions held
    """
    if total_sessions == 0:
        return 0
    return round((len(attendance_records) / total_sessions) * 100, 2)

def group_attendance_by_month(attendance_list):
    """
    Group attendance dates by month-year.
    attendance_list: list of datetime.date or datetime.datetime objects
    Returns a dict: { 'YYYY-MM': count_of_days_present }
    """
    monthly_attendance = defaultdict(int)
    for date in attendance_list:
        key = date.strftime('%Y-%m')
        monthly_attendance[key] += 1
    return dict(monthly_attendance)

def get_date_range(start_date, end_date):
    """Generate a list of dates between start_date and end_date inclusive."""
    delta = end_date - start_date
    return [start_date + datetime.timedelta(days=i) for i in range(delta.days + 1)]

def filter_attendance_by_date(attendance_list, start_date, end_date):
    """Filter attendance records between two dates inclusive."""
    return [date for date in attendance_list if start_date <= date <= end_date]
