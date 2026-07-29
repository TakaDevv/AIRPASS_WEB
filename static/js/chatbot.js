// Chatbot simulé : réponses pré-enregistrées (aucune IA réelle connectée)
(function () {
    const chatWindow = document.getElementById("chatWindow");
    const chatForm = document.getElementById("chatForm");
    const chatInput = document.getElementById("chatInput");

    const responses = [
        { keywords: ["acheter", "billet", "reserver", "réserver"],
          answer: "Pour acheter un billet : ouvrez un évènement depuis la page d'accueil, cliquez sur « Acheter », choisissez votre place sur le plan du stade, puis validez le paiement simulé." },
        { keywords: ["parking", "voiture", "garer"],
          answer: "Une place de parking est attribuée automatiquement dès l'achat de votre billet. Vous retrouverez le numéro de votre place dans « Mes billets »." },
        { keywords: ["perdu", "perdre"],
          answer: "Pas de panique ! Votre billet reste disponible à tout moment dans la section « Mes billets » de votre compte, avec son QR Code." },
        { keywords: ["paiement", "payer", "carte"],
          answer: "Le paiement est simulé dans ce prototype : aucune carte bancaire réelle n'est nécessaire. Cliquez simplement sur « Payer » pour valider votre réservation." },
        { keywords: ["nfc"],
          answer: "Le contrôle NFC à l'entrée du stade est simulé par un bouton « Scanner NFC » sur la page de votre billet." },
        { keywords: ["face id", "faceid", "identite", "identité"],
          answer: "La vérification d'identité (Face ID) est simulée par un bouton « Identité vérifiée » sur la page de votre billet." },
        { keywords: ["bonjour", "salut", "hello"],
          answer: "Bonjour ! Comment puis-je vous aider avec votre billet ou votre réservation ?" },
    ];

    function findAnswer(text) {
        const lower = text.toLowerCase();
        for (const r of responses) {
            if (r.keywords.some(k => lower.includes(k))) return r.answer;
        }
        return "Je n'ai pas toutes les informations sur ce sujet dans cette démonstration, mais un conseiller humain pourra vous aider prochainement.";
    }

    function addBubble(text, who) {
        const div = document.createElement("div");
        div.className = "chat-bubble " + who;
        div.textContent = text;
        chatWindow.appendChild(div);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    function sendMessage(text) {
        if (!text.trim()) return;
        addBubble(text, "user");
        setTimeout(() => addBubble(findAnswer(text), "bot"), 500);
    }

    chatForm.addEventListener("submit", function (e) {
        e.preventDefault();
        sendMessage(chatInput.value);
        chatInput.value = "";
    });

    document.querySelectorAll(".quick-q").forEach(btn => {
        btn.addEventListener("click", () => sendMessage(btn.textContent));
    });
})();
