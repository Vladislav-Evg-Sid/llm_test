from bert_score import score

def compute_bertscore(candidate: str, reference: str, lang: str = "ru"):
    """
    Вычисляет BERTScore (Precision, Recall, F1)

    :param candidate: сгенерированный текст
    :param reference: эталонный текст
    :param lang: язык ("ru", "en" и т.д.)
    :return: dict с precision, recall, f1
    """
    P, R, F1 = score(
        [candidate], 
        [reference], 
        lang=lang,
        verbose=False
    )

    return {
        "precision": P.item(),
        "recall": R.item(),
        "f1": F1.item()
    }

def get_gold_text(section_code: str) -> str:
    with open(f"app/services/llm_service/texts/gold/2025/{section_code}..txt", 'r', encoding='utf-8') as f:
        return f.read()

def get_generated_text(section_code: str) -> str:
    with open(f"app/services/llm_service/texts/llm_output/{section_code}..txt", 'r', encoding='utf-8') as f:
        text = f.read()
        return text.split("\n\nTime: ")[0]