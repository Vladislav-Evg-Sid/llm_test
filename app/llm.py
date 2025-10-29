from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch


class LlamaChatbot:
    _instance = None
    _initialized = False

    def __init__(self, name="sberbank-ai/rugpt3small_based_on_gpt2"):
        if LlamaChatbot._initialized:
            return
        print("⚡ Загрузка ультра-лёгкой модели...")
        
        self.tokenizer = GPT2Tokenizer.from_pretrained(name)
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.model = GPT2LMHeadModel.from_pretrained(
            "sberbank-ai/rugpt3small_based_on_gpt2",
            torch_dtype=torch.float32
        )
        self.model.eval()
        print("✅ Ультра-лёгкая модель загружена!")
        LlamaChatbot._initialized = True

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = LlamaChatbot()
        return cls._instance
    
    def generate_response(self, user_input):
        inputs = self.tokenizer.encode(user_input, return_tensors="pt")
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.7,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response.replace(user_input, "").strip()

# # Example Usage
# if __name__ == "__main__":
#     test = input()
#     if test == "n":
#         exit(0)
#     print("start")
#     chatbot = LlamaChatbot()

#     user_input = "Привет. Расскажи мне про теорему Пифагора"
#     print(f"User: {user_input}")
#     response = chatbot.generate_response(user_input)
#     print(f"Bot: {response}")
#     print("----------------------")
#     print("Введи следующее сообщение:")
#     user_input = input()
#     response = chatbot.generate_response(user_input)
#     print(f"Bot: {response}")
#     print("----------------------")
