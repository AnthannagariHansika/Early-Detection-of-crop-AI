import streamlit as st
from ultralytics import YOLO
from PIL import Image
from datetime import datetime
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

with c5:
    st.metric(
        "🐛 Pest Risk",
        pest_risk
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
    # PEST RISK
    # ========================================================

    if (
        "yellow_curl" in disease.lower()
        or "yellow curl" in disease.lower()
    ):

        pest_risk = "HIGH"

        pest_name = (
            "Whitefly (Bemisia tabaci)"
        )

        pesticide = (
            "Thiamethoxam 25% WG"
        )

        pest_action = (
            "Confirm infestation and "
            "follow the product label."
        )


    elif (
        "blight" in disease.lower()
        or "septoria" in disease.lower()
    ):

        pest_risk = "MEDIUM"

        pest_name = (
            "Whitefly / Aphid"
        )

        pesticide = (
            "Thiamethoxam 25% WG"
        )

        pest_action = (
            "Use yellow sticky traps "
            "and follow IPM practices."
        )


    else:

        pest_risk = "LOW"

        pest_name = (
            "No major pest indicated"
        )

        pesticide = "Not required"

        pest_action = (
            "Continue monitoring and "
            "use yellow sticky traps."
        )


    # ========================================================
    # FINAL FLAG
    # ========================================================

    if "Healthy" not in disease:

        flag = "RED"

    elif (
        weather_risk == "HIGH"
        or pest_risk == "HIGH"
    ):

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

            st.error(
                "🐛 Pest Risk: HIGH"
            )

        elif pest_risk == "MEDIUM":

            st.warning(
                "🐛 Pest Risk: MEDIUM"
            )

        else:

            st.success(
                "🐛 Pest Risk: LOW"
            )


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


# ============================================================
# AUTOMATIC VOICE ALERT DEMO
# ============================================================

if prediction_done and (
    pest_risk == "HIGH"
    or weather_risk == "HIGH"
):

    st.subheader(
        "🔊 Automatic Voice Alert"
    )

    if preferred_language == "Telugu":

        voice_message = (
            "రైతు గారికి హెచ్చరిక. "
            "పంటలో సమస్య గుర్తించబడింది. "
            "దయచేసి వెంటనే పంటను పరిశీలించండి."
        )

    elif preferred_language == "Hindi":

        voice_message = (
            "किसान के लिए चेतावनी। "
            "फसल में समस्या पाई गई है। "
            "कृपया तुरंत फसल की जाँच करें।"
        )

    else:

        voice_message = (
            "Attention farmer. "
            "A crop problem has been detected. "
            "Please inspect the crop immediately."
        )

    st.write(
        voice_message
    )

    st.info(
        "🔊 Voice alert prepared in the selected language."
    )


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


# ------------------------------------------------------------
# DISPLAY MAP
# ------------------------------------------------------------

st_folium(
    m,
    width=900,
    height=550
)


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
# 🗺️ TELANGANA DISEASE HOTSPOT MAP
# =================================================

st.divider()

st.subheader("🗺️ Telangana Disease Hotspot Map")

st.info("📍 Disease hotspot monitoring across Telangana")

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

m = folium.Map(
    location=[17.95, 79.20],
    zoom_start=7
)

for h in hotspots:

    if h["risk"] == "HIGH":
        color = "red"
    elif h["risk"] == "MEDIUM":
        color = "orange"
    else:
        color = "green"

    folium.CircleMarker(
        location=[h["lat"], h["lon"]],
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

st_folium(m, width=900, height=550)