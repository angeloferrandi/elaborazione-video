from flask import Flask, request, jsonify, render_template, send_file
import os

app = Flask(__name__)

# Percorso per salvare temporaneamente i file caricati
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

    # Conferma il caricamento
    return f'''
        <!doctype html>
        <title>Caricamento Completato</title>
        <h1>Video Caricato con Successo!</h1>
        <p>Il video è stato salvato come: {file_path}</p>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
