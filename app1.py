# ============================================================
# 🌱 SMART CROP MONITORING SYSTEM
# SIH 26131 - Early Detection and Management of
# Crop Diseases and Pest Infestations
# ============================================================

import os
import json
from datetime import datetime

import streamlit as st
from PIL import Image
from ultralytics import YOLO
import pyttsx3
import folium
from streamlit_folium import st_folium

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Smart Crop Monitoring System",
    page_icon="🌱",
    layout="wide"
)


# ============================================================
# AUTOMATIC DAY / NIGHT
# ============================================================

current_hour = datetime.now().hour

if 6 <= current_hour < 18:
    day_night = "☀️ DAY"
else:
    day_night = "🌙 NIGHT"


# ============================================================
# MODEL PATH
# ============================================================

MODEL_PATH = (
    "runs/classify/tomato_disease_model/weights/best.pt"
)


# ============================================================
# SESSION STATE
# ============================================================

if "farmer_registered" not in st.session_state:
    st.session_state.farmer_registered = False

if "farmer" not in st.session_state:
    st.session_state.farmer = {}

if "prediction_done" not in st.session_state:
    st.session_state.prediction_done = False

if "disease" not in st.session_state:
    st.session_state.disease = "Not analyzed"

if "confidence" not in st.session_state:
    st.session_state.confidence = 0.0

if "image_source" not in st.session_state:
    st.session_state.image_source = ""


# ============================================================
# LOAD MODEL
# ============================================================

@st.cache_resource
def load_model():
    if not os.path.exists(MODEL_PATH):
        return None

    return YOLO(MODEL_PATH)


model = load_model()


# ============================================================
# VOICE ALERT FUNCTION
# ============================================================

def create_voice_alert(message):

    try:

        engine = pyttsx3.init()

        engine.setProperty("rate", 145)

        engine.save_to_file(
            message,
            "voice_alert.wav"
        )

        engine.runAndWait()

        return os.path.exists(
            "voice_alert.wav"
        )

    except Exception:
        return False


# ============================================================
# PHONE ALERT DEMO
# ============================================================

def phone_alert(phone, message):

    st.info(
        f"📱 Phone Alert Prepared\n\n"
        f"Number: {phone}\n\n"
        f"Message: {message}"
    )


# ============================================================
# MULTILINGUAL MESSAGES
# ============================================================

def get_disease_message(
    language,
    farmer_name,
    disease
):

    disease_name = disease.replace(
        "_",
        " "
    )

    messages = {

        "English":
            f"Alert {farmer_name}. "
            f"{disease_name} has been detected "
            f"in your tomato crop. "
            f"Please inspect the affected plants "
            f"and take the recommended action.",

        "Telugu":
            f"{farmer_name} గారూ, "
            f"మీ టమాటా పంటలో {disease_name} "
            f"వ్యాధి గుర్తించబడింది. "
            f"దయచేసి ప్రభావిత మొక్కలను పరిశీలించి "
            f"సూచించిన చర్య తీసుకోండి.",

        "Hindi":
            f"{farmer_name} जी, "
            f"आपकी टमाटर की फसल में "
            f"{disease_name} रोग पाया गया है। "
            f"कृपया प्रभावित पौधों की जांच करें "
            f"और सुझाया गया उपचार करें।",

        "Tamil":
            f"{farmer_name}, "
            f"உங்கள் தக்காளி பயிரில் "
            f"{disease_name} நோய் கண்டறியப்பட்டுள்ளது. "
            f"பாதிக்கப்பட்ட செடிகளை பரிசோதித்து "
            f"பரிந்துரைக்கப்பட்ட நடவடிக்கையை எடுக்கவும்.",

        "Kannada":
            f"{farmer_name} ಅವರೇ, "
            f"ನಿಮ್ಮ ಟೊಮೇಟೊ ಬೆಳೆಯಲ್ಲಿ "
            f"{disease_name} ರೋಗ ಕಂಡುಬಂದಿದೆ. "
            f"ದಯವಿಟ್ಟು ಪೀಡಿತ ಸಸ್ಯಗಳನ್ನು ಪರಿಶೀಲಿಸಿ "
            f"ಶಿಫಾರಸು ಮಾಡಿದ ಕ್ರಮ ತೆಗೆದುಕೊಳ್ಳಿ.",

        "Marathi":
            f"{farmer_name}, "
            f"तुमच्या टोमॅटो पिकामध्ये "
            f"{disease_name} रोग आढळला आहे. "
            f"कृपया प्रभावित झाडांची तपासणी करा "
            f"आणि शिफारस केलेली कृती करा."
    }

    return messages.get(
        language,
        messages["English"]
    )


