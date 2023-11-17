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




def convert_text_to_speech(text):
    try:
        max_length = 3000
        parts = [text[i : i + max_length] for i in range(0, len(text), max_length)]

        audio_files = []  # 用于存储生成的音频文件路径

        for index, part in enumerate(parts):
            response = client.audio.speech.create(
                model="tts-1", voice="nova", input=part
            )
            part_file = f"output_part_{index}.mp3"
            response.stream_to_file(part_file)
            audio_files.append(part_file)

        return audio_files
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return []


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
camera_image = st.camera_input("Take a picture")

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


# File uploader for images (multiple files)
uploaded_files = st.file_uploader("Upload files", accept_multiple_files=True)

# Process each uploaded file
if uploaded_files:
    user_description_text = ""
    texts = []
    for uploaded_file in uploaded_files:
        image_base64 = encode_image_to_base64(uploaded_file)
        response = call_vision_api(image_base64)

        if response and "responses" in response:
            text_annotations = response["responses"][0].get("textAnnotations", [])
            if text_annotations:
                text = text_annotations[0]["description"]
                texts.append(text)  # Collect text from each file

    # Combine texts in reverse order
    user_description_text = "\n".join(texts)

    # Update user_description_text with all extracted text

# Text input for user's description
user_description = st.text_area(
    "Enter your description or text here:", value=user_description_text
)


# Function to automatically convert text to speech if there is a description
def auto_convert_to_speech(description):
    if description:
        audio_files = convert_text_to_speech(description)
        if audio_files:
            for audio_file in audio_files:
                st.audio(audio_file, format="audio/mpeg", start_time=0)
        else:
            st.error("Failed to convert text to speech.")


# Automatically call the convert to speech function if there is text in the description
auto_convert_to_speech(user_description)

# Buttons for different actions
generate_image_button = st.button("Generate Image")
convert_speech_button = st.button("Convert to Speech")


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
