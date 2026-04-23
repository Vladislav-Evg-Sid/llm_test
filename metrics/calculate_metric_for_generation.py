from pathlib import Path
import re

from bert_score import score


GOLD_TEXT_PATH = Path("app/services/llm_service/texts/gold/2025/2.5.txt")
LLM_OUTPUT_DIR = Path("app/services/llm_service/texts/llm_output")


def compute_bertscore(candidate: str, reference: str, lang: str = "ru") -> dict[str, float]:
    """
    Вычисляет BERTScore (Precision, Recall, F1) для одной пары текстов.
    """
    precision, recall, f1 = score(
        [candidate],
        [reference],
        lang=lang,
        verbose=False,
    )

    return {
        "precision": precision.item(),
        "recall": recall.item(),
        "f1": f1.item(),
    }


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def parse_generated_file(path: Path) -> tuple[str, float | None]:
    raw_text = read_text(path)

    time_match = re.search(r"Time:\s*([0-9]+(?:\.[0-9]+)?)", raw_text)
    elapsed_time = float(time_match.group(1)) if time_match else None

    generated_text = re.sub(r"\n*Time:\s*[0-9]+(?:\.[0-9]+)?\s*$", "", raw_text).strip()
    generated_text = generated_text.strip('"')
    generated_text = generated_text.replace("<|end_of_turn|>", "").strip()

    return generated_text, elapsed_time


def collect_metrics() -> list[dict[str, str | float]]:
    reference_text = read_text(GOLD_TEXT_PATH)
    rows: list[dict[str, str | float]] = []

    for output_file in sorted(LLM_OUTPUT_DIR.glob("*.txt")):
        generated_text, elapsed_time = parse_generated_file(output_file)
        metrics = compute_bertscore(generated_text, reference_text)

        rows.append(
            {
                "model": output_file.stem,
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
                "time": elapsed_time if elapsed_time is not None else "N/A",
            }
        )

    return rows


def format_table(rows: list[dict[str, str | float]]) -> str:
    headers = ["model", "precision", "recall", "f1", "time"]
    formatted_rows = [
        [
            str(row["model"]),
            f"{row['precision']:.4f}",
            f"{row['recall']:.4f}",
            f"{row['f1']:.4f}",
            f"{row['time']:.3f}" if isinstance(row["time"], float) else str(row["time"]),
        ]
        for row in rows
    ]

    column_widths = []
    for index, header in enumerate(headers):
        max_width = max([len(header), *[len(row[index]) for row in formatted_rows]])
        column_widths.append(max_width)

    header_line = " | ".join(
        header.ljust(column_widths[index]) for index, header in enumerate(headers)
    )
    separator_line = "-+-".join("-" * width for width in column_widths)
    row_lines = [
        " | ".join(value.ljust(column_widths[index]) for index, value in enumerate(row))
        for row in formatted_rows
    ]

    return "\n".join([header_line, separator_line, *row_lines])


def main() -> None:
    rows = collect_metrics()
    print(format_table(rows))


if __name__ == "__main__":
    main()
