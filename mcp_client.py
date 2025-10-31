from mcp_client import MCPClient


class EmailProcessingClient(MCPClient):
    def on_data(self, data):
        email = data.get("email")
        category = self.classify_email(email)
        print(f"Email categorized as: {category}")
        self.handle_email(category, email)

    def classify_email(self, email):
        response = self.send_request({"text": email.get("body")})
        return response.get("category")


client = EmailProcessingClient()
client.connect_to("gmail_mcp_server")
client.connect_to("classification_mcp_server")
