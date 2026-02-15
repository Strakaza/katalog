from flask import Flask, request, jsonify
from flask_cors import CORS
from notion_client import Client
from yt_dlp import YoutubeDL
import os
import re
import requests
from datetime import datetime
import random
import json

app = Flask(__name__)
CORS(app)

# --- CONFIGURATION ---
def load_config():
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)

CONFIG = load_config()

NOTION_TOKEN = CONFIG["notion"]["token"]
DATABASE_ID = CONFIG["notion"]["database_id"]
notion = Client(auth=NOTION_TOKEN)
EMOJIS = ["📚", "💡", "🧠", "🎬", "🌍", "📺", "🧐", "📝", "🏛️", "🔋", "🚀", "📜", "⚖️", "🎨"]
def clean_vtt(text):
    """Nettoie les balises techniques des sous-titres VTT."""
    lines = text.split('\n')
    clean_lines = []
    for line in lines:
        if '-->' not in line and 'WEBVTT' not in line and 'Kind:' not in line and 'Language:' not in line:
            clean_line = re.sub(r'<[^>]+>', '', line).strip()
            if clean_line:
                clean_lines.append(clean_line)
    return " ".join(clean_lines)

def parse_rich_text(text):
    """Convertit un texte avec **gras** en rich_text Notion."""
    parts = re.split(r'(\*\*.*?\*\*)', text)
    rich_text = []
    for part in parts:
        if not part:
            continue
        if part.startswith('**') and part.endswith('**'):
            rich_text.append({
                "type": "text",
                "text": {"content": part[2:-2]},
                "annotations": {"bold": True}
            })
        else:
            rich_text.append({
                "type": "text",
                "text": {"content": part}
            })
    return rich_text if rich_text else [{"type": "text", "text": {"content": text}}]

def markdown_to_notion_blocks(md_text):
    """Convertit du texte Markdown en blocs Notion structurés."""
    blocks = []
    lines = md_text.split('\n')
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            continue
        
        if re.match(r'^-{3,}$', stripped):
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            continue
        
        match_h2 = re.match(r'^#{2,3}\s+\*{0,2}(.+?)\*{0,2}\s*$', stripped)
        if match_h2:
            title = match_h2.group(1).strip()
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"type": "text", "text": {"content": title}}]}
            })
            continue
        
        match_h3 = re.match(r'^#{4,}\s+\*{0,2}(.+?)\*{0,2}\s*$', stripped)
        if match_h3:
            title = match_h3.group(1).strip()
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"type": "text", "text": {"content": title}}]}
            })
            continue
        
        match_bullet = re.match(r'^[-*]\s+(.+)$', stripped)
        if match_bullet:
            content = match_bullet.group(1).strip()
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": parse_rich_text(content)}
            })
            continue
        
        match_numbered = re.match(r'^\d+\.\s+(.+)$', stripped)
        if match_numbered:
            content = match_numbered.group(1).strip()
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": parse_rich_text(content)}
            })
            continue
        

        cleaned = re.sub(r'^#+\s*', '', stripped)
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": parse_rich_text(cleaned)}
        })
    
    return blocks[:100]

