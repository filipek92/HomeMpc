from datetime import datetime

def get_fve_forecast(state_list, entity_id):
    now = datetime.now().replace(minute=0, second=0, microsecond=0).astimezone()
    values = []
    for e in state_list:
        if e["entity_id"] == entity_id:
            attributes = e.get("attributes", {})
            detailed = attributes.get("detailedHourly", [])
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
    return values