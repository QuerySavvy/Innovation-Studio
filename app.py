import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# Title of the application
st.title("The Desktop Prototype")

# File upload section
st.header("Image Upload Section")
uploaded_images = st.file_uploader("Upload Image(s)", accept_multiple_files=True)
for uploaded_image in uploaded_images:
    image = uploaded_image.read()
    st.image(image, width=250, clamp=True)

# Geolocation Section
st.header("Geolocation Section")

# Load suburb data
file = "https://raw.githubusercontent.com/matthewproctor/australianpostcodes/master/australian_postcodes.csv"
data = pd.read_csv(file, usecols=[2, 3, 14, 15, 35])
data = data[data['state'] == "NSW"]
data = data.drop_duplicates('locality')

# Select suburb
suburbs = data['locality'].to_list()
suburbs.sort()
selected_suburb = st.selectbox("Suburb", suburbs, index=None, placeholder="Select a Suburb ...",)
if selected_suburb is None:
    st.stop()

# Get latitude and longitude of selected suburb
latitude = data.loc[data['locality'] == selected_suburb, "Lat_precise"].values[0]
longitude = data.loc[data['locality'] == selected_suburb, "Long_precise"].values[0]

selected_street = st.text_input("Street Name")
selected_number = st.text_input("Street Number")

# Get location info using geopy
geolocator = Nominatim(user_agent="UTS_APP")

if selected_street is not None and selected_street != "":
    if selected_number is not None and selected_number != "":
        geo_location = geolocator.geocode(selected_number +" "+selected_street +" "+ selected_suburb+" "+"NSW, Australia")
        coordinates = (geo_location.latitude, geo_location.longitude)
        map = folium.Map(location=coordinates, zoom_start=17)
        folium.Marker([geo_location.latitude, geo_location.longitude]).add_to(map)
    else:
        geo_location = geolocator.geocode(selected_street +" "+ selected_suburb+" "+"NSW, Australia")
        coordinates = (geo_location.latitude, geo_location.longitude)
        map = folium.Map(location=coordinates, zoom_start=17)
        folium.Marker([geo_location.latitude, geo_location.longitude]).add_to(map)
else:
    geo_location = geolocator.geocode(selected_suburb+" "+", NSW, Australia")
    coordinates = (geo_location.latitude, geo_location.longitude)
    map = folium.Map(location=coordinates, zoom_start=14)

# Display location address and coordinates
address = geo_location.address

if not address[0].isdigit() and selected_number!= "":
    address = selected_number + ", " + address
    st.warning('Unable to find exact location on map', icon="⚠️")

st.write("Address:", address)
st.write("Coordinates:", (geo_location.latitude, geo_location.longitude))

# Display map
st_folium(map, height=400)
