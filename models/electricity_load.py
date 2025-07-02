def get_electricity_load(time):
    if time.hour < 6:
        return 0.0
    elif time.hour < 9:
        return 2.0
    elif time.hour < 12:
        return 1.5
    elif time.hour < 18:
        return 1.0
    elif time.hour < 21:
        return 0.5
    else:
        return 0.0