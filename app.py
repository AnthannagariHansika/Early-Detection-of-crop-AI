import sqlite3
import pyttsx3
import winsound
import hashlib
import streamlit as st
from ultralytics import YOLO
from PIL import Image
from datetime import datetime
import folium
from streamlit_folium import st_folium
from twilio.rest import Client

# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Smart Crop Monitoring System",
    page_icon="🌱",
    layout="wide"
)

def play_buzzer():
    try:
        winsound.Beep(1000, 700)
        winsound.Beep(1300, 700)
        winsound.Beep(1000, 700)
    except Exception as e:
        st.warning(f"Buzzer could not play: {e}")

# ============================================================
# FARMER REGISTRATION
# ============================================================

st.header("🌱 Farmer Registration")

registration_mode = st.radio(
    "Choose Registration Method",
    ["Self-Registration", "Helpline-Assisted Registration"],
    horizontal=True
)

if registration_mode == "Helpline-Assisted Registration":
    st.info(
        "The agent should speak in the farmer's preferred "
        "language and enter the farmer's answers."
    )
    agent_name = st.text_input("Helpline Agent Name")
else:
    agent_name = "Self-Registered"

with st.form("farmer_registration_form"):
    farmer_name = st.text_input("Farmer Full Name")
    mobile = st.text_input("Mobile Number")
    
    language = st.selectbox(
        "Preferred Language",
        ["Telugu", "Hindi", "English", "Tamil",
         "Kannada", "Marathi"]
    )

    village = st.text_input("Village")
    district = st.text_input("District")
    state = st.text_input("State", value="Telangana")

    crop = st.selectbox(
        "Main Crop",
        ["Tomato", "Rice", "Cotton", "Chilli", "Other"]
    )

    consent = st.checkbox(
        "I agree to the collection and use of these "
        "details for crop monitoring."
    )

    submitted = st.form_submit_button("Register Farmer")

if submitted:
    if not farmer_name.strip() or not mobile.strip():
        st.error("Please enter the farmer's name and mobile number.")
    elif not mobile.strip().isdigit() or len(mobile.strip()) != 10:
        st.error("Enter a valid 10-digit Indian mobile number.")
    elif not village.strip() or not district.strip():
        st.error("Please enter the village and district.")
    elif registration_mode == "Helpline-Assisted Registration" \
            and not agent_name.strip():
        st.error("Please enter the helpline agent's name.")
    elif not consent:
        st.warning("Please obtain the farmer's consent before registering.")
    else:
        try:
            conn = sqlite3.connect("farmers.db")
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS farmers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    mobile TEXT NOT NULL UNIQUE,
                    language TEXT,
                    village TEXT,
                    district TEXT,
                    state TEXT,
                    crop TEXT,
                    registration_mode TEXT,
                    agent_name TEXT
                )
            """)

            cursor.execute("""
                INSERT INTO farmers (
                    name, mobile, language, village, district,
                    state, crop, registration_mode, agent_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                farmer_name.strip(),
                mobile.strip(),
                language,
                village.strip(),
                district.strip(),
                state.strip(),
                crop,
                registration_mode,
                agent_name.strip()
            ))

            farmer_id = cursor.lastrowid
            conn.commit()
            conn.close()

            st.success("Registration successful!")
            st.write(f"Farmer Registration ID: {farmer_id}")
            st.write(f"Preferred language: {language}")
            st.write("You can now use the crop monitoring dashboard.")

        except sqlite3.IntegrityError:
            st.warning(
                "This mobile number is already registered. "
                "Please check the existing registration."
            )
        except sqlite3.Error as e:
            st.error(f"Database error: {e}")


# ============================================================
# FARMER LANGUAGE
# ============================================================

preferred_language = st.selectbox(
    "🗣️ Farmer Preferred Language",
    ["Telugu", "Hindi", "English"]
)

# ============================================================
# FARMER VOICE ALERT
# ============================================================