def get_water_message(
    language,
    farmer_name
):

    messages = {

        "English":
            f"{farmer_name}, your crop needs water. "
            f"Please check the soil moisture.",

        "Telugu":
            f"{farmer_name} గారూ, "
            f"మీ పంటకు నీరు అవసరం. "
            f"దయచేసి నేల తేమను పరిశీలించండి.",

        "Hindi":
            f"{farmer_name} जी, "
            f"आपकी फसल को पानी की आवश्यकता है। "
            f"कृपया मिट्टी की नमी जांचें.",

        "Tamil":
            f"{farmer_name}, "
            f"உங்கள் பயிருக்கு தண்ணீர் தேவை. "
            f"மண் ஈரப்பதத்தை சரிபார்க்கவும்.",

        "Kannada":
            f"{farmer_name} ಅವರೇ, "
            f"ನಿಮ್ಮ ಬೆಳೆಗೆ ನೀರು ಅಗತ್ಯವಿದೆ. "
            f"ಮಣ್ಣಿನ ತೇವಾಂಶವನ್ನು ಪರಿಶೀಲಿಸಿ.",

        "Marathi":
            f"{farmer_name}, "
            f"तुमच्या पिकाला पाण्याची गरज आहे. "
            f"मातीतील ओलावा तपासा."
    }

    return messages.get(
        language,
        messages["English"]
    )


def get_risk_message(
    language,
    farmer_name
):

    messages = {

        "English":
            f"Alert {farmer_name}. "
            f"High crop risk has been detected. "
            f"Please inspect your field.",

        "Telugu":
            f"{farmer_name} గారూ, "
            f"పంటకు అధిక ప్రమాదం గుర్తించబడింది. "
            f"దయచేసి పొలాన్ని పరిశీలించండి.",

        "Hindi":
            f"{farmer_name} जी, "
            f"फसल में अधिक जोखिम पाया गया है। "
            f"कृपया खेत की जांच करें।",

        "Tamil":
            f"{farmer_name}, "
            f"பயிரில் அதிக ஆபத்து கண்டறியப்பட்டுள்ளது. "
            f"வயலை பரிசோதிக்கவும்.",

        "Kannada":
            f"{farmer_name} ಅವರೇ, "
            f"ಬೆಳೆಯಲ್ಲಿ ಹೆಚ್ಚಿನ ಅಪಾಯ ಕಂಡುಬಂದಿದೆ. "
            f"ದಯವಿಟ್ಟು ಹೊಲವನ್ನು ಪರಿಶೀಲಿಸಿ.",

        "Marathi":
            f"{farmer_name}, "
            f"पिकामध्ये जास्त धोका आढळला आहे. "
            f"कृपया शेताची तपासणी करा."
    }

    return messages.get(
        language,
        messages["English"]
    )


# ============================================================
# TITLE
# ============================================================

st.title(
    "🌱 Smart Crop Monitoring System"
)

st.caption(
    "SIH 26131 | AI Crop Disease, Pest, "
    "Weather & Water Monitoring"
)


# ============================================================
# TOP STATUS
# ============================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "🌾 Crop",
    "Tomato"
)

c2.metric(
    "🤖 AI",
    "YOLO"
)

c3.metric(
    "🕐 Mode",
    day_night
)

c4.metric(
    "📡 Operation",
    "Local + Sync"
)


# ============================================================
# FARMER REGISTRATION
# ============================================================

st.header("👨‍🌾 Farmer Registration")

