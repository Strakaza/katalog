chrome.commands.onCommand.addListener((command) => {
  if (command === "save-to-notion") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const activeTab = tabs[0];
      if (activeTab.url.includes("youtube.com/watch")) {
        sendToPi(activeTab.url);
      }
    });
  }
});

try {
  importScripts('config.js');
} catch (e) {
  console.error(e);
}

function sendToPi(videoUrl) {
  const piEndpoint = `http://${CONFIG.SERVER_IP}:${CONFIG.PORT}/add?url=${encodeURIComponent(videoUrl)}`;
  fetch(piEndpoint)
    .then(response => response.json())
    .then(data => {
      console.log("Succès:", data);
      chrome.action.setBadgeText({ text: "OK" });
      setTimeout(() => chrome.action.setBadgeText({ text: "" }), 3000);
    })
    .catch(error => {
      console.error("Erreur:", error);
      chrome.action.setBadgeText({ text: "ERR" });
    });
}