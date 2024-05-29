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
import time

# Initialize the RoboFlow client
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key=st.secrets['api_key']
)

# Initialize Google Sheets credentials
credentials_dict = st.secrets['google_credentials']

def initialize_session_state():
    if 'user_login_status' not in st.session_state:
        st.session_state['user_login_status'] = None
    if 'image_uploaded' not in st.session_state:
        st.session_state.update({
            'image_uploaded': None,
            'classification': None,
            'object': None,
            'address': None,
            'form': None,
            'locate_me': None,
            'latitude': None,
            'longitude': None,
            'detected_object': None,
            'confidence': None,
            'user_points': 0,
            'user_name': 'Anonymous'
        })

@st.cache_data
def load_location_data():
    url = "https://raw.githubusercontent.com/matthewproctor/australianpostcodes/master/australian_postcodes.csv"
    data = pd.read_csv(url, usecols=[2, 3, 14, 15, 35])
    data = data[data['state'] == "NSW"].drop_duplicates('locality')
    suburbs = sorted([suburb.title() for suburb in data['locality'].to_list()])
    return suburbs

def rubbish_detector(image_file):
    with st.spinner('Please wait for image classification...'):
        result = CLIENT.infer(image_file, model_id="rubpred/4")
    detected_object = result["top"]
    confidence = format(result["confidence"], ".2%")
    return detected_object, confidence

def get_coordinates_from_address(country, state, city, road, number):
    geolocator = Nominatim(user_agent="UTS_APP")
    location = geolocator.geocode(f"{number} {road}, {city}, {state}, {country}", addressdetails=True)
    if location:
        return location.latitude, location.longitude, location.address
    return None, None, None

def generate_map(lat, long):
    map_ = folium.Map(location=(lat, long), zoom_start=17)
    folium.Marker([lat, long]).add_to(map_)
    return st_folium(map_, height=300)

def locate_me():
    loc = get_geolocation()
    if loc:
        latitude, longitude = loc['coords']['latitude'], loc['coords']['longitude']
        geolocator = Nominatim(user_agent="UTS_APP")
        location = geolocator.reverse((latitude, longitude))
        address_raw = location.raw['address']
        country = address_raw.get('country')
        state = address_raw.get('state')
        road = address_raw.get('road')
        city = next((address_raw.get(key) for key in ['city', 'suburb', 'town', 'village'] if address_raw.get(key)), None)
        number = address_raw.get('house_number')
        return country, state, city, road, number
    return None, None, None, None, None

def display_thank_you_page(new_points):
    url = 'https://github.com/QuerySavvy/Innovation-Studio/blob/main/pngtree-goldan-3d-star-emoji-icon-png-image_10459560.png?raw=true'
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    with st.container():
        st.header(f"Congratulations {st.session_state['user_name']}!")
        st.subheader(f"You now have a total of {new_points} points")
        st.image(image)
        st.write("You earned 10 points")
    return new_points

def please_sign_up():
    with st.container():
        st.header("Don't forget to sign up next time")
        st.subheader("Collect points and claim local discount vouchers 🤑")

def authenticate_user(username, password, worksheet):
    records = worksheet.get_all_records()
    for record in records:
        if record['user_name'] == username:
            if record['user_password'] == password:
                st.session_state.update({
                    'user_login_status': "Logged In",
                    'user_name': username,
                    'user_points': record['user_points']
                })
                st.success("Authenticated")
                st.write(f"✨ Welcome {username} ✨")
                st.write(f"You currently have {record['user_points']} points.")
                time.sleep(2)
                st.experimental_rerun()
            else:
                st.warning("Incorrect password")
            return
    st.warning("Username not found")

