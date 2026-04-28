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
    print("=== TRANSCRIBE REQUEST RECEIVED ===")
    
    if 'audio' not in request.files:
        print("ERROR: No audio file")
        return jsonify({'error': 'No audio file'}), 400
    
    audio_file = request.files['audio']
    print("Audio filename:", audio_file.filename)
    print("Audio content type:", audio_file.content_type)
    
    audio_data = audio_file.read()
    print("Audio size:", len(audio_data), "bytes")
    
    if len(audio_data) == 0:
        print("ERROR: Audio file is empty")
        return jsonify({'error': 'Audio file is empty'}), 400
    
    upload_headers = {"authorization": ASSEMBLYAI_API_KEY}
    print("Uploading to AssemblyAI...")
    
    upload_response = requests.post(
        BASE_URL + "/upload",
        headers=upload_headers,
        data=audio_data
    )
    
    print("Upload status:", upload_response.status_code)
    print("Upload response:", upload_response.text)
    
    if upload_response.status_code != 200:
        return jsonify({'error': 'Upload failed: ' + upload_response.text}), 500
    
    upload_json = upload_response.json()
    if "upload_url" not in upload_json:
        return jsonify({'error': 'No upload_url: ' + str(upload_json)}), 500
    
    audio_url = upload_json["upload_url"]
    print("Upload URL:", audio_url)
    
    print("Requesting transcription...")
    transcript_response = requests.post(
        BASE_URL + "/transcript",
        json={"audio_url": audio_url, "language_detection": True},
        headers={"authorization": ASSEMBLYAI_API_KEY, "content-type": "application/json"}
    )
    
    print("Transcript status:", transcript_response.status_code)
    print("Transcript response:", transcript_response.text)
    
    if transcript_response.status_code != 200:
        return jsonify({'error': 'Transcript failed: ' + transcript_response.text}), 500
    
    transcript_json = transcript_response.json()
    if "id" not in transcript_json:
        return jsonify({'error': 'No id: ' + str(transcript_json)}), 500
    
    transcript_id = transcript_json["id"]
    print("Transcript ID:", transcript_id)
    
    while True:
        result = requests.get(
            BASE_URL + "/transcript/" + transcript_id,
            headers={"authorization": ASSEMBLYAI_API_KEY}
        ).json()
        print("Status:", result["status"])
        if result["status"] == "completed":
            text = result.get("text") or "Tsy hita texte"
            print("Result:", text)
            return jsonify({"text": text})
        elif result["status"] == "error":
            print("Error:", result.get("error"))
            return jsonify({"error": result.get("error", "Unknown error")}), 500
        time.sleep(2)

application = app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
