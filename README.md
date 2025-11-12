# Agentia Support Client Email - Agent IA Autonome

## 🎯 Description

Système d'automatisation intelligent pour la gestion des emails de support client avec **deux implémentations** :
1. **n8n** : Workflow visuel no-code/low-code
2. **MCP (Model Context Protocol)** : Architecture d'agents Python modulaires avec sécurité renforcée

### Technologies clés
- **Gmail API** : Réception et envoi d'emails
- **Hugging Face** : Classification IA gratuite (facebook/bart-large-mnli)
- **n8n** : Orchestration visuelle (Docker)
- **MCP** : Protocole d'agents modulaires
- **Streamlit** : Interface utilisateur web
- **BeautifulSoup** : Sanitisation HTML et sécurité

---

## 🏗️ Architecture

### Version 1 : Workflow n8n (No-code)
```
Gmail Trigger 
  → Code (extraction) 
    → HTTP Request (classification HuggingFace)
      → Code (structuration résultats)
        → Switch (routage)
          ├─→ Réponse Support Technique
          ├─→ Réponse Commerciale
          ├─→ Réponse Information
          ├─→ Traitement Spam
          └─→ Réponse Urgence
```

**Workflow principal : Classification et routage des emails**
1. **Gmail Trigger** : Détection des nouveaux emails (polling toutes les minutes)
2. **Extraction des données** : Parsing (from, to, subject, body, date)
3. **Classification IA** : Analyse avec Hugging Face API (bart-large-mnli)
4. **Routage intelligent** : Switch selon la catégorie détectée
5. **Génération de réponse** : Templates personnalisés par catégorie

### Version 2 : Architecture MCP (Agents Python avec Sécurité)
```
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrateur Principal                   │
│                 (mcp_agent_orchestrator.py)                  │
└─────────────────────────────────────────────────────────────┘
         │            │              │            │          │
         ▼            ▼              ▼            ▼          ▼
    ┌────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  ┌──────────┐
    │ Gmail  │  │Classifier│  │Response  │  │ Gmail  │  │ Security │
    │ Reader │  │  Engine  │  │Generator │  │ Sender │  │  Guard   │
    │  MCP   │  │   MCP    │  │   MCP    │  │  MCP   │  │   MCP    │
    └────────┘  └──────────┘  └──────────┘  └────────┘  └──────────┘
```

**Serveurs MCP modulaires** :
- `gmail_mcp_server.py` : Lecture des emails Gmail
- `classification_mcp_server.py` : Classification IA (Hugging Face local)
- `response_generator_mcp_server.py` : Génération de réponses contextuelles
- `gmail_sender_mcp_server.py` : Envoi d'emails et réponses
- `security_mcp_server.py` : 🔒 Module de sécurité (NOUVEAU)

**Interfaces** :
- `mcp_agent_orchestrator.py` : CLI avec arguments
- `streamlit_ui.py` : Interface web interactive

---

## 🔒 Fonctionnalités de Sécurité

### Module Security Guard

✅ **Liste blanche d'expéditeurs** - Validation des expéditeurs de confiance  
✅ **Validation des URLs** - Blocage des liens non fiables  
✅ **Nettoyage HTML** - Suppression scripts, styles, iframes dangereux  
✅ **Détection de patterns dangereux** - JavaScript, eval(), cookies  
✅ **Analyse des pièces jointes** - Blocage PDF et fichiers exécutables  
✅ **Suppression caractères invisibles** - Zero-width chars, polices cachées  
✅ **Nettoyage métadonnées** - Conservation uniquement des champs sûrs  
✅ **Score de sécurité** - 0-100 pour chaque email  
✅ **Blocage automatique** - Les emails dangereux ne sont pas traités

### Niveaux de Sécurité

| Niveau | Score | Action |
|--------|-------|--------|
| 🟢 **SAFE** | 80-100 | Traitement normal |
| 🟡 **WARNING** | 40-79 | Traitement avec précaution |
| 🔴 **DANGER** | 0-39 | Blocage automatique |

---

## 📊 Catégories de classification

