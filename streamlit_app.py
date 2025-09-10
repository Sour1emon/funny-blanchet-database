import streamlit as st
import json
import pandas as pd
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# -------------------------------
# Config
# -------------------------------
INPUT_FILE = "directory.json"
OUTPUT_FILE = "directory_with_coords.json"

# -------------------------------
# Load JSON
# -------------------------------
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

st.title("📖 Student Directory with Map (Geocoded)")

# -------------------------------
# Convert JSON → DataFrame
# -------------------------------
rows = []
for student in data:
    row = {
        "Name": student.get("name"),
        "Grade": student.get("grade"),
        "Email": student.get("email"),
    }
    if student["households"]:
        row["Address"] = student["households"][0].get("address")
        row["Phones"] = ", ".join(student["households"][0].get("phones", []))
    rows.append(row)

df = pd.DataFrame(rows)

# -------------------------------
# Load previously geocoded results (if any)
# -------------------------------
if Path(OUTPUT_FILE).exists():
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        geocoded_cache = json.load(f)
else:
    geocoded_cache = {}

# -------------------------------
# Geocode missing addresses
# -------------------------------
geolocator = Nominatim(user_agent="student-directory")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)  # respect limits

new_geocoded = False
progress = st.progress(0)
addresses = df["Address"].dropna().unique()

for i, addr in enumerate(addresses, 1):
    if addr not in geocoded_cache:
        try:
            location = geocode(addr)
            if location:
                geocoded_cache[addr] = {"lat": location.latitude, "lon": location.longitude}
            else:
                geocoded_cache[addr] = {"lat": None, "lon": None}
        except Exception:
            geocoded_cache[addr] = {"lat": None, "lon": None}
        new_geocoded = True
    progress.progress(i / len(addresses))

# Save updated geocoded results
if new_geocoded:
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(geocoded_cache, f, indent=2)

# -------------------------------
# Add lat/lon to DataFrame
# -------------------------------
df["lat"] = df["Address"].map(lambda a: geocoded_cache.get(a, {}).get("lat"))
df["lon"] = df["Address"].map(lambda a: geocoded_cache.get(a, {}).get("lon"))

# -------------------------------
# Search & Filter
# -------------------------------
st.subheader("🔍 Search Students")

search_term = st.text_input("Search by name, email, or grade").lower()

if search_term:
    filtered_df = df[
        df.apply(
            lambda row: search_term in str(row["Name"]).lower()
            or search_term in str(row["Email"]).lower()
            or search_term in str(row["Grade"]).lower(),
            axis=1,
        )
    ]
else:
    filtered_df = df

# -------------------------------
# Map view (filtered)
# -------------------------------
st.subheader("🗺️ Student Households Map")
map_data = filtered_df.dropna(subset=["lat", "lon"])[["lat", "lon"]]
if not map_data.empty:
    st.map(map_data)
else:
    st.info("No geocoded addresses to display for current filter.")

# -------------------------------
# Table view (filtered)
# -------------------------------
st.subheader("📋 Student List")
st.dataframe(filtered_df.drop(columns=["lat", "lon"]), use_container_width=True)
