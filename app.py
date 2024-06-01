import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image, ImageOps
import pandas as pd
import folium
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
from streamlit_js_eval import get_geolocation, streamlit_js_eval
from datetime import date
import requests
from io import BytesIO
import gspread
from google.oauth2.service_account import Credentials
import time
# initialize the roboflow client
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key=st.secrets['api_key']
)
# initialize the googlesheets dictionary
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

# --------------------------------     Copy/Paste code below this line     --------------------------------

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

def get_nominatim_coordinates(country, state, city, road, number):
    try:
    # Get location info using geopy
        geolocator = Nominatim(user_agent="UTS_APP")
        #check to see if locate_me function is being used
        if 'locate_me' not in session_state:
            state = "NSW"
            country = "Australia"
        if selected_number:
            geo_location = geolocator.geocode(selected_number +" "+selected_street +" "+ selected_suburb+", "+ state +", "+country,addressdetails=True)
            nominatim_coordinates = (geo_location.latitude, geo_location.longitude)
            nominatim_lat = geo_location.latitude
            nominatim_long = geo_location.longitude
            session_state['latitude'] = geo_location.latitude
            session_state['longitude'] = geo_location.longitude
            address = geo_location.address
            if "house_number" not in geo_location.raw['address']:
                address = selected_number + ", " + address
                st.info('Unable to find exact location on our server, however your address details have been saved.', icon="⚠️")
            st.write("Full Address:", address)
        return nominatim_lat, nominatim_long, nominatim_coordinates
    except Exception as e:
        st.error(f"error with the generate_coordinates function \n\nError Message: {e}")     
def generate_map(lat,long):
    try:
        map = folium.Map(location=(lat,long), zoom_start=17)
        folium.Marker([lat,long]).add_to(map)       
        # Display map
        return st_folium(map, height=300)
    except Exception as e:
        session_state['latitude'] = None
        session_state['longitude'] = None
        st.error(f"Map currently unavailable. \n\nError Message: {e}")
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
    newpoints = session_state['user_points'] + 10
    with st.container(border=True):
        st.header("Congrations " + session_state['user_name'] + "!")
        st.subheader("You now have a total of "+ str(newpoints)+" points")
        with st.popover("See rewards"):
            display_my_rewards(newpoints)
        congrats_col1, congrats_col2, congrats_col3 = st.columns([3,4,3])
        with congrats_col2:
            st.image(image)
            st.subheader("You earned 10 points\n\n")   
    
    return newpoints
    #Need to add function to write the points to the user account
def please_sign_up():
    with st.container(border=True):
        st.header("Don't forget to sign up next time")
        st.subheader("Collect points and claim local dicount vouchers 🤑 ")
def login(username, password, worksheet):
    with st.spinner('Authenticating . . . .'):
        # Filter data for the given username
        records = worksheet.get_all_records()
        user_data = None
        row_number = None
        for index, record in enumerate(records):
            if record['user_name'] == username:
                user_data = record
                row_number = index + 2  # +2 to account for header row and zero-based index
                break
        if user_data:
            if user_data['user_password'] == password:
                session_state['user_login_status'] = "Logged In"
                session_state['user_name'] = username
                session_state['user_row_number'] = row_number
                session_state['user_points'] = user_data['user_points']
                st.success("Authenticated")
                st.write("✨ Welcome "+username+" ✨")
                st.write("You currently have "+ str(user_data['user_points']) +" points.")
                time.sleep(5)
                st.rerun()
            else:
                st.warning("Incorrect password")
        else:
            st.warning("Username not found")
def initialise_sheets():
    with st.spinner('Connecting to database . . . .'):
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
    return data, users
def create_user(username, password, users):
    if username not in users.col_values(2):
        next_row = len(users.col_values(1)) + 1
        userid = "User"+str(next_row-1)
        users.insert_row([userid,username,password,0],next_row)
        st.success("User Created")
        time.sleep(0.5)
        session_state['user_login_status'] = "Logged In"
        session_state['user_name'] = username
        session_state['user_row_number'] = next_row
        session_state['user_points'] = 0
        st.write("✨ Welcome "+username+" ✨")
        time.sleep(1)
        st.rerun()
    else:
        st.warning("username already exists")