def synthesize_text(raw_transcript):
    config = load_config() 
    transcript_text = raw_transcript[:60000]
    provider = config.get("provider", "ollama")
    
    system_prompt = """Tu es un expert en analyse de contenu vidéo et en synthèse documentaire.
Ta mission est de produire une fiche de lecture complète, détaillée et structurée EN FRANÇAIS à partir de la transcription fournie.
L'objectif est d'atteindre un niveau de détail suffisant pour permettre au lecteur de comprendre **l'intégralité du contenu** sans avoir besoin de regarder la vidéo.

RÈGLES CRITIQUES :
1. **Langue** : Réponds UNIQUEMENT en français.
2. **Exhaustivité** : Ne te contente pas de survoler. Explique chaque concept, argument ou tutoriel en profondeur.
3. **Structure** : Utilise le format Markdown ci-dessous.
4. **Filtrage** : Ignore strictement les sponsors, publicités, et introductions/outros inutiles (abonnements, likes, etc.).
5. **Formatage** : Utilise le gras pour mettre en évidence les termes importants.

FORMAT ATTENDU :

# [Titre de la Vidéo]

## Contexte et Objectif
(Présentation concise du sujet et de la problématique abordée. À qui s'adresse cette vidéo ?)

## Analyse Détaillée
(C'est la partie la plus importante. Divise le contenu en sous-sections thématiques claires si nécessaire, ou une liste de points approfondis.
Pour chaque point clé :
- Ne fais pas juste une phrase.
- Développe l'argumentation, donne les exemples cités, explique le "comment" et le "pourquoi".
- Si c'est un tutoriel, liste les étapes précises.)
- Si c'est du storytelling, il faut pouvoir comprendre l'histoire

## Pépites et Retenues
(Les informations les plus précieuses, astuces uniques, ou conclusions surprenantes)

## Synthèse Finale
(Le mot de la fin ou la conclusion générale de l'auteur)"""

    if provider == "openrouter":
        api_key = config["openrouter"]["api_key"]
        model = config["openrouter"]["model"]
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Transcription :\n{transcript_text}"}
            ]
        }
        
        try:
            print(f"DEBUG: Envoi à OpenRouter ({model})...")
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                return f"Erreur OpenRouter {response.status_code}: {response.text}"
                
        except Exception as e:
            return f"Erreur de connexion à OpenRouter : {str(e)}"

    else: 
        ollama_url = config["ollama"]["url"]
        model = config["ollama"]["model"]
        
        prompt = f"{system_prompt}\n\n[INSTRUCTION]\nTranscription :\n{transcript_text}\n"
        
        try:
            print(f"DEBUG: Envoi à Ollama ({model})...")
            response = requests.post(ollama_url, 
                json={
                    "model": model, 
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_ctx": 8192
                    }
                })
            return response.json().get('response', "Erreur de génération du texte.")
        except Exception as e:
            return f"Erreur de connexion à Ollama : {str(e)}"

def get_video_data(video_url):
    """Extrait les métadonnées et la transcription de YouTube."""
    filename = "temp_sub"
    ydl_opts = {
        'noplaylist': True,
        'skip_download': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['fr'],
        'outtmpl': filename,
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            title = info.get('title', 'Titre Inconnu')
            thumbnail = info.get('thumbnail')
            
            uploader_id = info.get('uploader_id')
            channel_url = f"https://www.youtube.com/{uploader_id}" if uploader_id else info.get('channel_url', 'Inconnue')
            
            print(f"DEBUG PI -> Vidéo : {title}")
            print(f"DEBUG PI -> Chaîne : {channel_url}")
            
            ydl.download([video_url])
        
        path_vtt = f"{filename}.fr.vtt"
        transcript = ""
        if os.path.exists(path_vtt):
            with open(path_vtt, "r", encoding="utf-8") as f:
                transcript = clean_vtt(f.read())
            os.remove(path_vtt)
        
        return title, channel_url, transcript, thumbnail
    except Exception as e:
        print(f"Erreur extraction YouTube : {e}")
        return None, None, str(e), None

@app.route('/add', methods=['GET'])
def add_video():
    video_url = request.args.get('url')
    if not video_url:
        return jsonify({"status": "error", "message": "URL manquante"}), 400

    v_title, v_channel, v_transcript, v_thumb = get_video_data(video_url)
    
    if not v_title:
        return jsonify({"status": "error", "message": "Erreur lors de l'extraction YouTube"}), 500

    print(f"Synthèse en cours pour : {v_title}...")
    v_summary = synthesize_text(v_transcript)

    random_emoji = random.choice(EMOJIS)

    try:
        children = markdown_to_notion_blocks(v_summary)
        
        notion.pages.create(
            parent={"database_id": DATABASE_ID},
            icon={
                "type": "emoji",
                "emoji": random_emoji
            },
            cover={
                "type": "external",
                "external": {"url": v_thumb}
            } if v_thumb else None,
            properties={
                "Name": {"title": [{"text": {"content": v_title}}]},
                "Chaine": {"multi_select": [{"name": v_channel}]},
                "type de contenue": {"multi_select": [{"name": "Web"}]},
                "date de visonnage": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}}
            },
            children=children
        )
        return jsonify({
            "status": "success", 
            "message": f"Ajouté avec l'icône {random_emoji}",
            "title": v_title
        })
    except Exception as e:
        print(f"Erreur lors de la création dans Notion : {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5006)