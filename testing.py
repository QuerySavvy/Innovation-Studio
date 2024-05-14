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


def geolocate(country, state, city, road, number):
    try:
    # Get location info using geopy
        geolocator = Nominatim(user_agent="UTS_APP")

        #check to see if locate_me function is being used
        if 'locate_me' not in session_state:
            state = "NSW"
            country = "Australia"

        if selected_number:
            geo_location = geolocator.geocode(selected_number +" "+selected_street +" "+ selected_suburb+", "+ state +", "+country,addressdetails=True)
            coordinates = (geo_location.latitude, geo_location.longitude)
            map = folium.Map(location=coordinates, zoom_start=17)
            folium.Marker([geo_location.latitude, geo_location.longitude]).add_to(map)

        # Display location address and coordinates
        address = geo_location.address
        if "house_number" not in geo_location.raw['address']:
            address = selected_number + ", " + address
            st.info('Unable to find exact location on map. Your address has been saved.', icon="⚠️")
        st.write("Full Address:", address)
            
            # Display map
        return st_folium(map, height=400)
    except Exception as e:
        st.error(f"Map currently unavailable. Please double check the address. \n\nError Message: {e}")

# Geolocation function
def locate_me():
    latitude = loc['coords']['latitude']
    longitude = loc['coords']['longitude']
    coordinates = (latitude, longitude)
    geolocator = Nominatim(user_agent="UTS_APP")
    location = geolocator.reverse(coordinates)
    address_raw = location.raw['address']

    country = address_raw['country']
    state = address_raw['state']
    road = address_raw['road']

    # Define a list of potential fields for the city or suburb field
    city_field = ['city', 'suburb', 'town', 'village']

    # Iterate over the potential field names and retrieve the value if it exists
    city = None
    for key in city_field:
        if key in address_raw:
            city = address_raw[key]
            break
    number = None
    if 'house_number' in address_raw:
        number = address_raw['house_number']
    
    return country, state, city, road, number

# ----------------------------------------------------------------     Streamlit app     ----------------------------------------------------------------
st.title("Curbside rubbish reporting app")

# Define a SessionState object
session_state = st.session_state

#Run the geolocation engine
loc = None
loc = get_geolocation()

#Photo subheader
st.subheader("Please take a photo or upload an image")

# Define a SessionState object
session_state = st.session_state
if 'image uploaded' not in session_state:
    session_state['image uploaded'] = None

# Allow user to upload an image type=["jpg", "jpeg"]
uploaded_image = st.file_uploader("Choose an image...", type=["jpg", "jpeg"])
if uploaded_image is not None:
    # Display the uploaded image
    image = Image.open(uploaded_image)
    image = ImageOps.exif_transpose(image)

# Perform inference if an image is uploaded and the function has not been run yet or if a new image is uploaded
if uploaded_image is not None and session_state['image uploaded'] !=  uploaded_image.name + str(uploaded_image.size):
    # Run the rubbish_detector function
    detected_object, confidence = rubbish_detector(image)
    session_state['detected_object'] = detected_object
    session_state['confidence'] = confidence
    session_state['image uploaded'] = uploaded_image.name + str(uploaded_image.size)

# Load location data
suburbs = loadlocationdata()

# Allow user to select their location
with st.container(border=True):
    st.subheader("Please enter the rubbish location ")

    if st.button(":round_pushpin: Locate Me "):
        session_state['locate_me'] = True

    if 'locate_me' in session_state:
        try:
            country, state, city, road, number = locate_me()
            suburbs.insert(0, city)
        except:
            st.warning('Geolocation service currently unavailable', icon="⚠️")
    else:
        country = "Australia"
        state = "NSW"

    selected_suburb = st.selectbox("Suburb", suburbs, index=0 if 'locate_me' in session_state else None, placeholder="Select a Suburb . . .",)
    col1, col2 = st.columns(2)
    selected_street = col1.text_input("Street Name", value=road if 'locate_me' in session_state else "", placeholder="Enter a Street Name . . .   e.g. Smith Street")
    selected_number = col2.text_input("Street Number", value=number if 'locate_me' in session_state else "",placeholder="Enter your street number")

    if selected_suburb and (not selected_street or not selected_number):
        st.warning("Please enter a value in every field.")

    if selected_suburb and selected_street and selected_number:
        geolocate(country, state, selected_suburb, selected_street, selected_number)

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
# ----------------------------------------------------------------     Streamlit app - end     --------------------------------

# ------------------------------------------------------------------------------------------------     testing

#Testing only
with st.container(border=True):
    st.subheader("Backend Code information")

    st.info('Address Information')
    if loc is not None:
        try:
            latitude = loc['coords']['latitude']
            longitude = loc['coords']['longitude']
            coordinates = (latitude, longitude)
    
            geolocator = Nominatim(user_agent="UTS_APP")
            location = geolocator.reverse(coordinates)
            address_raw = location.raw['address']
        except:
            st.warning('location services unavailable on your device')
    #used for testing
        st.write(address_raw)

    st.info('Session State Information')
    session_state

# ------------------------------------------------------------------------------------------------     testing