def send_sheets_data(data, Address, Latitude, Longitude, type_of_rubbish, user_name):
    #create the data frame
    data_df = pd.DataFrame({
    'Column1': [Address],
    'Column2': [Latitude],
    'Column3': [Longitude],
    'Column4': [type_of_rubbish],
    'Column5': [user_name],
    'Column6': [str(date.today())],
    'Column7': ['Null']
    })
    # Find the first blank row in the sheet
    next_row = len(data.col_values(1)) + 1
    # Insert data into the first blank row without headers
    data.insert_row(data_df.values[0].tolist(), next_row)
def update_user_points(user_row, new_points, user_table):
    # Update the user_points column for the specific user
    user_table.update_cell(user_row, 4, new_points)  # Assuming user_points is in the fourth column
    session_state['user_points'] = new_points
    st.success("User points updated")

def display_my_rewards(points):
    rewards_scale = {
    50: "$10 voucher for your local pub",
    100: "50% off movie tickets",
    200: "$25 restaurant gift card",
    300: "Free coffee for a week at a local café",
    500: "$50 shopping voucher",
    750: "Free monthly gym membership",
    1000: "$100 travel voucher",
    1500: "Free entry to a local event or concert",
    2000: "$200 tech gadget gift card"
    }

    eligible_reward_found = False

    for pts, reward in rewards_scale.items():
        if points >= pts:
            if not eligible_reward_found:
                st.subheader("🎉 You are eligible for:")
                eligible_reward_found = True
            st.write(f"{pts} pts = {reward}")

        elif points < pts:
            st.subheader("Your next reward is:")
            st.write(f"{pts} pts = {reward}")
            break
def display_leader_board(userdata):
    # Fetch all records from the users worksheet
    users_data = userdata.get_all_records()
    
    users_df = pd.DataFrame(users_data)
    users_df.drop(columns=["user_id","user_password","user_tbc"],inplace=True)

    users_sorted = users_df.sort_values(by='user_points',ascending=False).head()
    st.subheader("Leaderboard")
    st.dataframe(
        users_sorted,
        column_config={
            "user_name": "User Name",
            "user_points": st.column_config.NumberColumn(
                "User XP",
                format="%d ⭐"
            ),
        },
        hide_index=True,use_container_width=True
    )

    
    
def reload_page():
    streamlit_js_eval(js_expressions="parent.window.location.reload()")


# ----------------------------------------------------------------     Streamlit app     ----------------------------------------------------------------

url = 'https://github.com/QuerySavvy/Innovation-Studio/blob/main/bird_of_pred.jpg?raw=true'
response = requests.get(url)
image = Image.open(BytesIO(response.content))
st.image(image)

# Title with emojis
title = "📷 Spot & Send 📤"

# Center-aligned title with black text
st.markdown(f"<h1 style='text-align: center; color: black;'>{title}</h1>", unsafe_allow_html=True)


with st.expander("About Spot & Send"):
    st.write("Welcome to Spot & Send, we're on a mission to reduce illegal rubbish dumping.")
    st.write("1. 📸 Snap a photo of illegally dumped rubbish.")
    st.write("2. 🗑️ Confirm the rubbish type.")
    st.write("3. 📍 Confirm your location.")
    st.write("4. 📤 Send to earn points.")
    st.write("Thanks for your help, let's get started!")

# Define a SessionState object
session_state = st.session_state
#login screen
if 'user_login_status' not in session_state:
    with st.container(border=True):
        #Login Screen
        st.subheader("Welcome to our Curbside rubbish reporting app")
        st.write("How would you like to continue:")
        screen1_1, screen1_2, screen1_3 = st.columns(3)
        with screen1_1:
            with st.popover("Sign In"):
                username = st.text_input("Enter your username")
                password = st.text_input("Enter your password",type="password")
                login_button = st.button("Sign In")
                if login_button:
                    data, users = initialise_sheets()
                    login(username,password,users)
        with screen1_2:
            with st.popover("Create Account"):
                username = st.text_input("Enter a username")
                password = st.text_input("Enter a password",type="password")
                sign_up_button = st.button("Create Account")
                if(sign_up_button):
                    data, users = initialise_sheets()
                    create_user(username, password, users)
        with screen1_3:
            guest = st.button("Continue as guest")
        if guest:
            if "user_login_status" not in session_state:
                session_state['user_login_status'] = "guest"
                session_state['user_name'] = "Anonymous"
                st.rerun()
            elif session_state['user_login_status'] != "guest":
                session_state['user_login_status'] = "guest"
                session_state['user_name'] = "Anonymous"
                st.rerun()           
    st.stop()
