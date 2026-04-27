from flask import Flask, request, jsonify
import requests
import os
import time

app = Flask(__name__)

ASSEMBLYAI_API_KEY = os.environ.get("ASSEMBLYAI_API_KEY")
BASE_URL = "https://api.assemblyai.com/v2"

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file'}), 400

    audio_file = request.files['audio']
    upload_headers = {"authorization": ASSEMBLYAI_API_KEY}
    
    upload_response = requests.post(
        BASE_URL + "/upload",
        headers=upload_headers,
        data=audio_file.read()
    )
    audio_url = upload_response.json()["upload_url"]

    transcript_response = requests.post(
        BASE_URL + "/transcript",
        json={"audio_url": audio_url, "language_detection": True},
        headers={"authorization": ASSEMBLYAI_API_KEY, "content-type": "application/json"}
    )
    transcript_id = transcript_response.json()["id"]

    while True:
        result = requests.get(
            BASE_URL + "/transcript/" + transcript_id,
            headers={"authorization": ASSEMBLYAI_API_KEY}
        ).json()
        if result["status"] == "completed":
            return jsonify({"text": result["text"]})
        elif result["status"] == "error":
            return jsonify({"error": result["error"]}), 500
        time.sleep(2)

application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