def play_farmer_alert(language, disease):
    messages = {
        "Telugu": (
            "హెచ్చరిక! పంటలో వ్యాధి లక్షణాలు కనిపించాయి. "
            "దయచేసి పంటను పరిశీలించండి."
        ),
        "Hindi": (
            "चेतावनी! फसल में बीमारी के लक्षण दिखाई दिए हैं। "
            "कृपया फसल की जाँच करें।"
        ),
        "English": (
            f"Warning! Possible crop disease detected: "
            f"{disease.replace('_', ' ')}. Please inspect your crop."
        ),
    }

    voice_message = messages.get(language, messages["English"])

    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 140)
        engine.say(voice_message)
        engine.runAndWait()
        engine.stop()

        # Audible buzzer on the computer running Streamlit
        winsound.Beep(1000, 1000)
        winsound.Beep(1200, 500)

    except Exception as e:
        st.error(f"Voice alert failed: {e}")




# ============================================================
# TITLE
# ============================================================

st.title("🌱 Smart Crop Monitoring System")

st.write(
    "AI-based crop disease detection, pest monitoring, "
    "weather risk, water monitoring and farmer alerts."
)


# ============================================================
# LOAD AI MODEL
# ============================================================

@st.cache_resource
def load_model():
    return YOLO(
        "runs/classify/tomato_disease_model/weights/best.pt"
    )


model = load_model()


def alert_farmer(language, disease):
    import winsound
    import pyttsx3

    messages = {
        "Telugu": "హెచ్చరిక! మొక్కలో వ్యాధి లక్షణాలు కనిపించాయి. దయచేసి మొక్కను పరిశీలించండి.",
        "Hindi": "चेतावनी! फसल में बीमारी के लक्षण दिखाई दिए हैं। कृपया पौधे की जाँच करें।",
        "English": f"Warning! Possible crop disease detected: {disease}. Please check your plant."
    }

    # Play buzzer sound on Windows
    winsound.MessageBeep(winsound.MB_ICONHAND)

    # Speak the alert
    engine = pyttsx3.init()
    engine.setProperty("rate", 140)
    engine.say(messages[language])
    engine.runAndWait()
    engine.stop()
# ============================================================
# SMS ALERT FUNCTION
# ============================================================

def send_farmer_sms(phone_number, disease):
    client = Client(
        st.secrets["TWILIO_ACCOUNT_SID"],
        st.secrets["TWILIO_AUTH_TOKEN"]
    )

    message = client.messages.create(
        body=(
            f"Crop Alert! Possible disease detected: {disease}. "
            "Please inspect your crop."
        ),
        from_=st.secrets["TWILIO_PHONE_NUMBER"],
        to=phone_number
    )

    return message.sid

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🌦️ Field Sensor Monitoring")

temperature = st.sidebar.slider(
    "🌡️ Temperature (°C)",
    10,
    50,
    28
)

humidity = st.sidebar.slider(
    "💧 Humidity (%)",
    20,
    100,
    65
)

soil_moisture = st.sidebar.slider(
    "🌱 Soil Moisture (%)",
    0,
    100,
    62
)

water_level = st.sidebar.slider(
    "🚰 Water Tank Level (%)",
    0,
    100,
    70
)

rainfall = st.sidebar.selectbox(
    "🌧️ Rainfall",
    ["Low", "Medium", "High"]
)

preferred_language = st.sidebar.selectbox(
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


# ============================================================
# DAY / NIGHT
# ============================================================

current_hour = datetime.now().hour

if 6 <= current_hour < 18:
    alert_time = "☀️ Day"
else:
    alert_time = "🌙 Night"

st.sidebar.info(
    f"🕐 Current Mode: {alert_time}"
)


# ============================================================
# WEATHER RISK
# ============================================================

if (
    temperature >= 32
    or humidity >= 85
    or rainfall == "High"
):
    weather_risk = "HIGH"

elif (
    temperature >= 28
    or humidity >= 70
    or rainfall == "Medium"
):
    weather_risk = "MEDIUM"

else:
    weather_risk = "LOW"


# ============================================================
# WATER STATUS
# ============================================================

if soil_moisture < 30:

    water_status = "WATER REQUIRED"
    water_flag = "BLUE"

elif soil_moisture < 60:

    water_status = "MONITOR"
    water_flag = "BLUE"

else:

    water_status = "NORMAL"
    water_flag = "GREEN"


# ============================================================
# WATER TANK STATUS
# ============================================================

if water_level < 20:

    tank_status = "LOW"

elif water_level < 50:

    tank_status = "MEDIUM"

else:

    tank_status = "NORMAL"


# ============================================================
# INITIAL VARIABLES
# ============================================================

prediction_done = False

disease = ""
confidence = 0

treatment = ""

flag = ""

pest_risk = "LOW"
pest_name = "No major pest indicated"
pesticide = "Not required"
pest_action = "Continue monitoring."


# ============================================================
# DASHBOARD
# ============================================================

st.subheader("📊 Field Dashboard")

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.metric(
        "🌡️ Temperature",
        f"{temperature} °C"
    )

with c2:
    st.metric(
        "💧 Humidity",
        f"{humidity}%"
    )

with c3:
    st.metric(
        "🌱 Soil Moisture",
        f"{soil_moisture}%"
    )

with c4:
    st.metric(
        "🚰 Water Level",
        f"{water_level}%"
    )



# ============================================================
# WEATHER STATUS
# ============================================================

st.subheader("🌦️ Environmental Status")

w1, w2, w3 = st.columns(3)

with w1:

    if weather_risk == "HIGH":
        st.error("🌦️ Weather Risk: HIGH")

    elif weather_risk == "MEDIUM":
        st.warning("🌦️ Weather Risk: MEDIUM")

    else:
        st.success("🌦️ Weather Risk: LOW")


with w2:

    if water_status == "WATER REQUIRED":
        st.error("💧 Water: REQUIRED")

    elif water_status == "MONITOR":
        st.warning("💧 Water: MONITOR")

    else:
        st.success("💧 Water: NORMAL")


with w3:

    if tank_status == "LOW":
        st.error("🚰 Tank: LOW")

    elif tank_status == "MEDIUM":
        st.warning("🚰 Tank: MEDIUM")

    else:
        st.success("🚰 Tank: NORMAL")


# ============================================================
# IMAGE INPUT
# ============================================================

st.divider()

st.subheader("📷 Crop Image Analysis")

col1, col2 = st.columns(2)

with col1:

    uploaded = st.file_uploader(
        "📁 Upload Tomato Leaf Image",
        type=["jpg", "jpeg", "png"]
    )


with col2:

    camera_image = st.camera_input(
        "📷 Capture Image"
    )


if camera_image is not None:

    uploaded = camera_image
# Farmer Preferred Language

preferred_language = st.selectbox(
    "🗣️ Farmer Preferred Language",
    ["Telugu", "Hindi", "English"],
    key="farmer_voice_language"
)


# ============================================================
# AI PREDICTION
# ============================================================

if uploaded is not None:

    image = Image.open(uploaded)

    st.image(
        image,
        caption="🌱 Crop Image",
        width=450
    )

    with st.spinner(
        "🤖 AI is analyzing the crop..."
    ):

        result = model.predict(
            image,
            verbose=False
        )[0]

    class_id = int(
        result.probs.top1
    )

    confidence = float(
        result.probs.top1conf
    )

    disease = result.names[class_id]

    prediction_done = True


    # Determine crop status
    disease_name = disease.lower()

    if "healthy" in disease_name:
        flag = "GREEN"
    else:
        flag = "RED"

    # Display prediction result
    st.subheader("🔍 AI Prediction Result")
    st.write(f"**Disease:** {disease.replace('_', ' ')}")
    st.write(f"**Confidence:** {confidence * 100:.2f}%")

    # Trigger buzzer for suspected disease
    if flag == "RED":
        st.error("🚨 RISK DETECTED!")
        st.write("Please inspect your crop.")
        play_buzzer()
    else:
        st.success("✅ Crop image classified as healthy.")

    # ========================================================
    # DISEASE INFORMATION
    # ========================================================

    st.divider()

    st.subheader("🩺 AI Disease Detection")

    st.write(
        f"### Disease: {disease.replace('_', ' ')}"
    )

    st.write(
        f"🎯 Confidence: {confidence * 100:.2f}%"
    )


    # ========================================================
    # TREATMENT
    # ========================================================

    if "Healthy" in disease:

        treatment = (
            "Crop appears healthy. "
            "Continue normal crop monitoring."
        )

    elif "Early_blight" in disease:

        treatment = (
            "Remove infected leaves and improve "
            "air circulation around plants."
        )

    elif "late_blight" in disease.lower():

        treatment = (
            "Remove infected leaves and avoid "
            "excess moisture."
        )

    elif "yellow_curl" in disease.lower():

        treatment = (
            "Monitor and control whiteflies. "
            "Remove severely infected plants."
        )

    elif "mold" in disease.lower():

        treatment = (
            "Improve ventilation and reduce "
            "leaf moisture."
        )

    elif "Septoria" in disease:

        treatment = (
            "Remove infected leaves and avoid "
            "overhead watering."
        )

    else:

        treatment = (
            "Inspect the crop and consult "
            "an agricultural expert."
        )


    st.info(
        f"💊 Recommended Action: {treatment}"
    )


        # ========================================================
    # PEST RISK, POSSIBLE INSECT AND TREATMENT
    # ========================================================

    disease_name = disease.lower()

    if "healthy" in disease_name:
        pest_risk = "LOW"
        pest_name = "No insect identified"
        pesticide = "No pesticide required based on this image"
        pest_action = "Continue monitoring the crop."

    elif "yellow_curl" in disease_name or "yellow curl" in disease_name:
        pest_risk = "HIGH"
        pest_name = "Whitefly (possible association)"
        pesticide = "Consider a locally registered whitefly control product only after confirming infestation."
        pest_action = "Inspect the undersides of leaves for whiteflies."

    elif "late_blight" in disease_name:
        pest_risk = "HIGH"
        pest_name = "Insect not identified; late blight is a disease"
        pesticide = "Ask an agricultural expert about a registered fungicide for confirmed late blight."
        pest_action = "Remove severely affected plant material and avoid wetting leaves."

    elif "early_blight" in disease_name:
        pest_risk = "MEDIUM"
        pest_name = "No insect confirmed; inspect for aphids and whiteflies"
        pesticide = "For disease treatment, consult an expert about a registered fungicide for early blight."
        pest_action = (
        "Remove affected leaves where appropriate, "
        "improve airflow, and inspect for insects."
    )

    elif "septoria" in disease_name:
        pest_risk = "HIGH"
        pest_name = "No insect confirmed; inspect the plant"
        pesticide = "For disease treatment, consult an expert about a registered fungicide for Septoria leaf spot."
        pest_action = (
        "Remove affected leaves, avoid overhead watering, "
        "and monitor disease spread."
    )

    elif "mold" in disease_name:
        pest_risk = "MEDIUM"
        pest_name = "Insect not identified; inspect the crop"
        pesticide = "No insecticide indicated by this image. Confirm the mold/disease diagnosis."
        pest_action = "Improve airflow and reduce prolonged leaf wetness."

    else:
        pest_risk = "LOW"
        pest_name = "Unknown; field inspection needed"
        pesticide = "No pesticide recommendation until the problem is identified."
        pest_action = "Consult an agricultural expert."

    # Environmental adjustment
    if humidity >= 85 and temperature >= 28 and pest_risk != "HIGH":
        pest_risk = "HIGH"
        pest_action += " Environmental conditions warrant closer monitoring."

    elif humidity >= 75 and pest_risk == "LOW":
        pest_risk = "MEDIUM"
        pest_action += " Humidity is elevated; monitor the crop."

    # Display results ONCE
    st.subheader("🐛 Pest and Treatment Information")

    if pest_risk == "HIGH":
        st.error("Pest / crop risk: HIGH")
    elif pest_risk == "MEDIUM":
        st.warning("Pest / crop risk: MEDIUM")
    else:
        st.success("Pest / crop risk: LOW")

    st.write(f"**Possible insect:** {pest_name}")
    st.write(f"**Treatment guidance:** {pesticide}")
    st.info(f"**Recommended action:** {pest_action}")
    # ========================================================
    # DISEASE STATUS AND FLAG
    # ========================================================

    if "healthy" in disease_name:
        flag = "GREEN"
        buzzer_status = "OFF"
    else:
        flag = "RED"
        buzzer_status = "ON"

    # ========================================================
    # DISEASE AND PEST OUTPUT
    # ========================================================

    st.subheader("🩺 AI Disease Detection")
    st.write(f"**Disease:** {disease.replace('_', ' ')}")
    st.write(f"**Confidence:** {confidence * 100:.2f}%")

    st.subheader("🐛 Pest and Treatment Information")
    st.write(f"**Pest Risk:** {pest_risk}")
    st.write(f"**Possible insect:** {pest_name}")
    st.write(f"**Treatment guidance:** {pesticide}")
    st.info(f"🌱 **Recommended action:** {pest_action}")

    st.subheader("🚩 Field Alert")
    if flag == "RED":
        st.error("🔴 RED FLAG — Disease detected")
        st.error("🔔 BUZZER: ON (software demo)")
    else:
        st.success("🟢 GREEN FLAG — Healthy class predicted")
        st.success("🔔 BUZZER: OFF (software demo)")
# ========================================================
# 3. DASHBOARD
# ========================================================

with c5:
    st.metric("🐛 Pest Risk", pest_risk)

st.info(f"🐛 Pest indicator: {pest_name}")
st.write(f"**Recommended action:** {pest_action}")
st.write(f"**Treatment:** {pesticide}")


# ========================================================
# FINAL FLAG
# ========================================================

if "Healthy" not in disease:
    flag = "RED"

elif weather_risk == "HIGH" or pest_risk == "HIGH":
    flag = "ORANGE"

elif rainfall == "Low":
    flag = "BLUE"

else:
    flag = "GREEN"    
# ========================================================
    # FLAG STATUS
    # ========================================================

    st.subheader("🚩 Field Flag Status")

    if flag == "RED":

        st.error(
            "🔴 RED FLAG — Disease/Pest Problem"
        )

    elif flag == "ORANGE":

        st.warning(
            "🟠 ORANGE FLAG — High Risk"
        )

    elif flag == "BLUE":

        st.info(
            "🔵 BLUE FLAG — Water Monitoring"
        )

    else:

        st.success(
            "🟢 GREEN FLAG — Crop Healthy"
        )


    # ========================================================
    # PEST INFORMATION
    # ========================================================

    st.subheader("🐛 Pest Information")

    p1, p2, p3 = st.columns(3)

    with p1:
        st.write(
            f"**Risk:** {pest_risk}"
        )

    with p2:
        st.write(
            f"**Insect:** {pest_name}"
        )

    with p3:
        st.write(
            f"**Pesticide:** {pesticide}"
        )

    st.info(
        f"🌱 Recommended Action: {pest_action}"
    )


    # ========================================================
    # RISK STATUS
    # ========================================================

    st.subheader("⚠️ Risk Status")

    r1, r2 = st.columns(2)

    with r1:

        if weather_risk == "HIGH":

            st.error(
                "🌦️ Weather Risk: HIGH"
            )

        elif weather_risk == "MEDIUM":

            st.warning(
                "🌦️ Weather Risk: MEDIUM"
            )

        else:

            st.success(
                "🌦️ Weather Risk: LOW"
            )


    with r2:
       if pest_risk == "HIGH":
        st.error(f"🐛 Pest Risk: HIGH")
       elif pest_risk == "MEDIUM":
        st.warning(f"🐛 Pest Risk: MEDIUM")
       else:
        st.success(f"🐛 Pest Risk: LOW")

    st.write(f"**Possible insect/pest:** {pest_name}")
    st.write(f"**Treatment guidance:** {pesticide}")
    st.write(f"**Recommended action:** {pest_action}")

# ============================================================
# ALERT SYSTEM
# ============================================================

if prediction_done:

    st.divider()

    st.subheader("🚨 Farmer Alert System")

    if flag == "GREEN":

        st.success(
            "🟢 No immediate alert required."
        )

    else:

        st.warning(
            f"🚨 Alert Activated: {flag} FLAG"
        )

        st.write(
            "🔔 Buzzer: ON"
        )

        st.write(
            f"📱 Mobile Alert: READY"
        )

        st.write(
            f"🗣️ Language: {preferred_language}"
        )

        st.write(
            f"🕐 Mode: {alert_time}"
        )


# ============================================================
# AUTOMATIC SMS ALERT
# ============================================================

if prediction_done and (
    pest_risk == "HIGH"
    or weather_risk == "HIGH"
):

    st.divider()

    st.error(
        "🚨 HIGH RISK — AUTOMATIC SMS ACTIVATED"
    )


    if preferred_language == "Telugu":

        sms_message = f"""🌱 పంట హెచ్చరిక

వ్యాధి: {disease.replace("_", " ")}
పురుగు ప్రమాదం: {pest_risk}
పురుగు: {pest_name}
వాతావరణ ప్రమాదం: {weather_risk}

దయచేసి వెంటనే పంటను పరిశీలించండి."""


    elif preferred_language == "Hindi":

        sms_message = f"""🌱 फसल चेतावनी

रोग: {disease.replace("_", " ")}
कीट जोखिम: {pest_risk}
कीट: {pest_name}
मौसम जोखिम: {weather_risk}

कृपया तुरंत फसल की जाँच करें."""


    elif preferred_language == "Tamil":

        sms_message = f"""🌱 பயிர் எச்சரிக்கை

நோய்: {disease.replace("_", " ")}
பூச்சி ஆபத்து: {pest_risk}
பூச்சி: {pest_name}
வானிலை ஆபத்து: {weather_risk}

தயவுசெய்து பயிரை உடனடியாக பரிசோதிக்கவும்."""


    elif preferred_language == "Kannada":

        sms_message = f"""🌱 ಬೆಳೆ ಎಚ್ಚರಿಕೆ

ರೋಗ: {disease.replace("_", " ")}
ಕೀಟ ಅಪಾಯ: {pest_risk}
ಕೀಟ: {pest_name}
ಹವಾಮಾನ ಅಪಾಯ: {weather_risk}

ದಯವಿಟ್ಟು ಬೆಳೆ ಪರಿಶೀಲಿಸಿ."""


    elif preferred_language == "Marathi":

        sms_message = f"""🌱 पीक सूचना

रोग: {disease.replace("_", " ")}
कीड धोका: {pest_risk}
कीड: {pest_name}
हवामान धोका: {weather_risk}

कृपया पिकाची त्वरित तपासणी करा."""


    else:

        sms_message = f"""🌱 SMART CROP ALERT

Disease: {disease.replace("_", " ")}
Pest Risk: {pest_risk}
Insect: {pest_name}
Weather Risk: {weather_risk}

Please take necessary action."""


    st.write("📩 Automatic SMS")

    st.code(
        sms_message
    )

    st.success(
        f"✅ SMS READY — Language: {preferred_language}"
    )

# VOICE ALERT TEST IN STREAMLIT
st.subheader("🔔 Buzzer")

if st.button("▶️ Play Voice"):
    try:
        engine = pyttsx3.init()
        engine.setProperty("rate", 140)
        engine.say("Warning farmer. Crop disease detected.")
        engine.runAndWait()
        engine.stop()
        st.success("Voice played successfully!")
    except Exception as e:
        st.error(f"Voice error: {e}")


# ============================================================
# FARMER HELP CENTER
# ============================================================

st.divider()

st.subheader(
    "📞 Farmer Help Center"
)

st.info(
    f"🌐 Preferred Language: {preferred_language}"
)

st.write(
    "👨‍🌾 Agricultural support:"
)

st.write(
    "• Crop disease problems"
)

st.write(
    "• Pest and insect problems"
)

st.write(
    "• Pesticide guidance"
)

st.write(
    "• Water and crop management"
)

st.write(
    "• Agricultural expert support"
)

st.link_button(
    "📞 Call Farmer Helpline",
    "tel:18001801551"
)


# ============================================================
# 🗺️ TELANGANA DISEASE HOTSPOT MAP
# ============================================================

st.divider()

st.subheader(
    "🗺️ Telangana Disease Hotspot Map"
)

st.info(
    "📍 Demo hotspot data for SIH prototype. "
    "Real hotspots will be generated from GPS-tagged farmer reports."
)


# ------------------------------------------------------------
# DEMO HOTSPOT DATA
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# CREATE MAP
# ------------------------------------------------------------

m = folium.Map(
    location=[17.95, 79.20],
    zoom_start=7
)


# ------------------------------------------------------------
# ADD HOTSPOTS
# ------------------------------------------------------------

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
            f"Cases: {h['cases']}<br>"
            f"Risk: {h['risk']}"
        )

    ).add_to(m)


