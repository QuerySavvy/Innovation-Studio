import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image, ImageOps
import pandas as pd
import folium
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation
from datetime import date
import requests
from io import BytesIO
import gspread
from google.oauth2.service_account import Credentials

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

def thank_you_page():
    url = 'https://github.com/QuerySavvy/Innovation-Studio/blob/main/pngtree-goldan-3d-star-emoji-icon-png-image_10459560.png?raw=true'

    response = requests.get(url)
    image = Image.open(BytesIO(response.content))

    with st.container(border=True):
        congrats_col1, congrats_col2, congrats_col3 = st.columns([2,6,2])
        with congrats_col2:
            st.header("Congrations !")
            st.image(image)
            st.subheader("You earned 10 points")


def initialise_sheets():
    with st.spinner('loading . . . .'):
        credentials_dict = {
            "type": "service_account",
            "project_id": "innovationstudio",
            "private_key_id": "877c2f8e58421fd470a9b0be4bf6617a39318277",
            "private_key": st.secrets['google_api_key'],
            "client_email": "innovation-studio@innovationstudio.iam.gserviceaccount.com",
            "client_id": "103602022291355277889",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/innovation-studio@innovationstudio.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }

        # Create credentials using the dictionary
        credentials = Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        )

        # Authorize and initialize the gspread client
        client = gspread.authorize(credentials)

        # Open the Google Sheet by its name
        workbook = client.open("Sydney_log")
        data = workbook.get_worksheet(0)  # First sheet
        users = workbook.get_worksheet(1)  # Second sheet

    # Find the first blank row in the sheet
    data_next_row = len(data.col_values(1)) + 1
    users_next_row = len(users.col_values(1)) + 1
    return data, users, data_next_row, users_next_row

def send_sheets_data(data, data_next_row, Address, Latitude, Longitude, type_of_rubbish, user_IP, image_location):
    #create the data frame
    data_df = pd.DataFrame({
    'Column1': [Address],
    'Column2': [Latitude],
    'Column3': [Longitude],
    'Column4': [type_of_rubbish],
    'Column5': [user_IP],
    'Column6': [str(date.today())],
    'Column7': ['Null']
    })

    # Find the first blank row in the sheet
    next_row = len(data.col_values(1)) + 1

    # Insert data into the first blank row without headers
    data.insert_row(data_df.values[0].tolist(), next_row)


# ----------------------------------------------------------------     Streamlit app     ----------------------------------------------------------------
st.title("Curbside rubbish reporting app")

# Define a SessionState object
session_state = st.session_state

# Initialise the session state variables before the user uploads an image
if 'image uploaded' not in session_state:
    session_state['image uploaded'] = None
    session_state['classification'] = None
    session_state['object'] = None
    session_state['address'] = None
    session_state['form'] = None

#Run the geolocation engine
loc = None
loc = get_geolocation()

with st.expander('Click to find out more'):
        st.write("bla bla bla bla. do we wanna add some bla bla here?")

#Create the container for the image section 
with st.container(border=True):

    #Photo subheader
    st.subheader("Please take a photo or or upload an image to start")

    # Allow user to upload an image type=["jpg", "jpeg"]
    uploaded_image = st.file_uploader("Choose an image...", type=["jpg", "jpeg"])
    if uploaded_image is not None:
        # Display the uploaded image
        image = Image.open(uploaded_image)
        image = ImageOps.exif_transpose(image)
        st.write(image)

    # Perform inference if an image is uploaded and the function has not been run yet or if a new image is uploaded
    if uploaded_image is not None and session_state['image uploaded'] !=  uploaded_image.name + str(uploaded_image.size):
        # Run the rubbish_detector function
        detected_object, confidence = rubbish_detector(image)
        session_state['detected_object'] = detected_object
        session_state['confidence'] = confidence
        session_state['image uploaded'] = uploaded_image.name + str(uploaded_image.size)

    # Display inference results if available
    if 'detected_object' in session_state:
        string = f"Image matched with {session_state['confidence']} confidence."
        st.info(string, icon="ℹ️")
        st.write("The photo submitted looks like a ", session_state['detected_object'], " is that right?")
        col_1, col_2 = st.columns([.1,1])
        button_yes = col_1.button("Yes")
        button_no = col_2.button("No")
        if button_yes:
            session_state['classification'] = True
            st.balloons()
        if button_no:
            session_state['classification'] = False
        
        if session_state['classification'] == True:
            session_state['object'] = session_state['detected_object']
            st.success("⬇️ Enter location information ⬇️")

        if session_state['classification'] == False:
            junk = st.radio(
            "What is it ?",
            ['mattress', 'milk crate', 'bicycle', 'couch', 'construction waste', 'car', 'rubbish', 'tyres', 'shopping trolley', 'fridge'],
            index=None,)
            session_state['object'] = junk
            if not junk == None:
                st.write("You selected:", junk) 
                st.success("⬇️ Enter location information ⬇️")


# Load location data
suburbs = loadlocationdata()

# Create container for location section
if not session_state['object'] == None:
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
            session_state['address'] = selected_number + ', ' + selected_street + ', ' + selected_suburb
            session_state['form'] = 'ready'

# the form to submit the information
if session_state['form'] == 'ready':
    with st.container(border=True):
        st.subheader("Submit your report")
        with st.container(border=True):
            st.text("Rubish type: " + session_state['object'] + "\n"
                    "Address: " + session_state['address'] + "\n"
                    "Report Date: " + str(date.today()))
        if st.button('Submit to '+selected_suburb + ' council 📨'):
            session_state['form'] = 'submitted'
            st.text("Thank you for your submission")

if session_state['form'] == 'submitted':
    st.balloons()
    with st.spinner('Loading. . . .'):
        data, users, data_next_row, users_next_row = initialise_sheets()
        send_sheets_data(data, data_next_row, session_state['address'], session_state['latitude'], session_state['longitude'], session_state['object'], "tbc", "tbc")
    thank_you_page()


# --------------------------------     Streamlit app - end     --------------------------------


# ------------------------------------------------------------------------------------------------   New feature testing

#Testing only

st.title("*** ***BELOW FOR TESTING ONLY*** ***")
with st.container(border=True):
    st.subheader("Backend Code information")

    st.info('Address Information')
    if loc is not None:
        latitude = loc['coords']['latitude']
        longitude = loc['coords']['longitude']
        coordinates = (latitude, longitude)

        geolocator = Nominatim(user_agent="UTS_APP")
        location = geolocator.reverse(coordinates)
        address_raw = location.raw['address']
    #used for testing
        st.write(address_raw)

    st.info('Session State Information')
    session_state

# ------------------------------------------------------------------------------------------------   New feature testing