# Initialise the session state variables before the user uploads an image
if 'image uploaded' not in session_state:
    session_state['image uploaded'] = None 
    session_state['classification'] = None
    session_state['object'] = None
    session_state['address'] = None
    session_state['form'] = None
    session_state['locate_me'] = None
    session_state['reset_page'] = None
    session_state['latitude'] = None
    session_state['longitude'] = None    

#Run the geolocation engine
loc = None
loc = get_geolocation()
time.sleep(0.5)
#Create the container for the image section 
with st.container(border=True):
    #Photo subheader
    st.subheader("Please take a photo or or upload an image")
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
        st.markdown(f"The photo submitted looks like a ***{session_state['detected_object']}***, is that right?")
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
        if session_state['locate_me'] == True:
            try:
                country, state, city, road, number = locate_me()
                suburbs.insert(0, city)
            except:
                st.warning('Geolocation service currently unavailable', icon="⚠️")
                session_state['locate_me'] = False
        if session_state['locate_me'] == False:
            country = "Australia"
            state = "NSW"
        selected_suburb = st.selectbox("Suburb", suburbs, index=0 if session_state['locate_me'] == True else None, placeholder="Select a Suburb . . .",)
        col1, col2 = st.columns(2)
        selected_street = col1.text_input("Street Name", value=road if session_state['locate_me'] == True else "", placeholder="Enter a Street Name . . .   e.g. Smith Street")
        selected_number = col2.text_input("Street Number", value=number if session_state['locate_me'] == True else "",placeholder="Enter your street number")
        if selected_suburb and (not selected_street or not selected_number):
            st.warning("Please enter a value in every field.")
        if selected_suburb and selected_street and selected_number:
            try:
                nominatim_lat, nominatim_long, nominatim_coordinates = get_nominatim_coordinates(country, state, selected_suburb, selected_street, selected_number)
                generate_map(nominatim_lat,nominatim_long)
            except:
                st.warning('get_nominatim_coordinates() and generate_map() currently unavailable', icon="⚠️")
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
    if session_state['user_login_status'] == "guest":
        with st.spinner("Loading . . . ."):
            data, users = initialise_sheets()
            send_sheets_data(data, session_state['address'], session_state['latitude'], session_state['longitude'], session_state['object'], session_state['user_name'])
            please_sign_up()
            session_state['form'] = 'submitted'
    else:
        data, users = initialise_sheets()
        newpoints = thank_you_page()
        with st.spinner("Updating user points. . . ."):
            send_sheets_data(data, session_state['address'], session_state['latitude'], session_state['longitude'], session_state['object'], session_state['user_name'])
            update_user_points(session_state['user_row_number'], newpoints, users)
            session_state['form'] = 'submitted'
        with st.container(border=True):
            data, users = initialise_sheets()
            display_leader_board(users)

    st.button("Submit another request", on_click=reload_page)
    
# --------------------------------     Streamlit app - end     --------------------------------
# ------------------------------------------------------------------------------------------------   New feature testing
#Testing only
with st.sidebar:
    with st.container(border=True):
        st.write("App Health Checks")
        try:
            if loc is not None:
                latitude = loc['coords']['latitude']
                longitude = loc['coords']['longitude']
                coordinates = (latitude, longitude)
                geolocator = Nominatim(user_agent="UTS_APP")
                location = geolocator.reverse(coordinates)
                address_raw = location.raw['address']
                st.success('Geolocation OK')
            else:
                st.error('Geolocation NOT OK')
        except Exception as e:
            st.error(f'Geolocation NOT OK {e}')
        try:
            data, users = initialise_sheets()
            st.success('Google API OK')
        except:
            st.error('Google API NOT OK')
