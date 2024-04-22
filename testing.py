import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image

# initialize the client
CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key="uFsY2MHzUdNWrdNGsjcl"
)

st.title("Object Detection prototype")

# Allow user to upload an image
uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Open the uploaded image
    image = Image.open(uploaded_file)

    # Infer on the uploaded image
    result = CLIENT.infer(image, model_id="rubpred/4")

    # Display results
    st.image(image, caption='Uploaded Image', use_column_width=True)
    st.header("Detected objects:")
    summary = {
    'top': result['top'], 
    'confidence': result['confidence']
    }

    st.subheader("summary result:")
    st.write(summary)
    st.subheader("full result:")
    st.write(result)
