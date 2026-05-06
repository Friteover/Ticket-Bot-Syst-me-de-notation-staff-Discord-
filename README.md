# 🎫 Ticket Bot — Système de notation staff (Discord)
![Version](https://img.shields.io/badge/version-1.0-blue) ![Licence](https://img.shields.io/badge/licence-MIT-green) ![Taille](https://img.shields.io/badge/taille-fichier%20unique-orange)
Un bot Discord complet permettant de :

* Créer des tickets facilement
* Fermer les tickets via bouton ou commande
* Envoyer une demande de notation au client
* Collecter des avis avec ou sans commentaire
* Logger les notes dans un salon staff

---

## ⚙️ Installation

1. Installe Python (3.10 ou + recommandé)

2. Installe les dépendances :

```bash
pip install discord.py
```

3. Clone le projet :

```bash
git clone https://github.com/Friteover/Ticket-Bot-Syst-me-de-notation-staff-Discord.git
cd ticket-bot
```

---

## 🔧 Configuration

Dans le fichier principal, modifie ces variables :

```python
BOT_TOKEN         = "TON_TOKEN_ICI"
STAFF_ROLE_ID     = 123456789012345678
TICKET_CATEGORY   = "Tickets"
LOG_CHANNEL_ID    = 123456789012345678
```

### 📌 Explications :

* `BOT_TOKEN` → Token de ton bot Discord
* `STAFF_ROLE_ID` → ID du rôle staff
* `TICKET_CATEGORY` → Nom de la catégorie où seront créés les tickets
* `LOG_CHANNEL_ID` → Salon où les avis seront envoyés

---

## 🚀 Lancement

```bash
python bot.py
```

---

## 🧩 Fonctionnalités

### 🎫 Création de ticket

Commande :

```
!ticket
```

➡️ Crée un salon privé entre l’utilisateur et le staff

---

### 🔒 Fermeture de ticket

* Bouton intégré dans le ticket
* Commande staff :

```
!fermer
```

---

### ⭐ Système de notation

Quand un ticket est fermé :

* L’utilisateur reçoit un **DM**
* Il peut noter de **1 à 5 étoiles**
* Il peut ajouter un commentaire (optionnel)

---

### 📝 Logs staff

Un embed est envoyé dans le salon défini avec :

* Utilisateur
* Staff
* Note
* Commentaire
* Verdict automatique

---

## 🛡️ Permissions requises

Le bot doit avoir :

* Gérer les salons
* Envoyer des messages
* Gérer les messages
* Lire les messages
* Envoyer des messages privés

---

## ⚠️ Important

* Active les **Intents** dans le portail Discord Developer :

  * `MESSAGE CONTENT INTENT`
* Vérifie que les utilisateurs peuvent recevoir des DMs

---

## 💡 Améliorations possibles

* Ajout d’une base de données (SQLite / MongoDB)
* Statistiques des notes staff
* Système de blacklist
* Traduction multi-langue
* Interface web

---

## 📄 Licence

Libre d’utilisation et de modification.

---

## ❤️ Support

Si tu as un problème ou une question :

* Ouvre une issue GitHub
* Ou contacte le développeur

---
