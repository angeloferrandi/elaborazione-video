from flask import Flask, request, jsonify, send_file
import os
import cv2
import mediapipe as mp

app = Flask(__name__)

# Percorso per salvare temporaneamente i file caricati e processati
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# Configura MediaPipe
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()
mp_drawing = mp.solutions.drawing_utils

@app.route('/')
def home():
    return '''
        <!doctype html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Carica Video</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    margin: 0;
                    padding: 0;
                }
                h1 {
                    font-size: 1.8em;
                    margin-top: 20px;
                }
                form {
                    margin-top: 20px;
                }
                input[type="file"] {
                    font-size: 1.2em;
                }
                button {
                    font-size: 1.2em;
                    margin-top: 10px;
                    padding: 10px 20px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }
                button:hover {
                    background-color: #45a049;
                }
            </style>
        </head>
        <body>
            <h1>Carica un Video</h1>
            <form method="POST" action="/upload" enctype="multipart/form-data">
              <input type="file" name="video" accept="video/*">
              <button type="submit">Carica</button>
            </form>
        </body>
        </html>
    '''

@app.route('/upload', methods=['POST'])
def upload_video():
    # Controlla se un file è stato caricato
    if 'video' not in request.files:
        return jsonify({"error": "Nessun file video caricato"}), 400
    
    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({"error": "Nessun file selezionato"}), 400

    # Salva il file caricato
    file_path = os.path.join(UPLOAD_FOLDER, video_file.filename)
    video_file.save(file_path)

    # Processa il video con MediaPipe
    processed_path = os.path.join(PROCESSED_FOLDER, f"processed_{video_file.filename}")
    process_video(file_path, processed_path)

    # Redirigi alla pagina di conferma
    return f'''
        <!doctype html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Elaborazione Completata</title>
        </head>
        <body>
            <h1 style="font-size: 1.5em;">Video Elaborato con Successo!</h1>
            <p>Scarica il video processato:</p>
            <a href="/download/{os.path.basename(processed_path)}" 
               style="font-size: 1.2em; text-decoration: none; color: blue;">Scarica il video</a>
        </body>
        </html>
    '''

@app.route('/download/<filename>')
def download_file(filename):
    # Restituisce il video elaborato per il download
    return send_file(os.path.join(PROCESSED_FOLDER, filename), as_attachment=True)

def process_video(input_path, output_path):
    cap = cv2.VideoCapture(input_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Converti il frame in RGB per MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb_frame)

        # Disegna i landmark sul frame originale
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
            )

        # Inizializza il writer solo una volta
        if out is None:
            height, width, _ = frame.shape
            fps = cap.get(cv2.CAP_PROP_FPS)
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        out.write(frame)

    cap.release()
    if out:
        out.release()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