registration_method = st.radio(
    "Registration Method",
    [
        "📝 Self Registration",
        "🤖 AI Voice Helpline"
    ],
    horizontal=True
)


if registration_method == "📝 Self Registration":

    with st.form(
        "farmer_registration"
    ):

        farmer_name = st.text_input(
            "👤 Farmer Name"
        )

        farmer_phone = st.text_input(
            "📱 Registered Mobile Number"
        )

        farmer_location = st.text_input(
            "📍 Farm Location",
            value="Telangana"
        )

        preferred_language = st.selectbox(
            "🗣️ Preferred Language",
            [
                "English",
                "Telugu",
                "Hindi",
                "Tamil",
                "Kannada",
                "Marathi"
            ]
        )

        submitted = st.form_submit_button(
            "✅ Register Farmer"
        )

        if submitted:

            if (
                farmer_name
                and farmer_phone
            ):

                st.session_state.farmer = {

                    "name":
                        farmer_name,

                    "phone":
                        farmer_phone,

                    "location":
                        farmer_location,

                    "language":
                        preferred_language
                }

                st.session_state.farmer_registered = True

                st.success(
                    "✅ Farmer registered successfully."
                )

            else:

                st.warning(
                    "Please enter farmer name "
                    "and mobile number."
                )


else:

    st.info(
        "🤖 AI Voice Helpline\n\n"
        "For the final SIH version, the farmer "
        "can call the AI helpline. The AI can "
        "ask registration questions by voice "
        "and save the farmer details."
    )

    st.warning(
        "☎️ Real phone-call AI requires a "
        "telephony service such as Twilio "
        "and a public voice webhook."
    )

    st.write(
        "Prototype status: Voice Helpline "
        "integration ready for backend connection."
    )


# ============================================================
# REGISTERED FARMER DISPLAY
# ============================================================

if st.session_state.farmer_registered:

    farmer = st.session_state.farmer

    st.success(
        f"👨‍🌾 Registered Farmer: "
        f"{farmer['name']}"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "📱 Mobile",
        farmer["phone"]
    )

    c2.metric(
        "📍 Location",
        farmer["location"]
    )

    c3.metric(
        "🗣️ Language",
        farmer["language"]
    )

    c4.metric(
        "🌾 Crop",
        "Tomato"
    )


# ============================================================
# CAMERA / IMAGE INPUT
# ============================================================

st.header(
    "📷 Crop Image Diagnosis"
)

st.write(
    "Take a fresh crop photo using the camera "
    "or upload an existing image."
)


input_method = st.radio(
    "Choose Image Source",
    [
        "📷 Camera",
        "📁 Upload Image"
    ],
    horizontal=True
)


camera_image = None
uploaded_image = None


if input_method == "📷 Camera":

    camera_image = st.camera_input(
        "📷 Take a picture of tomato leaf",
        key="crop_camera",
        help="Capture a clear picture of the affected leaf."
    )

    image_file = camera_image

else:

    uploaded_image = st.file_uploader(
        "📁 Upload tomato leaf image",
        type=[
            "jpg",
            "jpeg",
            "png"
        ],
        key="crop_upload"
    )

    image_file = uploaded_image


# ============================================================
# AI DISEASE ANALYSIS
# ============================================================

prediction_done = False

disease = "Not analyzed"

confidence = 0.0


if image_file is not None:

    try:

        image = Image.open(
            image_file
        )

        st.image(
            image,
            caption="Crop Image",
            use_container_width=True
        )

        st.write(
            "📸 Image captured successfully."
        )

        if st.button(
            "🔍 Analyze Crop",
            type="primary"
        ):

            if model is None:

                st.error(
                    "❌ AI model not found."
                )

                st.code(
                    MODEL_PATH
                )

            else:

                with st.spinner(
                    "🤖 AI is analyzing the crop..."
                ):

                    results = model.predict(
                        image,
                        imgsz=224,
                        verbose=False
                    )

                result = results[0]

                class_id = (
                    result.probs.top1
                )

                confidence = (
                    float(
                        result.probs.top1conf
                    ) * 100
                )

                disease = (
                    result.names[class_id]
                )

                prediction_done = True

                st.session_state.prediction_done = True

                st.session_state.disease = disease

                st.session_state.confidence = confidence

                st.session_state.image_source = (
                    input_method
                )

                st.success(
                    "✅ Crop analysis completed."
                )

    except Exception as e:

        st.error(
            f"❌ Image processing error: {e}"
        )


