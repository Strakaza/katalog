# Tutoriel d'Installation et d'Utilisation - Katalog

Ce projet permet de récupérer automatiquement la transcription d'une vidéo YouTube, de la synthétiser via une IA (Cloud ou Locale) et d'envoyer le résultat directement dans une base de données Notion.

## Prérequis

Avant de commencer, assurez-vous d'avoir installé les logiciels suivants sur votre machine :

1.  **Python** (version 3.8 ou supérieure) : [Télécharger Python](https://www.python.org/downloads/)
    *   *Note : Cochez bien la case "Add Python to PATH" lors de l'installation.*
2.  **Git** (optionnel, pour cloner le projet) : [Télécharger Git](https://git-scm.com/downloads)
3.  **Ollama** (uniquement si vous souhaitez utiliser l'IA en local) : [Télécharger Ollama](https://ollama.com/)

---

## Installation

### 1. Récupérer le projet

Si vous avez Git, ouvrez un terminal et tapez :
```bash
git clone <URL_DU_DEPOT>
cd "gituhb2 - cloud"
```
Sinon, téléchargez le fichier ZIP depuis GitHub, extrayez-le et ouvrez le dossier dossier extrait.

### 2. Installer les dépendances

Ouvrez un terminal dans le dossier du projet (là où se trouve le fichier `requirements.txt`) et exécutez la commande suivante pour installer les bibliothèques nécessaires :

```bash
pip install -r requirements.txt
```

---

## Configuration

Le fichier `config.json` contient tous les réglages. Vous devez le modifier avec vos propres clés API.

Ouvrez le fichier `config.json` avec un éditeur de texte (Bloc-notes, VS Code, etc.).

### 1. Notion

**Conseil :** Pour vous faciliter la tâche, vous pouvez dupliquer ce modèle Notion qui contient déjà toutes les propriétés nécessaires : [Lien vers le template](https://strakaza.notion.site/305ac440c2c08012b711dbb4e27b13f9?v=305ac440c2c0808b90a6000c74d5662f)

Pour que le script puisse écrire dans votre Notion, il faut deux éléments :
1.  **Token d'intégration** : Créez une nouvelle intégration sur [Notion Developers](https://www.notion.so/my-integrations). Copiez le "Internal Integration Secret".
2.  **ID de la base de données** : Ouvrez votre base de données Notion dans le navigateur. L'ID se trouve dans l'URL après `notion.so/` et avant le `?`.
    *   *Exemple :* `https://www.notion.so/mon-espace/`**`251ac440c2c081cf9245d450db9291f1`**`?v=...`
    *   *Important :* N'oubliez pas de **connecter** votre intégration à la page de la base de données (menu "..." en haut à droite > "Add connections" > Sélectionnez votre intégration).

Remplissez les champs dans `config.json` :
```json
"notion": {
    "token": "VOTRE_TOKEN_NOTION",
    "database_id": "VOTRE_DATABASE_ID"
}
```

### 2. Choisir son IA (Cloud ou Locale)

Vous pouvez choisir entre utiliser **OpenRouter** (Cloud, payant ou gratuit selon le modèle) ou **Ollama** (Local, gratuit mais demande un bon PC).

Modifiez la ligne `"provider"` dans `config.json` :

*   Pour le Cloud : `"provider": "openrouter"`
*   Pour le Local : `"provider": "ollama"`

#### Configuration OpenRouter (Cloud)
1.  Créez un compte sur [OpenRouter](https://openrouter.ai/).
2.  Générez une clé API.
3.  Ajoutez-la dans `config.json` :
```json
"openrouter": {
    "api_key": "VOTRE_CLE_OPENROUTER",
    "model": "google/gemini-2.0-flash-lite-preview-02-05:free"
}
```
*Note : Vous pouvez changer le modèle selon vos préférences.*

#### Configuration Ollama (Local)
1.  Assurez-vous qu'Ollama est installé et lancé.
2.  Téléchargez le modèle souhaité (par exemple `qwen2.5:7b`) via la commande : `ollama pull qwen2.5:7b`
3.  Mettez à jour `config.json` :
```json
"ollama": {
    "url": "http://localhost:11434/api/generate",
    "model": "qwen2.5:7b"
}
```

---

## Installation de l'Extension Navigateur

Pour envoyer facilement les vidéos YouTube vers votre serveur, installez l'extension Chrome/Edge incluse.

1.  Ouvrez votre navigateur (Chrome, Edge, Brave...).
2.  Allez dans la gestion des extensions (tapez `chrome://extensions` ou `edge://extensions` dans la barre d'adresse).
3.  Activez le **Mode développeur** (souvent un switch en haut à droite ou à gauche).
4.  Cliquez sur le bouton **"Charger l'extension non empaquetée"** (Load unpacked).
5.  Sélectionnez le dossier de ce projet.
6.  L'icône de l'extension devrait apparaître dans votre barre d'outils.

---

## Utilisation

### Étape 1 : Lancer le serveur

Avant d'utiliser l'extension, le serveur Python doit être démarré.

Ouvrez un terminal dans le dossier du projet et lancez :
```bash
python ia_processor.py
```
Le serveur va démarrer et afficher qu'il écoute sur le port 5006. Laissez cette fenêtre ouverte.

### Étape 2 : Analyser une vidéo

1.  Allez sur une vidéo YouTube qui contient des sous-titres (même automatiques).
2.  Cliquez sur l'icône de l'extension dans votre navigateur.
3.  Cliquez sur le bouton **"Analyser la vidéo"**.
4.  Patientez quelques instants...
    *   Le serveur va télécharger les sous-titres.
    *   L'IA va générer le résumé.
    *   Le résultat sera envoyé sur Notion.
5.  Une notification vous confirmera que la fiche a été créée.
