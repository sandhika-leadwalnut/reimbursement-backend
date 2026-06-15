import datetime

def calculate_payment_date(submission_date: datetime.date) -> datetime.date:
    """
    Calculate the payment date based on the following rules:
    - Start from reimbursement submission date.
    - Add 10 business days (excluding Saturday, Sunday).
    - If the calculated date falls within ±3 calendar days of the 5th or 20th,
      assign that payment date.
    - Else, move to the next payment cycle (5th or 20th).
    """
    current_date = submission_date
    added_days = 0
    while added_days < 10:
        current_date += datetime.timedelta(days=1)
        if current_date.weekday() < 5:
            added_days += 1

    fifth_of_month = current_date.replace(day=5)
    twentieth_of_month = current_date.replace(day=20)
    
    if current_date.month == 12:
        next_month_fifth = current_date.replace(year=current_date.year + 1, month=1, day=5)
    else:
        next_month_fifth = current_date.replace(month=current_date.month + 1, day=5)
        
    diff_fifth = (current_date - fifth_of_month).days
    diff_twentieth = (current_date - twentieth_of_month).days
    diff_next_fifth = (current_date - next_month_fifth).days
    
    if -3 <= diff_fifth <= 3:
        return fifth_of_month
    elif -3 <= diff_twentieth <= 3:
        return twentieth_of_month
    elif -3 <= diff_next_fifth <= 3:
        return next_month_fifth
    else:
        # If it falls outside the ±3 day window, move to the next payment cycle
        if current_date.day < 5:
            return fifth_of_month
        elif current_date.day < 20:
            return twentieth_of_month
        else:
            return next_month_fifth
