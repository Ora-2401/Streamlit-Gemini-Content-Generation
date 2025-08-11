import os
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def analyze_text(text):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(f"Analyze this text and summarize insights: {text}")
    return response.text

def create_text(prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt)
    return response.text

def analyze_image(image_path):
    model = genai.GenerativeModel("gemini-pro-vision")
    img = Image.open(image_path)
    response = model.generate_content(["Analyze this image in detail", img])
    return response.text

def create_image(prompt):
    model = genai.ImageGenerationModel("imagen-3.0")
    img = model.generate_images(prompt=prompt)
    return img.generated_images[0]
