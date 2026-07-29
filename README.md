# AIRPASS — Prototype Web

Prototype fonctionnel de démonstration pour la plateforme de billetterie intelligente
**AIRPASS** (version Web uniquement, sans Face ID / NFC / IA réels — toutes ces
fonctionnalités sont simulées via des boutons dédiés, pour permettre une soutenance
réaliste sans dépendances matérielles ou cloud complexes).

## Stack technique

- **Frontend** : HTML5, CSS3, Bootstrap 5, JavaScript Vanilla
- **Backend** : Python Flask, SQLAlchemy, SQLite3
- **Auth** : Session Flask + mots de passe hashés (Werkzeug)
- **Sécurité** : Protection CSRF (Flask-WTF), validation des formulaires (WTForms)
- **QR Code** : librairie `qrcode`
- **PDF** : librairie `reportlab`

## Installation

```bash
cd airpass
python3 -m venv venv
source venv/bin/activate        # Windows : venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

L'application démarre sur **http://localhost:5000**.

Au tout premier lancement, la base `database.db` est créée automatiquement et
peuplée avec des données de démonstration :

- 3 stades (Alger, Blida, Oran)
- 8 événements sportifs
- 500 places par événement
- 20 utilisateurs
- 100 billets (avec QR Code + parking + notifications déjà générés)

## Comptes de démonstration

| Rôle  | Email                  | Mot de passe |
|-------|------------------------|--------------|
| Admin | admin@airpass.dz       | admin123     |
| User  | amine.boudiaf@example.com | password123 |

(Tous les 20 utilisateurs générés utilisent le mot de passe `password123`.)

## Fonctionnalités principales

- Inscription / connexion / profil
- Accueil avec recherche, stades, prochains matchs
- Détail d'un événement (places disponibles, prix, description)
- Réservation : plan de sièges interactif → paiement simulé ("Payer") → génération
  automatique du billet, du QR Code et de l'attribution de parking
- Mes billets : liste, détail, téléchargement PDF
- Simulation Face ID ("Identité vérifiée") et NFC ("Scanner NFC" → billet validé)
- Historique des notifications
- Assistant / chatbot simulé (réponses pré-enregistrées, pas d'IA réelle connectée)
- Dashboard administrateur : statistiques, gestion des utilisateurs, CRUD stades /
  événements / places, consultation des billets vendus et des réservations parking

## Réinitialiser les données de démonstration

Supprimez simplement le fichier `database.db` puis relancez `python app.py` :
les données seront régénérées automatiquement.

## Notes pour la soutenance

- Le paiement, le Face ID et le NFC sont **entièrement simulés** (aucune API bancaire,
  biométrique ou matérielle réelle) — conformément au cahier des charges du prototype.
- Le chatbot répond par mots-clés à partir d'un jeu de réponses pré-écrites ; il ne
  s'appuie sur aucun modèle de langage réel.
