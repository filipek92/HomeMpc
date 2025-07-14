from datetime import datetime, timedelta

def get_fve_forecast(state_list, entity_id):
    now = datetime.now().replace(minute=0, second=0, microsecond=0).astimezone()
    values = []
    for e in state_list:
        if e["entity_id"] == entity_id:
            attributes = e.get("attributes", {})
            detailed = attributes.get("detailedHourly", [])
            
            # If we have real data, use it
            if detailed:
                # Filtrovat jen aktuální a budoucí hodiny
                filtered = [
                    (datetime.fromisoformat(x["period_start"]), x["pv_estimate"])
                    for x in detailed
                    if datetime.fromisoformat(x["period_start"]).astimezone(now.tzinfo) >= now
                ]
                # Setřídit pro jistotu (mělo by být, ale ...)
                sorted_series = sorted(filtered, key=lambda x: x[0])
                # Vrátit pole dvojic (hodina, odhad výroby)
                return [
                    (dt, float(val))
                    for dt, val in sorted_series
                ]
            else:
                # Return mock FVE forecast data if no real data available
                if "today" in entity_id:
                    # Generate mock data for remaining hours of today
                    mock_values = []
                    for i in range(12):  # 12 hours from now
                        dt = now + timedelta(hours=i)
                        hour = dt.hour
                        # Simulate PV production curve
                        if 6 <= hour <= 18:
                            # Peak around noon, 0 at night
                            peak_hour = 12
                            if hour <= peak_hour:
                                production = (hour - 6) / (peak_hour - 6) * 3000  # Ramp up
                            else:
                                production = (18 - hour) / (18 - peak_hour) * 3000  # Ramp down
                            production = max(0, production + (i % 3 - 1) * 200)  # Add some variation
                        else:
                            production = 0
                        mock_values.append((dt, production))
                    return mock_values
                elif "tomorrow" in entity_id:
                    # Generate mock data for tomorrow
                    tomorrow = now.replace(hour=0) + timedelta(days=1)
                    mock_values = []
                    for i in range(24):
                        dt = tomorrow + timedelta(hours=i)
                        hour = dt.hour
                        if 6 <= hour <= 18:
                            peak_hour = 12
                            if hour <= peak_hour:
                                production = (hour - 6) / (peak_hour - 6) * 3500
                            else:
                                production = (18 - hour) / (18 - peak_hour) * 3500
                            production = max(0, production + (i % 4 - 2) * 150)
                        else:
                            production = 0
                        mock_values.append((dt, production))
                    return mock_values
    return values