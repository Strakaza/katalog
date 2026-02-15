from flask import Flask, render_template_string, request, jsonify
from yt_dlp import YoutubeDL 
import threading
import json
import os
import requests 

app = Flask(__name__)

log_storage = []
is_downloading = False
progress = {"current": 0, "total": 0}

def capture_logs_playlist(url):
    """Boucle sur la playlist et envoie chaque vidéo au service IA (5006)"""
    global is_downloading, log_storage, progress
    is_downloading = True
    log_storage.clear()
    progress = {"current": 0, "total": 0}
    
    try:
        log_storage.append(f"> ANALYSE DE LA PLAYLIST...")
        
        ydl_opts = {
            'extract_flat': True, # Récupère juste les infos sans télécharger
            'quiet': True,
            'ignoreerrors': True,
        }
        
        video_ids = []
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' in info:
                # C'est une playlist
                video_ids = [entry['id'] for entry in info['entries'] if entry]
            elif 'id' in info:
                # C'est une vidéo unique
                video_ids = [info['id']]
        
        progress["total"] = len(video_ids)
        log_storage.append(f"> {progress['total']} ÉLÉMENTS DÉTECTÉS. LANCEMENT DU BATCH IA.")

        for index, v_id in enumerate(video_ids):
            progress["current"] = index + 1
            v_url = f"https://www.youtube.com/watch?v={v_id}"
            
            log_storage.append(f"--- VIDÉO {progress['current']}/{progress['total']} ---")
            log_storage.append(f"> ENVOI À L'IA : {v_id}")
            
            try:
                # Appel au service IA (ia_processor.py)
                response = requests.get(f"http://localhost:5006/add?url={v_url}", timeout=600)
                if response.status_code == 200:
                    log_storage.append(f"> SUCCÈS : FICHE NOTION CRÉÉE.")
                else:
                    log_storage.append(f"> ERREUR IA : CODE {response.status_code}")
            except Exception as e:
                log_storage.append(f"> ERREUR DE CONNEXION IA : {str(e)}")

        log_storage.append("> TOUS LES TRAITEMENTS SONT TERMINÉS.")
    except Exception as e:
        log_storage.append(f"> ERREUR CRITIQUE PLAYLIST: {str(e)}")
    finally:
        is_downloading = False

