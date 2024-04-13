import streamlit as st
from geopy.geocoders import Nominatim
import geocoder
import cv2
import numpy as np
import streamlit as st

# Title of the application
st.title("The desktop prototype")

# File upload section

st.header("Image upload section")
uploaded_image = st.file_uploader("", accept_multiple_files=True)
for uploaded_image in uploaded_image:
    image = uploaded_image.read()
    st.image(image, width=250, clamp = True)

# Getting user's location using IP address
g = geocoder.ip('me')
location = g.latlng

# Displaying user's location
#st.write(location)

# Extracting latitude and longitude
lat = location[0]
lng = location[1]


st.header("Geolocation Section")
# Reverse geocoding to get user's address
geolocator = Nominatim(user_agent="rubbish-app")
location = geolocator.reverse((lat, lng))

# Displaying user's address
st.write(f"**Your address is:** {location.address}")

# Splitting address into components
my_string = location.address
my_list = my_string.split(",")

try:
    country = my_list[-1]
except IndexError:
    country = None

try:
    postcode = my_list[-2]
except IndexError:
    postcode = None

try:
    other1 = my_list[-3]
except IndexError:
    other1 = None

try:
    other2 = my_list[-4]
except IndexError:
    other2 = None

try:
    other3 = my_list[-5]
except IndexError:
    other3 = None

try:
    other4 = my_list[-6]
except IndexError:
    other4 = None

try:
    other5 = my_list[-7]
except IndexError:
    other5 = None

try:
    other6 = my_list[-8]
except IndexError:
    other6 = None


# Displaying address components
st.write(f"**Country:** {country}")
st.write(f"**Postcode:** {postcode}")
st.write(f"**Other1:** {other1}")
st.write(f"**Other2:** {other2}")
st.write(f"**Other3:** {other3}")
st.write(f"**Other4:** {other4}")
st.write(f"**Other5:** {other5}")
st.write(f"**Other6:** {other6}")


