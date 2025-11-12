class LlamaChatbot:
    def __init__(self, model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        print("model: " + model_name)

    def generate_response(self, user_input):
        return "ypur_text: " + user_input
