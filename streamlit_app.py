import streamlit as st
import json
import pandas as pd

# Load the JSON file
with open("directory.json", "r", encoding="utf-8") as f:
    data = json.load(f)

st.title("Student Directory Viewer")

# Sidebar filter
grades = sorted(set(entry.get("grade") for entry in data if entry.get("grade")))
selected_grade = st.sidebar.selectbox("Filter by Grade", ["All"] + grades)

# Build a dataframe for the table
rows = []
for student in data:
    if selected_grade != "All" and student.get("grade") != selected_grade:
        continue
    row = {
        "Name": student.get("name"),
        "Grade": student.get("grade"),
        "Email": student.get("email"),
        "Photo": student.get("photo")
    }
    # If there's at least one household, add address + phones
    if student["households"]:
        row["Address"] = student["households"][0].get("address")
        row["Phones"] = ", ".join(student["households"][0].get("phones", []))
    rows.append(row)

df = pd.DataFrame(rows)

# Show as table
st.subheader("Directory Table")
st.dataframe(df)

# Show student cards with photos
st.subheader("Student Profiles")
for _, row in df.iterrows():
    with st.container():
        cols = st.columns([1, 3])
        with cols[0]:
            if row["Photo"]:
                st.image(row["Photo"], width=100)
        with cols[1]:
            st.markdown(f"**{row['Name']}** (Grade {row['Grade']})")
            st.markdown(f"📧 {row['Email']}")
            if row.get("Address"):
                st.markdown(f"🏠 {row['Address']}")
            if row.get("Phones"):
                st.markdown(f"📞 {row['Phones']}")

# Optional: Map view if you have lat/lon data
# If you only have addresses, you'd need to geocode them (turn into lat/lon first).
