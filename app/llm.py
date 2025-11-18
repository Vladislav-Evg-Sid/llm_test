from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch


class LLMReportGenerator:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        if LLMReportGenerator._initialized:
            return
        # Загружаем токенизатор
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        # Устанавливаем pad_token если его нет
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Загружаем модель с оптимизациями для CPU
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            device_map="cpu",
            low_cpu_mem_usage=True,
            trust_remote_code=True
        )
        
        # Переводим в режим инференса
        self.model.eval()
        
        # Создаём пайплайн для упрощённой работы
        self.pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            torch_dtype=torch.float32,
            device="cpu"
        )
        
        self.history = []
        print("✅ Модель успешно загружена и готова к работе!")
        LLMReportGenerator._initialized = True
    
    def generate_response(self, user_input):
        try:
            # Формируем промт для чата
            if self.history:
                conversation = "\n".join([f"{'User' if i % 2 == 0 else 'Assistant'}: {msg['content']}" 
                                        for i, msg in enumerate(self.history[-4:])])  # Берём последние 4 сообщения
                prompt = f"{conversation}\nUser: {user_input}\nAssistant:"
            else:
                prompt = f"User: {user_input}\nAssistant:"
            
            # Генерируем ответ
            outputs = self.pipe(
                prompt,
                max_new_tokens=150,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.eos_token_id,
                num_return_sequences=1
            )
            
            # Извлекаем ответ
            full_text = outputs[0]['generated_text']
            response = full_text.replace(prompt, "").strip()
            
            # Очищаем ответ от лишнего
            if "\nUser:" in response:
                response = response.split("\nUser:")[0]
            
            # Обновляем историю
            self.history.append({"role": "user", "content": user_input})
            self.history.append({"role": "assistant", "content": response})
            
            # Ограничиваем историю
            if len(self.history) > 10:
                self.history = self.history[-10:]
                
            return response
            
        except Exception as e:
            return f"⚠️ Ошибка при генерации: {str(e)}"

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
