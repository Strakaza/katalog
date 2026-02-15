document.addEventListener('DOMContentLoaded', function () {
    const logSection = document.getElementById('logs');
    const statusText = document.getElementById('status');
    const sendBtn = document.getElementById('sendBtn');
    const urlInput = document.getElementById('urlInput');

    function addLog(text, isImportant = false) {
        const div = document.createElement('div');
        div.className = 'log-entry';
        if (isImportant) div.style.borderLeftColor = "#FF3C00";
        div.innerHTML = `[${new Date().toLocaleTimeString()}] ${text}`;
        logSection.appendChild(div);
        logSection.scrollTop = logSection.scrollHeight;
    }

    chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
        if (tabs[0] && tabs[0].url) {
            urlInput.value = tabs[0].url;
            addLog("CIBLE DÉTECTÉE : " + tabs[0].title.substring(0, 25) + "...");
        }
    });

    sendBtn.addEventListener('click', function () {
        const url = urlInput.value;

        sendBtn.disabled = true;
        statusText.innerHTML = 'СТАТУС : <span class="accent-text">SYNTHÈSE EN COURS...</span>';
        addLog("COMMUNICATION AVEC l'IA...");


        fetch(`http://${CONFIG.SERVER_IP}:${CONFIG.PORT}/add?url=${encodeURIComponent(url)}`)
            .then(response => {
                if (!response.ok) throw new Error(`Erreur Serveur: ${response.status}`);
                return response.json();
            })
            .then(data => {
                addLog("TERMINÉ : FICHE NOTION CRÉÉE !", true);
                statusText.innerHTML = 'СТАТУС : <span class="accent-text">SUCCÈS</span>';
            })
            .catch(error => {
                addLog("ERREUR CRITIQUE : SERVEUR INJOIGNABLE", true);
                statusText.innerHTML = 'СТАТУС : <span class="accent-text">ÉCHEC</span>';
                console.error("Détails de l'erreur:", error);
            })
            .finally(() => {
                sendBtn.disabled = false;
                sendBtn.innerHTML = '<span>RE-LANCER</span><span>↺</span>';
            });
    });
});