import json
import sys

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="ResponseGenerator")

# Templates de réponses (inchangé)
RESPONSE_TEMPLATES = {
    "support technique": """Bonjour,

Nous avons bien reçu votre demande de support technique concernant : "{subject}".

Notre équipe technique va analyser votre demande et vous reviendra dans les plus brefs délais avec une solution.

Pour accélérer le traitement de votre demande, vous pouvez nous fournir :
- Une description détaillée du problème
- Des captures d'écran si applicable
- Les étapes pour reproduire le problème

Nous vous remercions de votre patience.

Cordialement,
L'équipe Support
""",

    "question commerciale": """Bonjour,

Merci pour votre intérêt concernant : "{subject}".

Un membre de notre équipe commerciale va prendre contact avec vous très prochainement pour discuter de vos besoins et vous proposer une solution adaptée.

En attendant, n'hésitez pas à consulter notre site web pour découvrir nos offres et services.

Cordialement,
L'équipe Commerciale
""",

    "demande information": """Bonjour,

Nous avons bien reçu votre demande d'information concernant : "{subject}".

Nous allons vous transmettre les informations demandées dans les meilleurs délais.

Pour toute question complémentaire, n'hésitez pas à nous contacter.

Cordialement,
L'équipe Service Client
""",

    "urgence": """Bonjour,

Nous avons bien reçu votre message URGENT concernant : "{subject}".

Votre demande a été marquée comme prioritaire et transférée immédiatement à notre équipe. Un membre va vous contacter dans les plus brefs délais.

Si votre situation nécessite une assistance immédiate, vous pouvez également nous contacter par téléphone au [VOTRE_NUMERO].

Cordialement,
L'équipe Support Prioritaire
""",

    "spam": None
}


@mcp.tool()
async def generate_response(
        category: str,
        subject: str,
        confidence: float,
        min_confidence: float = 0.5
) -> str:
    """Génère une réponse automatique basée sur la catégorie."""

    should_send_auto = False

    if category == "urgence":
        should_send_auto = True
    elif category == "spam":
        should_send_auto = False
    elif category == "support technique":
        should_send_auto = confidence > 0.7
    elif category == "question commerciale":
        should_send_auto = confidence > 0.6
    elif category == "demande information":
        should_send_auto = confidence > 0.8
    else:
        should_send_auto = confidence > min_confidence

    template = RESPONSE_TEMPLATES.get(category)

    if template is None:
        response_body = None
    else:
        response_body = template.format(subject=subject)

    if category == "urgence":
        priority = "critique"
    elif category == "support technique" and confidence > 0.7:
        priority = "haute"
    elif category == "spam":
        priority = "aucune"
    else:
        priority = "normale" if confidence > 0.5 else "basse"

    result = {
        "category": category,
        "response_body": response_body,
        "should_send_auto": should_send_auto,
        "priority": priority,
        "confidence": confidence,
        "action": determine_action(category, should_send_auto)
    }

    return json.dumps(result)


def determine_action(category: str, should_send: bool) -> str:
    """Détermine l'action recommandée."""
    if category == "spam":
        return "Mark as spam"
    elif category == "urgence":
        return "ALERT TEAM + Send auto-reply + Create high priority ticket"
    elif should_send:
        return f"Send auto-reply + Create ticket"
    else:
        return "Manual review required + Create ticket"


if __name__ == "__main__":
    mcp.run()