from datetime import datetime
from requests import get

from local_settings import GOOGLE_URL, GOOGLE_PREDICT_URL, GOOGLE_API_KEY
from local_settings import GOOGLE_GEOCODE_URL
from local_settings import BING_URL, BING_API_KEY


def google_trace(start, stop, method):
    params = {
        "departure_time": "now",
        "key": GOOGLE_API_KEY,
        "mode": method,
        "origins": start,
        "destinations": stop,
        "region": "nz",
        "units": "metric",
        "traffic_model": "best_guess",
    }
    ret = get(GOOGLE_URL, params=params, timeout=(2, 5))
    assert ret.ok

    data = ret.json()
    assert data["status"] == "OK"

    item = data["rows"][0]["elements"][0]
    distance = item["distance"]["value"]
    if method == "driving":
        duration = item["duration_in_traffic"]["value"]
    else:
        duration = item["duration"]["value"]
    return {"distance": distance, "duration": duration}


def bing_trace(start, stop, method="driving", start_lat="", stop_lat=""):
    assert method in ["driving", "transit"]
    params = {
        "timeUnit": "second",
        "key": BING_API_KEY,
        "travelMode": method,
    }
    if method == "driving":
        params["startTime"] = datetime.utcnow().isoformat()

    if start_lat and stop_lat:
        params["origins"] = start_lat
        params["destinations"] = stop_lat
    else:
        params["origins"] = address_translate(start)
        params["destinations"] = address_translate(stop)
    ret = get(BING_URL, params=params, timeout=(2, 5))
    assert ret.ok, "bing fetching error"

    data = ret.json()
    assert data["statusCode"] == 200, "status code is not 200"

    result = data["resourceSets"][0]["resources"][0]["results"][0]
    # print result
    return {
        "distance": result["travelDistance"] * 1000,
        "duration": result["travelDuration"],
    }


def address_suggest(input_text, session_token=""):
    """
    TODO: use session token
    """
    params = {
        "key": GOOGLE_API_KEY,
        "components": "country:nz",
        "types": "address",
        "sessiontoken": session_token,
        "input": input_text,
    }
    ret = get(GOOGLE_PREDICT_URL, params=params, timeout=(2, 5))
    assert ret.ok

    data = ret.json()
    predictions = data["predictions"]
    return [i["description"] for i in predictions]


def address_translate(address_text):
    """
    address_text => latitude, longitude
    """
    params = {
        "key": GOOGLE_API_KEY,
        "address": address_text,
    }
    ret = get(GOOGLE_GEOCODE_URL, params=params, timeout=(2, 5))
    assert ret.ok

    data = ret.json()
    location = data["results"][0]["geometry"]["location"]
    return "{},{}".format(location["lat"], location["lng"])


if __name__ == "__main__":
    # address_suggest("188 carrin", "123456")
    # address_translate("68 stanhope road, auckland")
    print bing_trace(
        "60 stanhope road, auckland",
        "188 carrington road, auckland", "driving")
    print google_trace(
        "60 stanhope road, auckland",
        "188 carrington road, auckland", "driving")
