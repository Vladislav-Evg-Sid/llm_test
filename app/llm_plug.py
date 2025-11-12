class LLMReportGenerator:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            print("Создание нового экземпляра:", end=" ")
            cls._instance = super().__new__(cls)
            print(cls._instance)
        else:
            print("Экземпляр уже существует: " + str(cls._instance))
        return cls._instance
    
    def __init__(self, model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        print("model: " + str(model_name))
        if not self._initialized:
            self._initialized = True
    
    def generate_response(self, user_input):
        return "ypur_text: " + user_input
