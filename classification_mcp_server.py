import json
import sys
from typing import List

from mcp.server.fastmcp import FastMCP
from transformers import pipeline

mcp = FastMCP(name="EmailClassifier")

# Charger le modèle au démarrage (cache global)
# IMPORTANT: Ne pas utiliser print() - ça interfère avec le protocole MCP
# À la place, écrire dans stderr
sys.stderr.write("🔄 Loading classification model...\n")
sys.stderr.flush()

classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=-1)

sys.stderr.write("✅ Model loaded!\n")
sys.stderr.flush()


@mcp.tool()
async def classify_email(text: str, categories: List[str] = None) -> str:
    """
    Classifie un e-mail dans une catégorie métier.
    Retourne un JSON string avec la catégorie et le score de confiance.

    Args:
        text: Le texte de l'email à classifier
        categories: Liste optionnelle de catégories
    """
    if not categories:
        categories = [
            "support technique",
            "question commerciale",
            "demande information",
            "spam",
            "urgence",
        ]

    # Limiter la longueur du texte pour éviter les erreurs
    text_truncated = text[:512] if len(text) > 512 else text

    result = classifier(text_truncated, categories)

    output = {
        "category": result["labels"][0],
        "confidence": float(result["scores"][0]),
        "all_scores": {
            "labels": result["labels"],
            "scores": [float(s) for s in result["scores"]]
        }
    }

    # Retourner comme JSON string
    return json.dumps(output)


# Point d'entrée pour lancer le serveur
if __name__ == "__main__":
    mcp.run()
