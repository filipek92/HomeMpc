from datetime import datetime

def get_electricity_price(state_list, entity_id):
    now = datetime.now().replace(minute=0, second=0, microsecond=0).astimezone()
    for e in state_list:
        if e["entity_id"] == entity_id:
            attributes = e.get("attributes", {})
            filtered = [
                (k, v) for k, v in attributes.items()
                if k.startswith("202")
            ]
            filtered = [
                (k, v) for k, v in filtered
                if datetime.fromisoformat(k).astimezone(now.tzinfo) >= now
            ]
            sorted_series = sorted(filtered, key=lambda x: x[0])
            return [
                (datetime.fromisoformat(k), float(v))
                for k, v in sorted_series
            ]
    return []