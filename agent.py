import logging
import os

from google.adk.agents import Agent

from .config import DEFAULT_MODEL
from .tools.maps_tools import geocode_address, verify_shelter_on_google_maps

logger = logging.getLogger(__name__)

maps_tools = [geocode_address, verify_shelter_on_google_maps]

# The built-in Maps grounding tool cannot be mixed with function tools in one
# Gemini request, which makes every call fail. Opt in only if you remove the others.
if os.getenv("ENABLE_MAPS_GROUNDING", "").lower() == "true":
    from google.adk.tools import google_maps_grounding

    maps_tools = [google_maps_grounding]
    logger.info("Using ADK google_maps_grounding tool only.")

maps_instruction = """
You are the Maps & Geospatial Grounding Agent.

Your role is to handle location resolution, coordinate lookups (latitude and longitude), live Google Maps verification, and routing for emergency operations.

### YOUR CAPABILITIES:
1. Address & Zip Resolution: When a user or coordinator mentions an address or zip code, call geocode_address and report latitude and longitude.
2. Live Facility Verification: The emergency shelters database contains historical FEMA registrations. Call verify_shelter_on_google_maps to check whether the facility still exists, is open, or has been renamed/demolished.
3. Driving Directions & Deep Links: Generate Google Maps navigation URLs for safe routing, e.g. https://www.google.com/maps/dir/?api=1&origin=...&destination=...
4. Attribution: When displaying Google Maps information, retain 'Google Maps' unmodified with translate="no".

Always call a tool when the request involves a location, and always give the user a written answer after the tool returns.
"""

maps_agent = Agent(
    name="maps_agent",
    description="Resolves addresses to coordinates (lat/lon), verifies whether facilities still exist via Google Maps, and provides navigation links.",
    model=DEFAULT_MODEL,
    instruction=maps_instruction,
    tools=maps_tools,
)

root_agent = maps_agent