from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


class LlamaChatbot:
    _instance = None
    _initialized = False
    
    def __init__(self, model_name="meta-llama/Llama-3.2-3B"):
        # Для Llama моделей обычно нужен trust_remote_code
        if LlamaChatbot._initialized: return
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.float32,  # Явно указываем float32 для CPU
            device_map="auto",  # Автоматическое распределение (важно для CPU)
        )
        self.history = []
    
    @classmethod
    def get_instance(cls):
        """Статический метод для получения единственного экземпляра"""
        if cls._instance is None:
            cls._instance = LlamaChatbot()
        return cls._instance

    def generate_response(self, user_input):
        messages = self.history + [{"role": "user", "content": user_input}]

        # Llama использует другой формат чата, поэтому лучше явно форматировать
        formatted_messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": msg["content"]}
            for i, msg in enumerate(
                self.history + [{"role": "user", "content": user_input}]
            )
        ]

        # Альтернативный способ форматирования для Llama
        text = self.tokenizer.apply_chat_template(
            formatted_messages, tokenize=False, add_generation_prompt=True
        )

        inputs = self.tokenizer(text, return_tensors="pt")

        # Настройки генерации для CPU
        response_ids = self.model.generate(
            **inputs,
            max_new_tokens=256,  # Еще меньше для 3B модели на CPU
            do_sample=True,
            temperature=0.7,
            pad_token_id=self.tokenizer.eos_token_id,  # Важно для Llama
            repetition_penalty=1.1,  # Помогает избежать повторений
        )

        response = self.tokenizer.decode(
            response_ids[0][len(inputs.input_ids[0]) :], skip_special_tokens=True
        )

        # Обновляем историю
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": response})

        return response


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
