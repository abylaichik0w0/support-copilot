import argparse
import json
import sys
from app.models.schemas import TriageRequest, Message
from app.services.pipeline import run_triage


def main():
    parser = argparse.ArgumentParser(description="Grand Mobile Support Copilot Batch Inference")
    parser.add_argument("--in", dest="input_path", required=True, help="Path to input jsonl file")
    parser.add_argument("--out", dest="output_path", required=True, help="Path to output jsonl file")
    args = parser.parse_args()

    processed_count = 0

    with open(args.input_path, "r", encoding="utf-8") as fin, open(args.output_path, "w", encoding="utf-8") as fout:
        for line in fin:
            line_str = line.strip()
            if not line_str:
                continue

            item = json.loads(line_str)

            # Извлечение сообщений из формата обучающего/валидационного датасета
            raw_msgs = item.get("messages", [])
            messages = []
            
            for idx, m in enumerate(raw_msgs):
                attachments_count = item.get("images_count", 0) if idx == 0 else 0
                messages.append(
                    Message(
                        role=m.get("role", "player"),
                        text=m.get("text", ""),
                        attachments=attachments_count
                    )
                )

            # Если список messages пустой (например, аномальный тикет)
            if not messages:
                messages = [Message(role="player", text="", attachments=0)]

            req = TriageRequest(
                kind=item.get("kind", "complaint"),
                messages=messages
            )

            # Прогон через пайплайн
            res = run_triage(req)

            # Запись результата в формате jsonl
            fout.write(res.model_dump_json() + "\n")
            processed_count += 1

    print(f"Готово! Обработано тикетов: {processed_count}. Результат сохранен в {args.output_path}")


if __name__ == "__main__":
    main()