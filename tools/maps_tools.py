"""Location tools for the maps agent.

Uses the Google Maps Platform when GOOGLE_MAPS_API_KEY is set, and falls back
to OpenStreetMap Nominatim for geocoding when it is not.
"""
import logging
import os
import urllib.parse

import requests

logger = logging.getLogger(__name__)
TIMEOUT = 10


def _maps_key():
    return os.getenv("GOOGLE_MAPS_API_KEY")


def _search_link(query: str) -> str:
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(query)


def geocode_address(address: str) -> dict:
    """Resolve an address or zip code to latitude and longitude.

    Args:
        address: Street address, place name, or zip code.

    Returns:
        A dict with status, formatted_address, latitude, longitude and a Google Maps link.
    """
    key = _maps_key()
    try:
        if key:
            r = requests.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={"address": address, "key": key},
                timeout=TIMEOUT,
            )
            data = r.json()
            if data.get("status") == "OK":
                res = data["results"][0]
                loc = res["geometry"]["location"]
                return {
                    "status": "success",
                    "source": "google_geocoding",
                    "formatted_address": res["formatted_address"],
                    "latitude": loc["lat"],
                    "longitude": loc["lng"],
                    "maps_link": _search_link(res["formatted_address"]),
                }
            logger.warning("Google geocoding returned %s", data.get("status"))

        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": "mapsagent/1.0"},
            timeout=TIMEOUT,
        )
        results = r.json()
        if results:
            top = results[0]
            return {
                "status": "success",
                "source": "openstreetmap",
                "formatted_address": top["display_name"],
                "latitude": float(top["lat"]),
                "longitude": float(top["lon"]),
                "maps_link": _search_link(top["display_name"]),
            }
        return {"status": "not_found", "message": f"No location found for '{address}'."}
    except Exception as e:  # tools must never raise into the agent loop
        logger.exception("geocode_address failed")
        return {"status": "error", "message": str(e)}


def verify_shelter_on_google_maps(name: str, address: str = "") -> dict:
    """Check whether a shelter/facility still exists and is operating.

    Args:
        name: Facility name (e.g. "Lincoln High School").
        address: Optional street address or city to narrow the search.

    Returns:
        A dict with verification status, business status and a Google Maps link.
    """
    query = f"{name} {address}".strip()
    key = _maps_key()
    if not key:
        return {
            "status": "unverified",
            "message": "No GOOGLE_MAPS_API_KEY configured, so live verification is unavailable.",
            "maps_link": _search_link(query),
        }
    try:
        r = requests.post(
            "https://places.googleapis.com/v1/places:searchText",
            headers={
                "X-Goog-Api-Key": key,
                "X-Goog-FieldMask": "places.displayName,places.formattedAddress,"
                "places.location,places.businessStatus,places.googleMapsUri",
            },
            json={"textQuery": query},
            timeout=TIMEOUT,
        )
        places = r.json().get("places", [])
        if not places:
            return {
                "status": "not_found",
                "message": "No matching place on Google Maps; it may be closed or renamed.",
                "maps_link": _search_link(query),
            }
        p = places[0]
        return {
            "status": "found",
            "name": p.get("displayName", {}).get("text"),
            "address": p.get("formattedAddress"),
            "business_status": p.get("businessStatus", "UNKNOWN"),
            "latitude": p.get("location", {}).get("latitude"),
            "longitude": p.get("location", {}).get("longitude"),
            "maps_link": p.get("googleMapsUri", _search_link(query)),
        }
    except Exception as e:
        logger.exception("verify_shelter_on_google_maps failed")
        return {"status": "error", "message": str(e), "maps_link": _search_link(query)}