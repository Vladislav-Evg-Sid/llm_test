from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")

# Для диалога:
chat_history_ids = None
if True:
    user_input = "Hi. Who is Pifaghor?"
    # user_input = input(">> User:")
    # if user_input.lower() == 'quit':
    #     break

    # Кодируем вход + историю
    inputs = tokenizer.encode(user_input + tokenizer.eos_token, return_tensors="pt")

    # Генерируем ответ
    outputs = model.generate(
        (
            inputs
            if chat_history_ids is None
            else torch.cat([chat_history_ids, inputs], dim=-1)
        ),
        max_length=1000,
        pad_token_id=tokenizer.eos_token_id,
        do_sample=True,
        temperature=0.7,
    )

    # Декодируем ответ
    response = tokenizer.decode(
        outputs[:, inputs.shape[-1] :][0], skip_special_tokens=True
    )
    print(f"Bot: {response}")

    # Обновляем историю
    chat_history_ids = outputs
