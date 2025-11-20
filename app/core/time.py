from datetime import datetime, timezone, timedelta

def now_utc8():
    """返回东八区的当前时间"""
    return datetime.now(timezone(timedelta(hours=8)))