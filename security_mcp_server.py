import html
import json
import re
from typing import Dict, Any, List
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="SecurityGuard")

# ============================================================================
# CONFIGURATION DE SÉCURITÉ
# ============================================================================

# Liste blanche des domaines de confiance
TRUSTED_DOMAINS = {
    "google.com",
    "github.com",
    "stackoverflow.com",
    "linkedin.com",
    # Ajoutez vos domaines de confiance ici
}

# Liste blanche des expéditeurs de confiance (emails complets ou domaines)
TRUSTED_SENDERS = {
    "@yourcompany.com",  # Tous les emails de votre entreprise
    "noreply@github.com",
    "support@stripe.com",
    # Ajoutez vos expéditeurs de confiance ici
}

# Patterns dangereux à détecter
DANGEROUS_PATTERNS = [
    r'javascript:',
    r'data:text/html',
    r'<script',
    r'onclick=',
    r'onerror=',
    r'onload=',
    r'eval\(',
    r'document\.cookie',
    r'window\.location',
]

# Extensions de fichiers autorisées (par défaut)
ALLOWED_FILE_EXTENSIONS = {'.txt', '.csv', '.json', '.png', '.jpg', '.jpeg', '.gif'}

# Extensions dangereuses (toujours bloquées)
DANGEROUS_FILE_EXTENSIONS = {'.exe', '.bat', '.cmd', '.sh', '.ps1', '.vbs', '.js', '.jar'}


# ============================================================================
# FONCTIONS DE NETTOYAGE ET VALIDATION
# ============================================================================

def is_sender_trusted(sender_email: str) -> bool:
    """Vérifie si l'expéditeur est dans la liste blanche."""
    sender_email = sender_email.lower()

    # Vérifier email exact
    if sender_email in TRUSTED_SENDERS:
        return True

    # Vérifier domaine
    for trusted in TRUSTED_SENDERS:
        if trusted.startswith('@') and sender_email.endswith(trusted):
            return True

    return False


def extract_urls(text: str) -> List[str]:
    """Extrait toutes les URLs d'un texte."""
    # Pattern pour détecter les URLs
    url_pattern = r'https?://[^\s<>"\']+|www\.[^\s<>"\']+'
    urls = re.findall(url_pattern, text)
    return urls


def is_url_safe(url: str) -> bool:
    """Vérifie si une URL est sûre."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        # Vérifier si le domaine est dans la liste blanche
        for trusted_domain in TRUSTED_DOMAINS:
            if domain == trusted_domain or domain.endswith('.' + trusted_domain):
                return True

        return False
    except:
        return False


def sanitize_html(html_content: str) -> str:
    """
    Nettoie le contenu HTML en supprimant les éléments dangereux.
    Retourne du texte brut sans HTML.
    """
    if not html_content:
        return ""

    try:
        # Parser le HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Supprimer tous les scripts
        for script in soup.find_all('script'):
            script.decompose()

        # Supprimer tous les styles
        for style in soup.find_all('style'):
            style.decompose()

        # Supprimer les iframes
        for iframe in soup.find_all('iframe'):
            iframe.decompose()

        # Supprimer les objets et embeds
        for obj in soup.find_all(['object', 'embed']):
            obj.decompose()

        # Supprimer les attributs dangereux de tous les tags
        for tag in soup.find_all(True):
            # Liste des attributs à supprimer
            dangerous_attrs = ['onclick', 'onload', 'onerror', 'onmouseover',
                               'onfocus', 'onblur', 'onchange', 'onsubmit']
            for attr in dangerous_attrs:
                if attr in tag.attrs:
                    del tag.attrs[attr]

        # Convertir en texte brut
        text = soup.get_text(separator='\n', strip=True)

        # Nettoyer les espaces multiples
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' +', ' ', text)

        return text.strip()

    except Exception as e:
        # En cas d'erreur, retourner une chaîne vide par sécurité
        return f"[Error sanitizing HTML: {str(e)}]"


def remove_invisible_text(text: str) -> str:
    """Supprime les caractères invisibles et les polices cachées."""
    if not text:
        return ""

    # Supprimer les caractères de contrôle Unicode (sauf \n, \r, \t)
    text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F-\x9F]', '', text)

    # Supprimer les caractères Unicode invisibles
    invisible_chars = [
        '\u200B',  # Zero-width space
        '\u200C',  # Zero-width non-joiner
        '\u200D',  # Zero-width joiner
        '\uFEFF',  # Zero-width no-break space
        '\u2060',  # Word joiner
    ]
    for char in invisible_chars:
        text = text.replace(char, '')

    return text


def check_dangerous_patterns(text: str) -> List[str]:
    """Détecte les patterns dangereux dans le texte."""
    found_patterns = []

    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            found_patterns.append(pattern)

    return found_patterns


def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Nettoie les métadonnées en supprimant les informations sensibles."""
    safe_metadata = {}

    # Liste des champs autorisés
    allowed_fields = {'id', 'threadId', 'from', 'to', 'subject', 'date', 'snippet'}

    for key, value in metadata.items():
        if key in allowed_fields:
            if isinstance(value, str):
                # Nettoyer la valeur
                value = remove_invisible_text(value)
                value = html.unescape(value)
            safe_metadata[key] = value

    return safe_metadata


