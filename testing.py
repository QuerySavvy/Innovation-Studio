import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image, ImageOps
import pandas as pd
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from streamlit_js_eval import get_geolocation

# initialize the client
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key=st.secrets['api_key']
)

#testing title
st.title("*** ***TESTING PAGE*** ***")

# --------------------------------     Copy/Paste code below this line     --------------------------------


# Function to perform inference on uploaded image
def rubbish_detector(image_file):
    with st.spinner('Please wait for image classification . . . .'):
        # Perform inference
        result = CLIENT.infer(image_file, model_id="rubpred/4")

    # Extract the item and confidence
    detected_object = result["top"]
    confidence = format(result["confidence"],".2%")
    return detected_object, confidence

@st.cache_data
def loadlocationdata():
# Load suburb data
    file = "https://raw.githubusercontent.com/matthewproctor/australianpostcodes/master/australian_postcodes.csv"
    data = pd.read_csv(file, usecols=[2, 3, 14, 15, 35])
    data = data[data['state'] == "NSW"]
    data = data.drop_duplicates('locality')
    suburbs = data['locality'].to_list()
    suburbs = [suburb.title() for suburb in suburbs]
    suburbs.sort()
    return suburbs

def geolocate():
    # Get location info using geopy
    geolocator = Nominatim(user_agent="UTS_APP")
    if selected_street is not None and selected_street != "":
        if selected_number is not None and selected_number != "":
            geo_location = geolocator.geocode(selected_number +" "+selected_street +" "+ selected_suburb+", "+ state +", "+country,addressdetails=True)
            coordinates = (geo_location.latitude, geo_location.longitude)
            map = folium.Map(location=coordinates, zoom_start=17)
            folium.Marker([geo_location.latitude, geo_location.longitude]).add_to(map)
        else:
            geo_location = geolocator.geocode(selected_street +" "+ selected_suburb+", "+ state +", "+country,addressdetails=True)
            coordinates = (geo_location.latitude, geo_location.longitude)
            map = folium.Map(location=coordinates, zoom_start=17)
            folium.Marker([geo_location.latitude, geo_location.longitude]).add_to(map)
    else:
        geo_location = geolocator.geocode(selected_suburb+", "+ state +", "+country,addressdetails=True)
        coordinates = (geo_location.latitude, geo_location.longitude)
        map = folium.Map(location=coordinates, zoom_start=14)
    
    # Display location address and coordinates
    address = geo_location.address
    if "house_number" not in geo_location.raw['address']:
        address = selected_number + ", " + address
        st.warning('Unable to find exact location on map', icon="⚠️")
    st.write("Full Address:", address)
    
    #used for testing
    #st.write(geo_location.raw['address'])

    # Display map
    return st_folium(map, height=400)

def locate_me():
    latitude = loc['coords']['latitude']
    longitude = loc['coords']['longitude']
    coordinates = (latitude, longitude)

    geolocator = Nominatim(user_agent="UTS_APP")
    location = geolocator.reverse(coordinates)
    address_raw = location.raw['address']
    
    #used for testing
    #st.write(location.raw)

    country = address_raw['country']
    state = address_raw['state']
    city = address_raw['city']
    road = address_raw['road']
    
    return country, state, city, road


# --------------------------------     Streamlit app     --------------------------------
st.title("Curbside rubbish reporting app")
#Run the geolocation
loc = get_geolocation()

#photo subheader
st.subheader("Please take a photo or upload an image")

# Define a SessionState object
session_state = st.session_state

if 'image uploaded' not in session_state:
    session_state['image uploaded'] = None

# Allow user to upload an image
uploaded_image = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])
if uploaded_image is not None:
    # Display the uploaded image
    image = Image.open(uploaded_image)
    image = ImageOps.exif_transpose(image)
    st.image(image, width=250, caption="Uploaded Image")
    
# Define a SessionState object
session_state = st.session_state

# Perform inference if an image is uploaded and the function has not been run yet or if a new image is uploaded
if uploaded_image is not None and session_state['image uploaded'] !=  uploaded_image.name:
    # Run the rubbish_detector function
    detected_object, confidence = rubbish_detector(image)
    session_state['detected_object'] = detected_object
    session_state['confidence'] = confidence
    session_state['image uploaded'] = uploaded_image.name

# Load location data
suburbs = loadlocationdata()

# Allow user to select their location
#if 'detected_object' in session_state:

#Initiliaise values
country = ""
state = ""
city = ""
road = ""

with st.container(border=True):
    st.subheader("Please enter the rubbish location ")

    if st.button(":round_pushpin: Locate Me "):
        session_state['locate_me'] = True

    if 'locate_me' in session_state:
        if session_state['locate_me'] == True:
            try:
                country, state, city, suburb, road = locate_me()
                suburbs.insert(0, city)
                selected_suburb = st.selectbox("Suburb",suburbs, index=0, placeholder="Select a Suburb . . .",)
            except:
                st.warning('Geolocation service currently unavailable', icon="⚠️")
    
    else:
        selected_suburb = st.selectbox("Suburb",suburbs, index=0, placeholder="Select a Suburb . . .",)
        country = ""
        state = ""
        city = ""
        road = ""

    col1, col2 = st.columns(2)
    selected_street = col1.text_input("Street Name", value=road,placeholder="Enter a Street Name . . .   e.g. Smith Street")
    selected_number = col2.text_input("Street Number",placeholder="Enter your street number")


    if selected_street is not None and selected_street != "":
        geolocate()


# Display inference results if available
if 'detected_object' in session_state:
    with st.container(border=True):
        string = f"Image matched with {session_state['confidence']} confidence."
        st.info(string, icon="ℹ️")
        st.write("The photo submitted looks like a ", session_state['detected_object'], " is that right?")
        col_1, col_2 = st.columns([.1,1])
        button_yes = col_1.button("Yes")
        button_no = col_2.button("No")
        if button_yes:
            st.balloons()
        if button_no:
            st.snow()
# --------------------------------     Streamlit app - end     --------------------------------

# ------------------------------------------------------------------------------------------------   New feature testing

if st.button("TEST ME"):
    latitude = loc['coords']['latitude']
    longitude = loc['coords']['longitude']
    coordinates = (latitude, longitude)

    geolocator = Nominatim(user_agent="UTS_APP")
    location = geolocator.reverse(coordinates)
    address_raw = location.raw['address']
    
    #used for testing
    st.write(location.raw)
    
#Testing only
with st.container(border=True):
    st.subheader("Backend Code information")
    session_state



# ------------------------------------------------------------------------------------------------   New feature testing


