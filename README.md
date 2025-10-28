# Agentia Support Client Email - MVP

## Description
Système d'automatisation pour la gestion des emails de support client utilisant :
- n8n pour l'orchestration
- Gmail API pour la réception/envoi d'emails
- Hugging Face (gratuit) pour la classification automatique

## Architecture

### Workflow principal : Classification des emails
1. **Gmail Trigger** : Détection des nouveaux emails
2. **Extraction des données** : Parsing des informations (from, subject, body)
3. **Classification IA** : Analyse avec Hugging Face (bart-large-mnli)
4. **Structuration** : Organisation des résultats avec score de confiance

### Catégories de classification
- Support technique
- Question commerciale
- Demande d'information
- Spam
- Urgence

## Installation

### Prérequis
- Docker installé
- Compte Gmail avec API activée
- Compte Hugging Face (gratuit)

### Configuration

1. **Cloner le repository**
```bash
git clone https://github.com/alasnier/agentia_support_client_email.git
cd agentia_support_client_email
```

2. **Démarrer n8n avec Docker**
```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

3. **Importer le workflow**
- Ouvrir n8n : http://localhost:5678
- Aller dans Workflows > Import from File
- Sélectionner `workflows/gmail-support-classification.json`

4. **Configurer les credentials**
Voir `docs/README.md` pour les instructions détaillées

## État du projet

### ✅ Complété
- [x] Configuration Gmail API + OAuth2
- [x] Lecture des emails entrants
- [x] Extraction et parsing des données
- [x] Classification IA avec Hugging Face
- [x] Calcul du score de confiance

### 🚧 En cours
- [ ] Routage selon catégorie (IF/Switch)
- [ ] Génération de réponses automatiques
- [ ] Envoi de réponses via Gmail

### 📋 À faire
- [ ] Gestion des pièces jointes
- [ ] Interface de monitoring
- [ ] Tests unitaires

## Technologies utilisées

- **n8n** : Orchestration (self-hosted via Docker)
- **Gmail API** : Gestion des emails
- **Hugging Face** : Classification IA (facebook/bart-large-mnli)
- **GitHub** : Versioning et collaboration

## Licence

MIT

## Auteur

Alex LASNIER