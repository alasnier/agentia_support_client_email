from mcp_server import MCPServer
from transformers import pipeline


class ClassificationMCPServer(MCPServer):
    def __init__(self):
        self.classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")

    def on_request(self, data):
        email_text = data.get("text")
        categories = ["support technique", "question commerciale", "demande information", "spam", "urgence"]
        result = self.classifier(email_text, categories)
        self.send_response({'category': result['labels'][0], 'confidence': result['scores'][0]})


server = ClassificationMCPServer()
server.start()