def initialize_google_sheets():
    credentials = Credentials.from_service_account_info(
        credentials_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(credentials)
    workbook = client.open("Sydney_log")
    data = workbook.get_worksheet(0)
    users = workbook.get_worksheet(1)
    return data, users

def create_user(username, password, users):
    if username not in users.col_values(2):
        next_row = len(users.col_values(1)) + 1
        users.insert_row([f"User{next_row-1}", username, password, 0], next_row)
        st.success("User Created")
        st.session_state.update({
            'user_login_status': "Logged In",
            'user_name': username,
            'user_points': 0
        })
        st.write(f"✨ Welcome {username} ✨")
        st.experimental_rerun()
    else:
        st.warning("Username already exists")

def send_sheets_data(data, address, lat, long, rubbish_type, user_name):
    row_data = [address, lat, long, rubbish_type, user_name, str(date.today()), 'Null']
    next_row = len(data.col_values(1)) + 1
    data.insert_row(row_data, next_row)

def update_user_points(user_row, new_points, user_table):
    user_table.update_cell(user_row, 4, new_points)
    st.session_state['user_points'] = new_points
    st.success("User points updated")

def display_rewards(points):
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
        else:
            st.subheader("Your next reward is:")
            st.write(f"{pts} pts = {reward}")
            break

def main():
    st.title("Curbside Rubbish Reporting App")
    url = 'https://github.com/QuerySavvy/Innovation-Studio/blob/main/bird_of_pred.jpg?raw=true'
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    st.image(image)

    initialize_session_state()
    suburbs = load_location_data()

    if st.session_state['user_login_status'] is None:
        with st.container():
            st.subheader("Welcome to our Curbside rubbish reporting app")
            screen1_1, screen1_2, screen1_3 = st.columns(3)
            with screen1_1:
                username = st.text_input("Enter your username")
                password = st.text_input("Enter your password", type="password")
                if st.button("Sign In"):
                    data, users = initialize_google_sheets()
                    authenticate_user(username, password, users)
            with screen1_2:
                username = st.text_input("Enter a username", key="create_username")
                password = st.text_input("Enter a password", type="password", key="create_password")
                if st.button("Create Account"):
                    data, users = initialize_google_sheets()
                    create_user(username, password, users)
            if st.button("Continue as Guest"):
                st.session_state.update({
                    'user_login_status': "guest",
                    'user_name': "Anonymous"
                })
                st.experimental_rerun()
    else:
        uploaded_image = st.file_uploader("Upload an image of the rubbish", type=["jpg", "jpeg", "png"])
        if uploaded_image:
            st.session_state['image_uploaded'] = Image.open(uploaded_image)
            st.image(st.session_state['image_uploaded'])
            if st.button("Classify Image"):
                detected_object, confidence = rubbish_detector(uploaded_image)
                st.session_state.update({
                    'detected_object': detected_object,
                    'confidence': confidence
                })
                st.success(f"Detected Object: {detected_object}")
                st.write(f"Confidence Level: {confidence}")
        
        with st.form("report_form"):
            form_cols = st.columns(2)
            with form_cols[0]:
                country = st.selectbox("Country", ["Australia"])
                state = st.selectbox("State", ["NSW"])
                city = st.selectbox("Suburb", suburbs)
                road = st.text_input("Road Name")
                number = st.text_input("House Number")
            with form_cols[1]:
                if st.button("Locate Me"):
                    country, state, city, road, number = locate_me()
                    st.write(f"Detected Location: {number} {road}, {city}, {state}, {country}")
            submit_button = st.form_submit_button("Submit Report")
            
            if submit_button:
                lat, long, address = get_coordinates_from_address(country, state, city, road, number)
                if lat and long:
                    send_sheets_data(data, address, lat, long, st.session_state['detected_object'], st.session_state['user_name'])
                    if st.session_state['user_login_status'] != "guest":
                        user_row = next(i+1 for i, row in enumerate(users.get_all_records()) if row['user_name'] == st.session_state['user_name'])
                        new_points = st.session_state['user_points'] + 10
                        update_user_points(user_row, new_points, users)
                        display_thank_you_page(new_points)
                    else:
                        please_sign_up()
                    generate_map(lat, long)
                else:
                    st.error("Failed to retrieve coordinates. Please check the address details.")

        if st.button("View Rewards"):
            display_rewards(st.session_state['user_points'])

if __name__ == '__main__':
    main()
