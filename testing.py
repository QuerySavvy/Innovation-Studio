import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image, ImageOps
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# initialize the client
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="uFsY2MHzUdNWrdNGsjcl"
)

# Function to perform inference on uploaded image
def rubbish_detector(image_file):
    with st.spinner('Performing image classification...'):
        # Perform inference
        result = CLIENT.infer(image_file, model_id="rubpred/4")

    # Extract the item and confidence
    object = result["top"]
    confidence = result["confidence"]

    # Display the result
    st.header("Detected objects:")
    st.subheader("Summary result:")
    st.write("Item Detected: ",object)
    st.write("Confidence: ", confidence)

    st.subheader("Full result:")
    st.write(result)

@st.cache_data
def loadlocationdata():
# Load suburb data
    file = "https://raw.githubusercontent.com/matthewproctor/australianpostcodes/master/australian_postcodes.csv"
    data = pd.read_csv(file, usecols=[2, 3, 14, 15, 35])
    data = data[data['state'] == "NSW"]
    data = data.drop_duplicates('locality')
    suburbs = data['locality'].to_list()
    suburbs.sort()
    return suburbs

def geolocate():
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
    #st.write("Coordinates:", (geo_location.latitude, geo_location.longitude))
    # Display map
    return st_folium(map, height=400)


# ----------------     Streamlit app     ----------------
st.title("The Desktop Prototype")
st.header("Image Upload Section")

# Allow user to upload an image
uploaded_image = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

# Perform inference if an image is uploaded
if uploaded_image is not None:
    # Display the uploaded image
    image = Image.open(uploaded_image)
    st.image(image, width=250, caption="Uploaded Image")

# Load location data
suburbs = loadlocationdata()

# Allow user to select their location
selected_suburb = st.selectbox("Suburb", suburbs, index=None, placeholder="Select a Suburb ...",)
selected_street = st.text_input("Street Name")
selected_number = st.text_input("Street Number")

if selected_suburb is not None and selected_suburb != "":
    geolocate()

# Button to trigger inference
if st.button("Detect Rubbish"):
    # Perform inference
    rubbish_detector(image)
