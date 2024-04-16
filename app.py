import streamlit as st
from geopy.geocoders import Nominatim
import cv2
import numpy as np
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Title of the application
st.title("The desktop prototype")

# File upload section
st.header("Image upload section")
uploaded_image = st.file_uploader("", accept_multiple_files=True)
for uploaded_image in uploaded_image:
    image = uploaded_image.read()
    st.image(image, width=250, clamp = True)




st.header("Geolocation Section")

file = "https://raw.githubusercontent.com/matthewproctor/australianpostcodes/master/australian_postcodes.csv"



data = pd.read_csv(file, usecols=[2,3,14,15,35])
data = data[data['state'] =="NSW"]
data = data.drop_duplicates('locality')


suburbs = data['locality'].to_list()
suburbs.sort()

selected_suburb = st.selectbox("Suburb select", suburbs, index=None, placeholder="Select a Suburb ...",)
if selected_suburb is None:
    st.stop()


latitude = data["Lat_precise"][data["locality"]==selected_suburb].values[0]
longitude = data["Long_precise"][data["locality"]==selected_suburb].values[0]
st.write(latitude)
st.write(longitude)


coordinates = (latitude,longitude)

map = folium.Map(location=coordinates, zoom_start=15)

st.header("Geo Map")

st_folium(map,width = 700)