# ============================================================
# SYSTEM STATUS
# ============================================================

st.divider()

st.subheader(
    "⚙️ System Status"
)

s1, s2, s3, s4 = st.columns(4)

with s1:

    st.success(
        "🤖 Local AI: Working"
    )

with s2:

    st.success(
        "📡 GSM: Ready"
    )

with s3:

    st.success(
        "🔔 Alert System: Ready"
    )

with s4:

    st.success(
        "🗺️ GIS Map: Ready"
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "SIH Prototype | AI Disease Detection • "
    "Sensor Monitoring • Offline AI • "
    "Day/Night Alerts • Multilingual Alerts • "
    "Buzzer • GSM • GIS Hotspot Mapping • Help Center"
)

# =================================================
# 🗺️ COMBINED TELANGANA DISEASE + FARM MAP
# =================================================

st.divider()
st.subheader("🗺️ Telangana Crop Monitoring Map")

st.info(
    "District disease hotspots and farmer field location "
    "shown together on one interactive map."
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

# Example field location only — replace with actual GPS
farmer_lat = 17.3850
farmer_lon = 78.4867

# Create ONE map
m = folium.Map(
    location=[17.95, 79.20],
    zoom_start=7
)

# Add district hotspots
for h in hotspots:

    if h["risk"] == "HIGH":
        color = "red"
    elif h["risk"] == "MEDIUM":
        color = "orange"
    else:
        color = "green"

    folium.CircleMarker(
        location=[h["lat"], h["lon"]],
        radius=10,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        tooltip=h["district"],
        popup=(
            f"<b>{h['district']}</b><br>"
            f"Disease: {h['disease']}<br>"
            f"Cases: {h['cases']}<br>"
            f"Risk: {h['risk']}"
        )
    ).add_to(m)

# Add farmer field to the SAME map
folium.Marker(
    location=[farmer_lat, farmer_lon],
    tooltip="Example Farmer Field",
    popup="Example farmer field location",
    icon=folium.Icon(color="blue", icon="home")
).add_to(m)

# Display the map only ONCE
st_folium(
    m,
    width=900,
    height=550,
    key="combined_crop_monitoring_map"
)
# Buzzer Sound Test
st.subheader("🔔 Buzzer Alert")

if st.button("🔔 Test Buzzer Sound"):
    winsound.MessageBeep(winsound.MB_ICONHAND)
    st.success("Buzzer sound played!")

# AUTOMATIC VOICE ALERT
if prediction_done and flag == "RED":

    if preferred_language == "Telugu":
        voice_message = "రైతు గారికి హెచ్చరిక. పంటను పరిశీలించండి."
    elif preferred_language == "Hindi":
        voice_message = "किसान के लिए चेतावनी। कृपया फसल की जाँच करें।"
    else:
        voice_message = (
            "Warning farmer. Possible crop disease detected. "
            "Please inspect your crop."
        )

    st.subheader("🔊 Automatic Farmer Voice Alert")

# AUTOMATIC VOICE ALERT
if prediction_done and flag == "RED":

    if preferred_language == "Telugu":
        voice_message = "రైతు గారికి హెచ్చరిక. పంటను పరిశీలించండి."
    elif preferred_language == "Hindi":
        voice_message = "किसान के लिए चेतावनी। कृपया फसल की जाँच करें।"
    else:
        voice_message = "Warning farmer. Possible crop disease detected."

    st.subheader("🔊 Automatic Farmer Voice Alert")
    st.write(voice_message)

    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 140)
        engine.say(voice_message)
        engine.runAndWait()
        engine.stop()
        st.success("Voice alert played!")

    except Exception as e:
        st.error(f"Voice alert failed: {e}")

    st.write(voice_message)

    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty("rate", 140)
        engine.say(voice_message)
        engine.runAndWait()
        engine.stop()
        st.success("Voice alert played!")

    except Exception as e:
        st.error(f"Voice alert failed: {e}")
