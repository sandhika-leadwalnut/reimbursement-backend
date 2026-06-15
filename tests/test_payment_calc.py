import datetime
from utils.payment_calc import calculate_payment_date

def test_payment_date_calculation():
    # Example 1: 3rd -> 10 business days = 17th -> Wait, let's trace:
    # 3rd + 10 bus days. Let's say 3rd is Monday.
    # 10 business days later is the 17th (Monday).
    # 17th is within 3 days of 20th. So payment date is 20th.
    
    submission_date = datetime.date(2026, 6, 1) # June 1st, 2026 is Monday
    # +10 bus days -> June 15th (Monday)
    # diff to 20th is 5 days. Not within 3 days of 20th.
    # So next cycle is 20th.
    calc_date = calculate_payment_date(submission_date)
    assert calc_date == datetime.date(2026, 6, 20)
    
    # Example from requirements:
    # 17th -> 10 bus days = next month 1st. Next month 5th is within 4 days...
    # The requirement says "Start from reimbursement submission date... Add 10 business days... If calculated 10-business-day date falls within +-3 calendar days of 5th or 20th, assign that payment date."
    
    # 3rd (Wednesday, June 3rd, 2026). 
    # 10 bus days -> June 17th (Wednesday). 
    # June 17th is within 3 days of June 20th. Payment = June 20th.
    sub_3rd = datetime.date(2026, 6, 3)
    calc_3rd = calculate_payment_date(sub_3rd)
    assert calc_3rd == datetime.date(2026, 6, 20)

    # 17th (Wednesday, June 17th, 2026).
    # 10 bus days -> July 1st (Wednesday).
    # July 1st is within 4 days of July 5th... wait, diff is 4 days.
    # So it moves to next cycle = July 5th.
    sub_17th = datetime.date(2026, 6, 17)
    calc_17th = calculate_payment_date(sub_17th)
    assert calc_17th == datetime.date(2026, 7, 5)
