"""Простой потоковый анализатор журналов событий."""
import argparse
import csv
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path

LEVELS = {"TRACE", "DEBUG", "INFO", "WARN", "ERROR"}


def parse_line(line):
    """Возвращает запись или None, если строка повреждена."""
    parts = [part.strip() for part in line.rstrip("\n\r").split("|")]
    if len(parts) != 5 or any(not part for part in parts):
        raise ValueError("ожидалось 5 непустых полей, разделённых символом |")
    timestamp, level, source, code, message = parts
    if level not in LEVELS:
        raise ValueError(f"неверный уровень: {level}")
    try:
        when = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("неверная дата") from exc
    if when.tzinfo is None or when.utcoffset() != timezone.utc.utcoffset(when):
        raise ValueError("дата должна быть в UTC (ISO 8601 с Z или +00:00)")
    return {"timestamp": when.isoformat().replace("+00:00", "Z"),
            "level": level, "source": source, "eventCode": code, "message": message,
            "_when": when}


def matches_filters(event, start, end, level=None, source=None):
    """Проверяет фильтры события отдельно от парсинга и агрегации."""
    when = event["_when"]
    if start and when < start:
        return False
    if end and when >= end:
        return False
    if level and event["level"] != level:
        return False
    if source and event["source"] != source:
        return False
    return True


def aggregate_event(event, counts):
    """Добавляет одно прошедшее фильтры событие в сводные счётчики."""
    counts["matched_events"] += 1
    counts["levels"][event["level"]] += 1
    counts["sources"][event["source"]] += 1
    if event["level"] == "ERROR":
        counts["top_codes"][event["eventCode"]] += 1


def analyze(args):
    counts = {"total_lines": 0, "valid_lines": 0, "invalid_lines": 0,
              "matched_events": 0, "levels": Counter(), "sources": Counter(),
              "top_codes": Counter(), "errors": []}
    start = parse_bound(args.from_time, "--from")
    end = parse_bound(args.to_time, "--to")
    if start and end and start >= end:
        raise ValueError("--from должен быть раньше --to")
    path = Path(args.input)
    if not path.exists():
        raise FileNotFoundError(f"файл не найден: {path}")
    if not path.is_file():
        raise ValueError(f"это не файл: {path}")
    with path.open("r", encoding="utf-8") as file:
        for number, line in enumerate(file, 1):
            counts["total_lines"] += 1
            try:
                event = parse_line(line)
                counts["valid_lines"] += 1
            except ValueError as exc:
                counts["invalid_lines"] += 1
                counts["errors"].append({"line": number, "error": str(exc)})
                continue
            if matches_filters(event, start, end, args.level, args.source):
                aggregate_event(event, counts)
    result = {
        "input": str(path),
        "total_lines": counts["total_lines"],
        "valid_lines": counts["valid_lines"],
        "invalid_lines": counts["invalid_lines"],
        "matched_events": counts["matched_events"],
        "levels": dict(sorted(counts["levels"].items())),
        "sources": dict(sorted(counts["sources"].items())),
        "top_error_codes": [
            {"code": code, "count": count}
            for code, count in sorted(counts["top_codes"].items(),
                                      key=lambda item: (-item[1], item[0]))[:args.top]
        ],
        "invalid_rows": counts["errors"],
    }
    return result


def parse_bound(value, option):
    """Разбирает границу фильтра: ДД.ММ.ГГ или ISO 8601 UTC.

    Дата без времени означает начало указанного дня по UTC.
    Формат ISO оставлен для точных временных границ.
    """
    if value is None:
        return None
    try:
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"неверная дата для {option}: {value}; используйте ДД.ММ.ГГ") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError(f"{option}: используйте дату ДД.ММ.ГГ или ISO 8601 в UTC с Z")
    return parsed


def write_result(result, fmt, output):
    if output:
        target = open(output, "w", encoding="utf-8", newline="")
    else:
        target = None
    try:
        if fmt == "json":
            text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
            if target:
                target.write(text)
            else:
                print(text, end="")
        else:
            rows = [
                ("metric", "name", "count"),
                ("lines", "total", result["total_lines"]),
                ("lines", "valid", result["valid_lines"]),
                ("lines", "invalid", result["invalid_lines"]),
                ("events", "matched", result["matched_events"]),
            ]
            rows += [("level", k, v) for k, v in result["levels"].items()]
            rows += [("source", k, v) for k, v in result["sources"].items()]
            rows += [("top_error_code", item["code"], item["count"])
                     for item in result["top_error_codes"]]
            rows += [("invalid_row", str(item["line"]), item["error"])
                     for item in result["invalid_rows"]]
            out = target if target else __import__("sys").stdout
            writer = csv.writer(out)
            writer.writerows(rows)
    finally:
        if target:
            target.close()


def build_parser():
    parser = argparse.ArgumentParser(description="Потоковый анализатор журналов событий")
    parser.add_argument("--input", required=True, help="путь к файлу журнала")
    parser.add_argument("--from", dest="from_time", help="начало включительно: ДД.ММ.ГГ (например, 03.09.26) или ISO 8601 UTC")
    parser.add_argument("--to", dest="to_time", help="конец исключительно: ДД.ММ.ГГ (например, 05.09.26) или ISO 8601 UTC")
    parser.add_argument("--level", choices=sorted(LEVELS), help="уровень события")
    parser.add_argument("--source", help="источник события")
    parser.add_argument("--top", type=int, default=5, help="сколько кодов ошибок показать")
    parser.add_argument("--format", choices=["json", "csv"], default="json")
    parser.add_argument("--output", help="файл для сохранения отчёта")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.top < 0:
        parser.error("--top не может быть отрицательным")
    try:
        result = analyze(args)
        write_result(result, args.format, args.output)
    except (OSError, ValueError) as exc:
        print(f"Ошибка: {exc}", file=__import__("sys").stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
