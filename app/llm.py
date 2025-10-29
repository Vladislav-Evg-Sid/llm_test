from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


class LlamaChatbot:
    _instance = None
    _initialized = False

    def __init__(self, model_name="openlm-research/open_llama_3b_v2"):
        if LlamaChatbot._initialized:
            return

        # Для OpenLLaMA рекомендуется отключить fast tokenizer (use_fast=False)
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True,
            use_fast=False  # Важно для корректной токенизации в OpenLLaMA[citation:8]
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            trust_remote_code=True,
            torch_dtype=torch.float32,
            device_map="auto",
        )
        self.history = []
        LlamaChatbot._initialized = True

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = LlamaChatbot()
        return cls._instance

    def generate_response(self, user_input):
        # Форматируем историю диалога и новый запрос
        messages = self.history + [{"role": "user", "content": user_input}]
        
        # Создаем промт в формате, который понимает модель
        # Для OpenLLaMA можно использовать простой формат, например:
        # <s> Предыдущий вопрос </s> </s> Предыдущий ответ </s> </s> Новый вопрос </s> </s>
        formatted_prompt = ""
        for msg in messages:
            if msg["role"] == "user":
                formatted_prompt += f"<s> {msg['content']} </s>"
            else:
                formatted_prompt += f" </s> {msg['content']} </s>"
        
        # Добавляем тег для начала ответа модели
        formatted_prompt += " </s>"

        inputs = self.tokenizer(formatted_prompt, return_tensors="pt")

        # Генерация ответа
        with torch.no_grad():
            response_ids = self.model.generate(
                **inputs,
                max_new_tokens=256,
                do_sample=True,
                temperature=0.7,
                pad_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.1,
            )

        # Декодируем только сгенерированную часть
        response = self.tokenizer.decode(response_ids[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

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
