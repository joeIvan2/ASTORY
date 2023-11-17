import streamlit as st
from openai import OpenAI
from pathlib import Path
import requests
from io import BytesIO
import base64


# Streamlit page setup
st.set_page_config(
    page_title="Text-Based Image and Speech Generator",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Page heading
st.title("🎨🔊 透過 AI 把圖片內的文字轉成語音 + 文字轉想像圖 👀")

# Retrieve the OpenAI API Key

api_key = st.secrets["kkk"]
google_api_key = st.secrets["google_api_key"]
# Initialize the OpenAI client
client = OpenAI(api_key=api_key)

# Variable to store and display the extracted or user-entered text
user_description_text = ""




# Function to convert text to speech
def convert_text_to_speech(text):
    try:
        response = client.audio.speech.create(model="tts-1", voice="nova", input=text)
        response.stream_to_file(speech_file_path)
        return True
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return False




# Function to encode the image to base64
def encode_image_to_base64(image_file):
    return base64.b64encode(image_file.read()).decode()


# Function to send POST request to Google Vision API
def call_vision_api(image_base64):
    url = f"https://vision.googleapis.com/v1/images:annotate?key={google_api_key}"
    headers = {"Content-Type": "application/json"}
    body = {
        "requests": [
            {
                "image": {"content": image_base64},
                "features": [{"type": "TEXT_DETECTION"}],
            }
        ]
    }

    response = requests.post(url, headers=headers, json=body)
    return response.json()


# File uploader for images
camera_image = st.camera_input("拍照文字")

# Check if an image is captured and extract text button is pressed
if camera_image:
    with st.spinner("Extracting text from image..."):
        image_base64 = encode_image_to_base64(camera_image)
        response = call_vision_api(image_base64)

        if response and "responses" in response:
            text_annotations = response["responses"][0].get("textAnnotations", [])
            if text_annotations:
                extracted_text = text_annotations[0]["description"]
                user_description_text = (
                    extracted_text  # Update the variable with extracted text
                )
                st.success("Text extracted from image!")
            else:
                st.error("No text detected in the image.")
        else:
            st.error("Failed to process the image.")

# Text input for user's description
user_description = st.text_area(
    "要轉成語音的文字:", value=user_description_text
)

# Directory to save the speech file
speech_file_dir = Path(__file__).parent
speech_file_path = speech_file_dir / "speech.mp3"


# Function to automatically convert text to speech if there is a description
def auto_convert_to_speech(description):
    if description:
        if convert_text_to_speech(description):
            st.audio(str(speech_file_path), format="audio/mpeg", start_time=0)
        else:
            st.error("Failed to convert text to speech.")


# Automatically call the convert to speech function if there is text in the description
auto_convert_to_speech(user_description)

# Buttons for different actions
generate_image_button = st.button("利用AI把文字轉成圖片")
convert_speech_button = st.button("將文字轉成語音")

# Directory to save the speech file
speech_file_dir = Path(__file__).parent
speech_file_path = speech_file_dir / "speech.mp3"

# Check if a description is provided and generate image button is pressed
if user_description and generate_image_button:
    with st.spinner("Generating the image ..."):
        try:
            # Make the request to generate the image
            response = client.images.generate(
                model="dall-e-3",
                prompt=user_description + "以上內容幫我稍做修飾與排版，只需要圖，不需要文字，純粹插畫即可",
                size="1024x1024",
                quality="standard",
                n=1,
            )

            # Get the URL of the generated image
            image_url = response.data[0].url

            # Display the generated image
            st.image(image_url, caption="Generated Image", use_column_width=True)

        except Exception as e:
            st.error(f"An error occurred: {e}")

# Check if text is provided and convert to speech button is pressed
if user_description and convert_speech_button:
    if convert_text_to_speech(user_description):
        st.audio(str(speech_file_path), format="audio/mpeg", start_time=0)
else:
    if not user_description and (generate_image_button or convert_speech_button):
        st.warning("Please enter a description or text.")