# ============================================================
# DEFAULT VALUES
# ============================================================

if not prediction_done:

    prediction_done = (
        st.session_state.prediction_done
    )

    disease = (
        st.session_state.disease
    )

    confidence = (
        st.session_state.confidence
    )



# ============================================================
# 🌡️ FIELD SENSOR MONITORING
# ============================================================

st.header("🌡️ Field Sensor Monitoring")

s1, s2, s3, s4 = st.columns(4)

with s1:
    temperature = st.slider(
        "🌡️ Temperature °C",
        10,
        45,
        28
    )

with s2:
    humidity = st.slider(
        "💧 Humidity %",
        20,
        100,
        65
    )

with s3:
    soil_moisture = st.slider(
        "🌱 Soil Moisture %",
        0,
        100,
        62
    )

with s4:
    water_level = st.slider(
        "🚰 Water Tank %",
        0,
        100,
        70
    )

rain = st.slider(
    "🌧️ Rainfall mm",
    0,
    100,
    2
)

        
# =================================================
# 🗺️ TELANGANA TOMATO DISEASE HOTSPOT MAP
# =================================================

st.divider()

st.subheader("🗺️ Telangana Tomato Disease Hotspot Map")

st.info(
    "📍 Tomato disease monitoring across major tomato-growing "
    "districts of Telangana"
)

hotspots = [
    {
        "district": "Rangareddy",
        "lat": 17.32,
        "lon": 78.40,
        "disease": "Septoria Leaf Spot",
        "cases": 42,
        "risk": "HIGH"
    },
    {
        "district": "Vikarabad",
        "lat": 17.34,
        "lon": 77.90,
        "disease": "Early Blight",
        "cases": 31,
        "risk": "MEDIUM"
    },
    {
        "district": "Siddipet",
        "lat": 18.10,
        "lon": 78.85,
        "disease": "Late Blight",
        "cases": 18,
        "risk": "MEDIUM"
    },
    {
        "district": "Sangareddy",
        "lat": 17.62,
        "lon": 78.08,
        "disease": "Yellow Curl Virus",
        "cases": 12,
        "risk": "LOW"
    }
]


# =================================================
# CREATE MAP
# =================================================

m = folium.Map(
    location=[17.95, 79.20],
    zoom_start=7
)


# =================================================
# ADD HOTSPOT MARKERS
# =================================================

for h in hotspots:

    if h["risk"] == "HIGH":

        color = "red"

    elif h["risk"] == "MEDIUM":

        color = "orange"

    else:

        color = "green"


    folium.CircleMarker(

        location=[
            h["lat"],
            h["lon"]
        ],

        radius=12,

        color=color,

        fill=True,

        fill_color=color,

        fill_opacity=0.7,

        popup=(
            f"<b>{h['district']}</b><br>"
            f"Disease: {h['disease']}<br>"
            f"Reported Cases: {h['cases']}<br>"
            f"Risk Level: {h['risk']}"
        ),

        tooltip=(
            f"{h['district']} - "
            f"{h['disease']}"
        )

    ).add_to(m)


# =================================================
# DISPLAY MAP
# =================================================

st_folium(
    m,
    width=900,
    height=550
)


# =================================================
# MAP LEGEND / EXPLANATION
# =================================================

st.markdown(
    """
    ### 📊 Hotspot Legend

    🔴 **HIGH** — Immediate attention required

    🟠 **MEDIUM** — Continuous monitoring required

    🟢 **LOW** — Normal monitoring

    **How this works in the final SIH system:**

    Farmer → Crop Image → AI Disease Detection →
    Location → Local Database → Disease Hotspot Map

    When multiple farmers report the same disease from
    nearby locations, the system can identify a potential
    disease hotspot for agriculture officials.
    """
)