| Catégorie | Confiance min | Action auto | Priorité |
|-----------|---------------|-------------|----------|
| **Support technique** | 70% | Auto-reply + Ticket | Haute |
| **Question commerciale** | 60% | Forward sales | Normale |
| **Demande information** | 80% | Send info pack | Basse |
| **Spam** | N/A | Mark as spam | Aucune |
| **Urgence** | N/A | ALERT + Auto-reply | Critique |
| **BLOCKED** (sécurité) | N/A | Blocage | Blocked |

---

## 🚀 Installation

### Prérequis

- **Python 3.10+**
- **Docker** (pour n8n)
- **Compte Gmail** avec API activée
- **Compte Hugging Face** (gratuit)
- **Google Cloud Console** projet configuré

### 1. Cloner le repository
```bash
git clone https://github.com/alasnier/agentia_support_client_email.git
cd agentia_support_client_email
```

### 2. Installer les dépendances Python
```bash
# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les packages
pip install -r requirements.txt
```

**Contenu de `requirements.txt`** :
```txt
mcp
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
transformers
torch
streamlit
beautifulsoup4
lxml
```

### 3. Configuration Gmail API

#### A. Créer un projet Google Cloud

1. Aller sur [Google Cloud Console](https://console.cloud.google.com/)
2. Créer un projet : `agentia-support-client-email`
3. Activer **Gmail API**

#### B. Configurer OAuth2

1. **APIs & Services** > **OAuth consent screen**
   - Type : External (ou Internal si Google Workspace)
   - App name : `Agentia Support Client Email`
   - User support email : Votre email
   - Developer contact : Votre email
   - Scopes requis :
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/gmail.send`
     - `https://www.googleapis.com/auth/gmail.modify`

2. **Credentials** > **Create OAuth client ID**
   - Type : Desktop application
   - Name : `n8n Gmail Integration` (ou autre)
   - Télécharger le fichier JSON
   - **Renommer en `credentials.json`**
   - **Placer à la racine du projet**

#### C. Générer le token d'authentification

**Créer `quickstart.py`** :
```python
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Si vous modifiez ces scopes, supprimez token.json
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify'
]

def main():
    """Authentifie l'utilisateur et génère token.json"""
    creds = None
    
    # Le fichier token.json stocke les tokens d'accès et de rafraîchissement
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Si pas de credentials valides, demander à l'utilisateur de se connecter
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                print("✅ Token refreshed successfully!")
            except Exception as e:
                print(f"❌ Failed to refresh token: {e}")
                print("🔄 Starting new authentication flow...")
                creds = None
        
        if not creds:
            if not os.path.exists('credentials.json'):
                print("❌ Error: credentials.json not found!")
                print("📥 Please download it from Google Cloud Console:")
                print("   1. Go to https://console.cloud.google.com/")
                print("   2. Select your project: agentia-support-client-email")
                print("   3. Go to APIs & Services > Credentials")
                print("   4. Download your OAuth 2.0 Client ID as 'credentials.json'")
                return
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            print("✅ Authentication successful!")
        
        # Sauvegarder les credentials pour la prochaine fois
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("✅ Token saved to token.json")
    
    # Tester la connexion
    try:
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        
        print("\n✅ Gmail API connection successful!")
        print(f"📧 Found {len(labels)} labels in your Gmail account")
        print("\n🎉 You're all set! You can now run:")
        print("   python mcp_agent_orchestrator.py --max-emails 5")
        
    except Exception as e:
        print(f"❌ Error testing Gmail connection: {e}")

if __name__ == '__main__':
    main()
```

**Exécuter l'authentification** :
```bash
python quickstart.py
```

Cela va :
1. Ouvrir votre navigateur
2. Vous demander de vous connecter à Gmail
3. Demander les permissions
4. Générer `token.json` (ne pas commiter ce fichier !)

### 4A. Installation n8n (Version workflow)
```bash
# Démarrer n8n avec Docker
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n
```

**Importer le workflow** :
1. Ouvrir http://localhost:5678
2. Workflows > Import from File
3. Sélectionner `workflows/gmail-support-classification.json`
4. Configurer credentials Gmail et Hugging Face

### 4B. Installation MCP (Version agents)

Les serveurs MCP sont déjà prêts, aucune installation supplémentaire nécessaire.

---

## 🎮 Utilisation

### Option 1 : n8n (Interface visuelle)

1. Ouvrir n8n : http://localhost:5678
2. Activer le workflow
3. Tester avec **Execute Workflow**
4. Monitorer les exécutions dans l'historique

### Option 2 : CLI Python (Ligne de commande)
```bash
# Mode simulation avec sécurité (dry-run)
python mcp_agent_orchestrator.py --max-emails 10

# Avec auto-reply activé (simulation)
python mcp_agent_orchestrator.py --max-emails 10 --auto-reply

# Désactiver la sécurité (non recommandé)
python mcp_agent_orchestrator.py --max-emails 5 --no-security

# Envoyer réellement les emails (ATTENTION !)
python mcp_agent_orchestrator.py \
  --max-emails 5 \
  --auto-reply \
  --no-dry-run \
  --min-confidence 0.8
```

**Arguments disponibles** :
- `--max-emails N` : Nombre max d'emails à traiter
- `--auto-reply` : Activer les réponses automatiques
- `--no-dry-run` : Envoyer réellement (sans = simulation)
- `--min-confidence 0.X` : Seuil de confiance minimum (0-1)
- `--no-security` : Désactiver le scan de sécurité (non recommandé)

### Option 3 : Interface Streamlit (Web UI)
```bash
streamlit run streamlit_ui.py
```

**Fonctionnalités UI** :
- 📊 Configuration interactive (sliders, checkboxes)
- 🔒 Toggle sécurité avec détails
- 📧 Vue détaillée de chaque email
- 🎯 Métriques en temps réel
- 📝 Prévisualisation des réponses générées
- 🧪 Mode dry-run intégré
- 🔴 Badges de sécurité colorés (SAFE/WARNING/DANGER)
- 📈 Graphiques de répartition sécurité

---

## 📁 Structure du projet
```
agentia_support_client_email/
├── workflows/
│   └── gmail-support-classification.json    # Workflow n8n
├── credentials/
│   ├── credentials-template.json            # Template Google OAuth
│   ├── credentials.json                     # Vos credentials (gitignored)
│   └── token.json                           # Token OAuth (gitignored)
├── mcp_servers/                             # OU fichiers à la racine
│   ├── gmail_mcp_server.py                 # MCP Gmail reader
│   ├── classification_mcp_server.py        # MCP Classifier
│   ├── response_generator_mcp_server.py    # MCP Response gen
│   ├── gmail_sender_mcp_server.py          # MCP Gmail sender
│   └── security_mcp_server.py              # 🔒 MCP Security (NOUVEAU)
├── mcp_agent_orchestrator.py               # CLI orchestrator
├── streamlit_ui.py                          # Web interface
├── quickstart.py                            # OAuth authentication
├── requirements.txt                         # Python dependencies
├── .gitignore
└── README.md
```

---

## 🎯 État du projet

### ✅ Complété (n8n)
- [x] Configuration Gmail API + OAuth2
- [x] Lecture des emails entrants
- [x] Extraction et parsing des données
- [x] Classification IA avec Hugging Face API
- [x] Calcul du score de confiance
- [x] Routage selon catégorie (Switch)
- [x] Génération de réponses par catégorie
- [x] Templates de réponses personnalisés

### ✅ Complété (MCP)
- [x] Architecture modulaire avec serveurs MCP
- [x] Serveur Gmail reader (lecture emails)
- [x] Serveur Classification (Hugging Face local)
- [x] Serveur Response Generator (templates)
- [x] Serveur Gmail Sender (envoi emails)
- [x] **Serveur Security Guard (scan sécurité)** 🔒
- [x] Orchestrateur CLI avec arguments
- [x] Interface Streamlit interactive avec sécurité
- [x] Mode dry-run pour tests
- [x] Gestion du seuil de confiance
- [x] Réponses automatiques conditionnelles
- [x] **Blocage automatique emails dangereux**
- [x] **Validation URLs et expéditeurs**
- [x] **Sanitisation HTML complète**
- [x] **Analyse pièces jointes**

### 🚧 En cours
- [ ] Persistance liste blanche (base de données)
- [ ] Dashboard métriques temps réel
- [ ] Notifications Slack/Discord pour urgences
- [ ] Tests unitaires et intégration

### 📋 Backlog
- [ ] Support des pièces jointes (extraction contenu)
- [ ] Intégration CRM (HubSpot, Salesforce)
- [ ] A/B testing des templates
- [ ] Analytics avancées
- [ ] Multi-langue (détection auto)
- [ ] Fine-tuning du modèle de classification
- [ ] Déploiement cloud (AWS/GCP)
- [ ] API REST publique
- [ ] Détection phishing avancée
- [ ] Sandbox pour pièces jointes suspectes

---

## 🔧 Configuration avancée

### Personnaliser la liste blanche de sécurité

Éditez `security_mcp_server.py` :
```python
# Liste blanche des domaines de confiance
TRUSTED_DOMAINS = {
    "google.com",
    "github.com",
    "votre-entreprise.com",
    # Ajoutez vos domaines
}

# Liste blanche des expéditeurs
TRUSTED_SENDERS = {
    "@votre-entreprise.com",  # Tous les emails du domaine
    "partenaire@externe.com",  # Email spécifique
    # Ajoutez vos expéditeurs
}
```

### Personnaliser les templates de réponse

Éditez `response_generator_mcp_server.py`, section `RESPONSE_TEMPLATES` :
```python
RESPONSE_TEMPLATES = {
    "support technique": """Votre template personnalisé ici...""",
    # ...
}
```

### Ajuster les seuils de confiance

Dans `response_generator_mcp_server.py`, fonction `generate_response()` :
```python
if category == "support technique":
    should_send_auto = confidence > 0.7  # Modifier ici
elif category == "question commerciale":
    should_send_auto = confidence > 0.6  # Modifier ici
```

### Ajouter de nouvelles catégories

1. Modifier la liste dans `classification_mcp_server.py`
2. Ajouter le template dans `response_generator_mcp_server.py`
3. Mettre à jour le workflow n8n (ajouter une sortie au Switch)

---

## 🧪 Tests et validation

### Tester la classification seule
```bash
python -c "
import asyncio
from classification_mcp_server import classify_email

async def test():
    result = await classify_email('Mon serveur est en panne, urgent!')
    print(result)

asyncio.run(test())
"
```

### Tester le module de sécurité
```bash
python -c "
import asyncio
from security_mcp_server import scan_email_security

async def test():
    result = await scan_email_security(
        sender='unknown@suspicious.ru',
        body_text='Click here: http://malicious-site.com',
        body_html='<script>alert(1)</script>'
    )
    print(result)

asyncio.run(test())
"
```

### Tester l'envoi d'email
```bash
# Mode dry-run (ne pas envoyer vraiment)
python mcp_agent_orchestrator.py --max-emails 1 --auto-reply

# Vérifier les logs
```

### Benchmarks

| Métrique | n8n | MCP Python | MCP + Security |
|----------|-----|------------|----------------|
| Latence moyenne | ~5-8s | ~3-5s | ~4-6s |
| Emails/minute | ~10-15 | ~20-30 | ~15-25 |
| Consommation RAM | ~300MB | ~500MB* | ~600MB* |
| Taux blocage spam | N/A | N/A | ~95%** |

*Inclut le modèle Hugging Face en mémoire  
**Sur emails de test connus

---

## 🐛 Troubleshooting

### Erreur `token.json not found` ou `invalid_grant`
```bash
# Supprimer l'ancien token
rm token.json

# Régénérer
python quickstart.py
```

### Erreur `Failed to parse JSONRPC message`

**Cause** : Print statements dans les serveurs MCP interfèrent avec le protocole JSON-RPC.

**Solution** : Les serveurs ne doivent PAS utiliser `print()`. Utilisez `sys.stderr.write()` à la place :
```python
import sys
sys.stderr.write("Message de debug\n")
sys.stderr.flush()
```

### Modèle Hugging Face ne charge pas
```bash
# Télécharger manuellement
python -c "from transformers import pipeline; pipeline('zero-shot-classification', model='facebook/bart-large-mnli')"
```

### n8n ne se connecte pas à Gmail

Vérifier dans Google Cloud Console :
- API Gmail activée
- OAuth redirect URI : `http://localhost:5678/rest/oauth2-credential/callback`
- Scopes corrects ajoutés

### Emails bloqués par le module de sécurité
```bash
# Vérifier les logs de sécurité
python mcp_agent_orchestrator.py --max-emails 5 | grep "Security"

# Désactiver temporairement
python mcp_agent_orchestrator.py --max-emails 5 --no-security

# Ajouter l'expéditeur à la liste blanche
# Éditez security_mcp_server.py -> TRUSTED_SENDERS
```

### Token expire trop rapidement

Les tokens Gmail OAuth2 expirent après un certain temps. Pour prolonger :

1. Utiliser `refresh_token` (géré automatiquement par `quickstart.py`)
2. Si problème persiste, régénérer complètement :
```bash
rm token.json credentials.json
# Retélécharger credentials.json depuis Google Cloud
python quickstart.py
```

---

## 📚 Ressources

- [Documentation n8n](https://docs.n8n.io/)
- [Gmail API Guide](https://developers.google.com/gmail/api)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Hugging Face Models](https://huggingface.co/models)
- [Streamlit Docs](https://docs.streamlit.io/)
- [BeautifulSoup Docs](https://www.crummy.com/software/BeautifulSoup/)
- [Google OAuth2 Guide](https://developers.google.com/identity/protocols/oauth2)

---

## 🔐 Sécurité et Confidentialité

### Bonnes pratiques

✅ **Ne jamais commiter** :
- `credentials.json` (contient les secrets OAuth2)
- `token.json` (contient les tokens d'accès)
- Tout fichier contenant des clés API

✅ **Toujours utiliser** :
- Le module de sécurité en production
- Des listes blanches strictes
- Le mode dry-run pour tester

✅ **Rotation des tokens** :
- Régénérer `token.json` tous les 6 mois minimum
- Révoquer les anciens tokens dans Google Cloud Console

### Gestion des données

- Les emails sont traités **en mémoire** uniquement
- Aucune donnée n'est stockée par défaut
- Les logs peuvent contenir des aperçus d'emails (à nettoyer régulièrement)

---

## 📜 Licence

MIT License - voir [LICENSE](LICENSE) pour plus de détails

---

## 👤 Auteur

**Alex LASNIER**
- 📊 Data Scientist & 💡 Product Owner
- GitHub: [@alasnier](https://github.com/alasnier)
- LinkedIn: [Alex LASNIER](https://linkedin.com/in/alex-lasnier)

---

## 🙏 Remerciements

- [n8n.io](https://n8n.io/) pour l'outil d'orchestration
- [Hugging Face](https://huggingface.co/) pour les modèles IA gratuits
- [Anthropic](https://anthropic.com/) pour le protocole MCP
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) pour la sanitisation HTML
- Communauté open-source

---

## 📊 Statistiques du projet

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-MVP-orange.svg)
![Security](https://img.shields.io/badge/Security-Enhanced-brightgreen.svg)

**Version actuelle** : 2.0.0-mvp-secure  
**Dernière mise à jour** : Novembre 2025

---

## 🚦 Quick Start (TL;DR)
```bash
# 1. Cloner et installer
git clone https://github.com/alasnier/agentia_support_client_email.git
cd agentia_support_client_email
pip install -r requirements.txt

# 2. Configurer Gmail OAuth
# Télécharger credentials.json depuis Google Cloud Console
python quickstart.py

# 3. Tester (mode sécurisé + simulation)
python mcp_agent_orchestrator.py --max-emails 5

# 4. Utiliser l'interface web
streamlit run streamlit_ui.py
```

**C'est tout !** 🎉