HTML_PAGE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YT—EXTRACT // PLAYLIST IA BATCH</title>
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Space+Mono:ital,wght@0,400;0,700;1,400&family=Syne:wght@500;700;800&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --bg-paper: #F2F0E9;
            --ink: #050505;
            --accent: #FF3C00;
            --grid-line: rgba(5, 5, 5, 0.08);
            --font-art: 'Syne', sans-serif;
            --font-tech: 'Space Mono', monospace;
            --ease-snap: cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        * { box-sizing: border-box; }

        body {
            background-color: var(--bg-paper);
            color: var(--ink);
            font-family: var(--font-tech);
            margin: 0; height: 100vh;
            display: grid; grid-template-rows: 1fr 220px;
            overflow: hidden;
        }

        body::before {
            content: ""; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.08'/%3E%3C/svg%3E");
            pointer-events: none; z-index: 998;
        }

        .main-stage { display: grid; grid-template-columns: 0.8fr 1.2fr; overflow-y: auto; position: relative; }
        .visual-pane { padding: 4rem; display: flex; flex-direction: column; justify-content: space-between; border-right: 2px solid var(--ink); }
        
        .giant-title { font-family: var(--font-art); font-size: 5vw; font-weight: 800; line-height: 0.85; text-transform: uppercase; letter-spacing: -2px; color: var(--ink); margin: 0; }
        .giant-title span { display: block; color: transparent; -webkit-text-stroke: 2px var(--ink); }
        .giant-title span.filled { color: var(--ink); -webkit-text-stroke: 0; }
        
        .meta-data { border-top: 2px solid var(--ink); padding-top: 2rem; display: flex; justify-content: space-between; font-size: 0.8rem; text-transform: uppercase; font-weight: bold; }

        .form-pane { padding: 4rem 6rem; position: relative; display: flex; flex-direction: column; justify-content: center; }
        .grid-bg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-image: linear-gradient(var(--grid-line) 1px, transparent 1px), linear-gradient(90deg, var(--grid-line) 1px, transparent 1px); background-size: 40px 40px; z-index: -1; }

        .form-group { margin-bottom: 2rem; position: relative; }
        label { display: block; font-family: var(--font-art); font-weight: 800; font-size: 1.2rem; margin-bottom: 0.8rem; transition: color 0.3s; }
        
        input[type="text"] {
            width: 100%; background: transparent; border: none; border-bottom: 3px solid var(--ink);
            padding: 15px 10px; font-family: var(--font-tech); font-size: 1.1rem; color: var(--ink);
            outline: none; cursor: text; transition: all 0.3s var(--ease-snap);
        }
        input:focus { border-bottom-color: var(--accent); background: rgba(0,0,0,0.03); padding-left: 25px; }
        .form-group:focus-within label { color: var(--accent); }

        .btn-mini {
            background: transparent; border: 2px solid var(--ink); color: var(--ink);
            font-family: var(--font-art); font-weight: 800; text-transform: uppercase;
            padding: 10px 20px; cursor: pointer; font-size: 0.9rem;
            transition: all 0.2s; white-space: nowrap; height: 50px;
            display: inline-flex; align-items: center; text-decoration: none;
        }
        .btn-mini:hover { background: var(--ink); color: var(--bg-paper); }
        .btn-mini:active { transform: scale(0.95); }

        .nav-link-top { position: absolute; top: 30px; right: 30px; z-index: 100; }

        .btn {
            margin-top: 2rem; background: var(--ink); color: var(--bg-paper); 
            border: none; padding: 2rem; width: 100%; font-family: var(--font-art); font-weight: 800; 
            font-size: 1.4rem; text-transform: uppercase; cursor: pointer; 
            transition: all 0.1s; position: relative; display: flex; justify-content: space-between; align-items: center;
        }
        .btn:hover { background: var(--accent); padding-left: 2.5rem; }
        .btn:active { transform: scale(0.98); }
        .btn:disabled { opacity: 0.7; cursor: wait; background: #555; transform: none; }

        .log-section { border-top: 4px solid var(--ink); background: var(--bg-paper); display: flex; flex-direction: column; position: relative; }
        .log-header { background: var(--ink); color: var(--bg-paper); padding: 5px 20px; font-size: 0.7rem; text-transform: uppercase; font-weight: bold; display: flex; justify-content: space-between; }
        .log-container { flex: 1; overflow-y: auto; padding: 20px 40px; font-family: var(--font-tech); font-size: 0.85rem; color: #333; }
        .log-container div { margin-bottom: 5px; border-left: 2px solid #ddd; padding-left: 10px; }

        @media (max-width: 900px) {
            body { grid-template-rows: auto 1fr 200px; overflow-y: scroll; }
            .main-stage { display: block; }
            .visual-pane, .form-pane { padding: 2rem; border: none; border-bottom: 2px solid var(--ink); }
            .giant-title { font-size: 12vw; }
            .nav-link-top { top: 10px; right: 10px; font-size: 0.7rem; padding: 5px 10px; height: 35px; }
        }
    </style>
</head>
<body>

    <a href="/" class="btn-mini nav-link-top">
        TOOL_01 // MEDIA SYSTEM
    </a>

    <div class="main-stage">
        <div class="visual-pane">
            <div>
                <div style="font-family: var(--font-tech); font-size: 0.8rem; margin-bottom: 1rem;">( TOOL_02 )</div>
                <h1 class="giant-title"><span>PLAYLIST</span><span class="filled">BATCH</span><span>PROCESSING</span></h1>
            </div>
            <div class="meta-data">
                <div>Local: /France</div>
                <div>SEQUENCE: <span id="prog-ui" style="color:var(--accent)">0 / 0</span></div>
            </div>
        </div>

        <div class="form-pane">
            <div class="grid-bg"></div>
            
            <form id="playlist-form">
                <div class="form-group">
                    <label>01. URL DE LA PLAYLIST YOUTUBE</label>
                    <input type="text" name="url" placeholder="https://www.youtube.com/playlist?list=..." required autocomplete="off">
                </div>
                
                <button type="submit" id="submit-btn" class="btn">LANCER LE TRAITEMENT IA</button>
            </form>
        </div>
    </div>

    <div class="log-section">
        <div class="log-header"><span>JOURNAL D'OPÉRATIONS</span></div>
        <div class="log-container" id="log-container">
            <div style="opacity:0.5">En attente de saisie...</div>
        </div>
    </div>

    <script>
        const form = document.getElementById('playlist-form');
        const btn = document.getElementById('submit-btn');
        const logs = document.getElementById('log-container');
        const progUi = document.getElementById('prog-ui');

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            btn.disabled = true;
            logs.innerHTML = '> Initialisation...';
            fetch('/start-download', { method: 'POST', body: new FormData(form) })
            .then(r => r.json())
            .then(() => setInterval(updateLogs, 1000));
        });

        function updateLogs() {
            fetch('/get-logs').then(r => r.json()).then(data => {
                logs.innerHTML = data.logs.map(l => `<div>${l}</div>`).join('');
                logs.scrollTop = logs.scrollHeight;
                if(data.progress.total > 0) progUi.innerText = `${data.progress.current} / ${data.progress.total}`;
                if(!data.active) btn.disabled = false;
            });
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/start-download', methods=['POST'])
def start():
    global is_downloading
    if is_downloading: return jsonify({"status": "busy"}), 400
    url = request.form.get('url')
    threading.Thread(target=capture_logs_playlist, args=(url,)).start()
    return jsonify({"status": "started"})

@app.route('/get-logs')
def get():
    return jsonify({"active": is_downloading, "logs": log_storage, "progress": progress})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
