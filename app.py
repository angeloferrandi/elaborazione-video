from flask import Flask, request, jsonify, send_file
import os
import cv2
import mediapipe as mp

app = Flask(__name__)

# Percorsi delle cartelle
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
        </head>
        <body style="text-align: center;">
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
    if 'video' not in request.files:
        return jsonify({"error": "Nessun file video caricato"}), 400

    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({"error": "Nessun file selezionato"}), 400

    # Salva il file caricato
    file_path = os.path.join(UPLOAD_FOLDER, video_file.filename)
    video_file.save(file_path)

    # Percorso per il file elaborato
    processed_path = os.path.join(PROCESSED_FOLDER, f"processed_{video_file.filename}")

    # Processa il video
    success = process_video(file_path, processed_path)
    if not success:
        return jsonify({"error": "Errore durante l'elaborazione del video"}), 500

    # Restituisci il link per scaricare il video elaborato
    return f'''
        <!doctype html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Video Elaborato</title>
        </head>
        <body style="text-align: center;">
            <h1>Video Elaborato con Successo!</h1>
            <p><a href="/download/{os.path.basename(processed_path)}" style="font-size: 1.2em; color: blue; text-decoration: none;">Scarica il video elaborato</a></p>
        </body>
        </html>
    '''

@app.route('/download/<filename>')
def download_file(filename):
    # Restituisce il file elaborato per il download
    return send_file(os.path.join(PROCESSED_FOLDER, filename), as_attachment=True)

def process_video(input_path, output_path):
    try:
        cap = cv2.VideoCapture(input_path)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = None
        frame_count = 0

        # Ottieni le dimensioni originali del video
        original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        original_fps = cap.get(cv2.CAP_PROP_FPS)

        # Calcola la nuova altezza e larghezza mantenendo le proporzioni
        target_width = 640  # Larghezza desiderata
        scale_factor = target_width / original_width
        target_height = int(original_height * scale_factor)

        # Calcola il nuovo FPS per il video di output
        processed_fps = original_fps / 5  # Processiamo 1 frame ogni 5

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            # Processa 1 frame ogni 5
            if frame_count % 5 != 0:
                continue

            # Ridimensiona mantenendo le proporzioni
            frame = cv2.resize(frame, (target_width, target_height))

            # Converti il frame in RGB per MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(rgb_frame)

            # Disegna i landmark sul frame
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(
                    frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS
                )

            # Inizializza il writer solo una volta
            if out is None:
                out = cv2.VideoWriter(output_path, fourcc, processed_fps, (target_width, target_height))

            out.write(frame)

        cap.release()
        if out:
            out.release()
        return True
    except Exception as e:
        print(f"Errore durante l'elaborazione: {e}")
        return False

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)