def analyze_attachments(attachments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyse les pièces jointes et détermine lesquelles sont sûres.

    Args:
        attachments: Liste des pièces jointes avec {filename, mimeType, size}

    Returns:
        Dict avec safe_attachments et dangerous_attachments
    """
    safe = []
    dangerous = []

    for attachment in attachments:
        filename = attachment.get('filename', '').lower()
        mime_type = attachment.get('mimeType', '').lower()

        # Extraire l'extension
        ext = '.' + filename.split('.')[-1] if '.' in filename else ''

        # Vérifier si l'extension est dangereuse
        if ext in DANGEROUS_FILE_EXTENSIONS:
            dangerous.append({
                **attachment,
                'reason': 'Dangerous file extension',
                'risk': 'HIGH'
            })
            continue

        # Vérifier si c'est un PDF (nécessite liste blanche)
        if ext == '.pdf' or 'pdf' in mime_type:
            dangerous.append({
                **attachment,
                'reason': 'PDF requires trusted sender',
                'risk': 'MEDIUM'
            })
            continue

        # Vérifier la taille (bloquer les fichiers > 25MB)
        size = attachment.get('size', 0)
        if size > 25 * 1024 * 1024:
            dangerous.append({
                **attachment,
                'reason': 'File too large',
                'risk': 'LOW'
            })
            continue

        # Si on arrive ici, la pièce jointe semble sûre
        if ext in ALLOWED_FILE_EXTENSIONS:
            safe.append(attachment)
        else:
            # Extension inconnue = à vérifier manuellement
            dangerous.append({
                **attachment,
                'reason': 'Unknown file type',
                'risk': 'MEDIUM'
            })

    return {
        'safe_attachments': safe,
        'dangerous_attachments': dangerous,
        'total_safe': len(safe),
        'total_dangerous': len(dangerous)
    }


# ============================================================================
# OUTILS MCP
# ============================================================================

@mcp.tool()
async def scan_email_security(
        sender: str,
        body_text: str,
        body_html: str = "",
        metadata: Dict[str, Any] = None,
        attachments: List[Dict[str, Any]] = None
) -> str:
    """
    Analyse complète de sécurité d'un email.

    Args:
        sender: Adresse email de l'expéditeur
        body_text: Corps de l'email en texte brut
        body_html: Corps de l'email en HTML (optionnel)
        metadata: Métadonnées de l'email
        attachments: Liste des pièces jointes

    Returns:
        JSON string avec le rapport de sécurité complet
    """
    report = {
        'sender': sender,
        'is_sender_trusted': is_sender_trusted(sender),
        'security_level': 'SAFE',  # SAFE, WARNING, DANGER
        'issues': [],
        'sanitized_content': {},
        'urls': {},
        'attachments': {},
        'recommendations': []
    }

    # 1. Vérifier l'expéditeur
    if not report['is_sender_trusted']:
        report['issues'].append({
            'type': 'UNTRUSTED_SENDER',
            'severity': 'MEDIUM',
            'message': f"Sender {sender} is not in the trusted list"
        })
        report['security_level'] = 'WARNING'

    # 2. Nettoyer et analyser le contenu texte
    cleaned_text = remove_invisible_text(body_text)
    dangerous_patterns = check_dangerous_patterns(cleaned_text)

    if dangerous_patterns:
        report['issues'].append({
            'type': 'DANGEROUS_PATTERNS',
            'severity': 'HIGH',
            'patterns': dangerous_patterns,
            'message': f"Detected {len(dangerous_patterns)} dangerous patterns"
        })
        report['security_level'] = 'DANGER'

    report['sanitized_content']['text'] = cleaned_text

    # 3. Nettoyer le HTML si présent
    if body_html:
        cleaned_html = sanitize_html(body_html)
        report['sanitized_content']['html_as_text'] = cleaned_html

    # 4. Analyser les URLs
    urls = extract_urls(cleaned_text)
    if body_html:
        urls.extend(extract_urls(body_html))

    urls = list(set(urls))  # Dédupliquer

    safe_urls = []
    dangerous_urls = []

    for url in urls:
        if is_url_safe(url):
            safe_urls.append(url)
        else:
            dangerous_urls.append(url)

    report['urls'] = {
        'total': len(urls),
        'safe': safe_urls,
        'dangerous': dangerous_urls,
        'safe_count': len(safe_urls),
        'dangerous_count': len(dangerous_urls)
    }

    # Si des URLs dangereuses et expéditeur non fiable
    if dangerous_urls and not report['is_sender_trusted']:
        report['issues'].append({
            'type': 'DANGEROUS_URLS',
            'severity': 'HIGH',
            'count': len(dangerous_urls),
            'message': f"Found {len(dangerous_urls)} untrusted URLs"
        })
        if report['security_level'] != 'DANGER':
            report['security_level'] = 'WARNING'

    # 5. Analyser les pièces jointes
    if attachments:
        attachment_analysis = analyze_attachments(attachments)
        report['attachments'] = attachment_analysis

        if attachment_analysis['total_dangerous'] > 0:
            # Si expéditeur non fiable + pièces jointes dangereuses
            if not report['is_sender_trusted']:
                report['issues'].append({
                    'type': 'DANGEROUS_ATTACHMENTS',
                    'severity': 'HIGH',
                    'count': attachment_analysis['total_dangerous'],
                    'message': f"{attachment_analysis['total_dangerous']} dangerous attachments from untrusted sender"
                })
                report['security_level'] = 'DANGER'
            else:
                report['issues'].append({
                    'type': 'ATTACHMENTS_REVIEW',
                    'severity': 'LOW',
                    'count': attachment_analysis['total_dangerous'],
                    'message': f"{attachment_analysis['total_dangerous']} attachments need review (trusted sender)"
                })

    # 6. Nettoyer les métadonnées
    if metadata:
        report['sanitized_content']['metadata'] = sanitize_metadata(metadata)

    # 7. Générer des recommandations
    if report['security_level'] == 'DANGER':
        report['recommendations'].append("⛔ DO NOT interact with this email")
        report['recommendations'].append("🚫 DO NOT click any links")
        report['recommendations'].append("🚫 DO NOT open attachments")
        report['recommendations'].append("🗑️ Consider marking as spam")
    elif report['security_level'] == 'WARNING':
        report['recommendations'].append("⚠️ Exercise caution with this email")
        if dangerous_urls:
            report['recommendations'].append("🔗 Verify URLs before clicking")
        if attachments:
            report['recommendations'].append("📎 Scan attachments before opening")
        report['recommendations'].append("👤 Verify sender identity")
    else:
        report['recommendations'].append("✅ Email appears safe")
        if not report['is_sender_trusted']:
            report['recommendations'].append("ℹ️ Sender not in trusted list (consider adding)")

    # 8. Calculer un score de sécurité (0-100, 100 = très sûr)
    security_score = 100

    if not report['is_sender_trusted']:
        security_score -= 20

    security_score -= len(dangerous_patterns) * 15
    security_score -= len(dangerous_urls) * 10

    if attachments:
        security_score -= attachment_analysis['total_dangerous'] * 15

    report['security_score'] = max(0, security_score)

    return json.dumps(report, indent=2)


@mcp.tool()
async def sanitize_email_content(
        body_text: str,
        body_html: str = ""
) -> str:
    """
    Nettoie le contenu d'un email (texte et HTML).
    Retourne uniquement du texte brut nettoyé.

    Args:
        body_text: Corps en texte brut
        body_html: Corps en HTML

    Returns:
        JSON string avec le contenu nettoyé
    """
    result = {
        'cleaned_text': '',
        'cleaned_html_as_text': '',
        'removed_invisible_chars': False,
        'removed_html_tags': False
    }

    # Nettoyer le texte
    if body_text:
        original_len = len(body_text)
        cleaned = remove_invisible_text(body_text)
        result['cleaned_text'] = cleaned
        result['removed_invisible_chars'] = len(cleaned) < original_len

    # Nettoyer le HTML
    if body_html:
        cleaned_html = sanitize_html(body_html)
        result['cleaned_html_as_text'] = cleaned_html
        result['removed_html_tags'] = True

    return json.dumps(result)


@mcp.tool()
async def add_trusted_sender(sender_email: str) -> str:
    """
    Ajoute un expéditeur à la liste blanche.
    Note: Dans cette version, c'est temporaire (mémoire).
    Pour une version persistante, utiliser une base de données.

    Args:
        sender_email: Email ou domaine à ajouter (@domain.com pour tout un domaine)

    Returns:
        JSON string avec confirmation
    """
    sender_email = sender_email.lower().strip()

    if sender_email not in TRUSTED_SENDERS:
        TRUSTED_SENDERS.add(sender_email)
        return json.dumps({
            'success': True,
            'message': f'Added {sender_email} to trusted senders',
            'total_trusted': len(TRUSTED_SENDERS)
        })
    else:
        return json.dumps({
            'success': False,
            'message': f'{sender_email} already in trusted list',
            'total_trusted': len(TRUSTED_SENDERS)
        })


@mcp.tool()
async def check_url_safety(url: str) -> str:
    """
    Vérifie si une URL est sûre.

    Args:
        url: URL à vérifier

    Returns:
        JSON string avec le résultat
    """
    is_safe = is_url_safe(url)

    try:
        parsed = urlparse(url)
        domain = parsed.netloc
    except:
        domain = "unknown"

    return json.dumps({
        'url': url,
        'is_safe': is_safe,
        'domain': domain,
        'in_whitelist': domain.lower() in TRUSTED_DOMAINS,
        'recommendation': 'Safe to visit' if is_safe else 'DO NOT visit - untrusted domain'
    })


if __name__ == "__main__":
    mcp.run()
