from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


class QwenChatbot:
    def __init__(self, model_name="Qwen/Qwen2.5-0.5B"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        # остальной код...


class QwenChatbot:
    def __init__(self, model_name="Qwen/Qwen3-0.6B"):
        # Добавьте параметры для безопасной загрузки
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            local_files_only=False,  # Принудительно скачать заново
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.float32,  # Для CPU используйте float32
            device_map="auto",  # Автоматическое распределение
        )
        self.history = []

    def generate_response(self, user_input):
        messages = self.history + [{"role": "user", "content": user_input}]

        text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        inputs = self.tokenizer(text, return_tensors="pt")

        # Для CPU лучше использовать меньший max_new_tokens
        response_ids = self.model.generate(
            **inputs,
            max_new_tokens=512,  # Уменьшите для CPU
            do_sample=True,
            temperature=0.7,
        )

        response = self.tokenizer.decode(
            response_ids[0][len(inputs.input_ids[0]) :], skip_special_tokens=True
        )

        # Update history
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": response})

        return response


# Example Usage
print("before test")
if __name__ == "__main__":
    print("start")
    chatbot = QwenChatbot()

    user_input_1 = "Привет. Расскажи мне про теорему Пифагора"
    print(f"User: {user_input_1}")
    response_1 = chatbot.generate_response(user_input_1)
    print(f"Bot: {response_1}")
    print("----------------------")
