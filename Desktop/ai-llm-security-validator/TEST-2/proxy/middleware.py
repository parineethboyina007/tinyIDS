from defense.firewall import ResponseValidationFirewall


class SecurityMiddleware:
    def __init__(self):
        self.firewall = ResponseValidationFirewall()

    def inspect_response(self, prompt: str, response: str, context=None):
        context = context or {}
        return self.firewall.inspect(response, context)