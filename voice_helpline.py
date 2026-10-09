from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
import json
import os

app = Flask(__name__)

FARMER_FILE = "farmer_data.json"


def save_farmer(data):
    with open(FARMER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_farmer():
    if os.path.exists(FARMER_FILE):
        with open(FARMER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    return {}


# ============================================================
# START CALL
# ============================================================

@app.route("/voice", methods=["POST", "GET"])
def voice():

    response = VoiceResponse()

    gather = Gather(
        input="speech",
        action="/process",
        method="POST",
        speech_model="deepgram_nova-3",
        language="multi",
        speech_timeout=3
    )

    gather.say(
        "Welcome to Smart Crop Monitoring. "
        "Please tell me your name in your preferred language."
    )

    response.append(gather)

    response.say(
        "I could not understand you. Please call again."
    )

    return str(response)


# ============================================================
# PROCESS FIRST SPEECH
# ============================================================

@app.route("/process", methods=["POST"])
def process():

    speech = request.values.get("SpeechResult", "")
    caller_phone = request.values.get("From", "")

    print("Farmer said:", speech)
    print("Caller:", caller_phone)

    response = VoiceResponse()

    if not speech:

        response.say(
            "Sorry, I could not understand you. Please try again."
        )

        response.redirect("/voice")

        return str(response)

    # --------------------------------------------------------
    # IMPORTANT:
    # Twilio gives the recognized speech here.
    # We temporarily save it.
    # --------------------------------------------------------

    farmer = {
        "name": speech,
        "phone": caller_phone,
        "location": "",
        "language": "Auto detected",
        "crop": "Tomato"
    }

    save_farmer(farmer)

    # --------------------------------------------------------
    # Ask location
    # --------------------------------------------------------

    gather = Gather(
        input="speech",
        action="/save_location",
        method="POST",
        speech_model="deepgram_nova-3",
        language="multi",
        speech_timeout=3
    )

    gather.say(
        "Thank you. Now please tell me your farm location."
    )

    response.append(gather)

    return str(response)


# ============================================================
# SAVE LOCATION
# ============================================================

@app.route("/save_location", methods=["POST"])
def save_location():

    speech = request.values.get("SpeechResult", "")

    farmer = get_farmer()

    farmer["location"] = speech

    save_farmer(farmer)

    response = VoiceResponse()

    # Ask crop

    gather = Gather(
        input="speech",
        action="/save_crop",
        method="POST",
        speech_model="deepgram_nova-3",
        language="multi",
        speech_timeout=3
    )

    gather.say(
        "Please tell me which crop you want to monitor."
    )

    response.append(gather)

    return str(response)


# ============================================================
# SAVE CROP
# ============================================================

@app.route("/save_crop", methods=["POST"])
def save_crop():

    speech = request.values.get("SpeechResult", "")

    farmer = get_farmer()

    farmer["crop"] = speech

    save_farmer(farmer)

    response = VoiceResponse()

    response.say(
        "Your registration information has been saved."
    )

    response.say(
        "Smart Crop Monitoring is now ready for you."
    )

    response.say(
        "Thank you. Goodbye."
    )

    return str(response)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )