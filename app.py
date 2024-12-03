from flask import Flask, request, jsonify, render_template, send_file
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
    # Mostra una semplice pagina web per caricare video
    return '''
        <!doctype html>
        <title>Carica Video</title>
        <h1>Carica un Video</h1>
        <form method="POST" action="/upload" enctype="multipart/form-data">
          <input type="file" name="video" accept="video/*">
          <button type="submit">Carica</button>
        </form>
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

    # Restituisci il video elaborato
    return f'''
        <!doctype html>
        <title>Elaborazione Completata</title>
        <h1>Video Elaborato con Successo!</h1>
        <p>Scarica il video processato:</p>
        <a href="/download/{os.path.basename(processed_path)}" download>Scarica il video</a>
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
