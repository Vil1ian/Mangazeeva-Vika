# Анализатор журналов событий

## 1. Бизнес-требования
Службе поддержки нужно быстро находить частые ошибки и их источники в журнале, в том числе если файл большой или содержит испорченные строки.

## 2. Реализовано
- Python CLI, чтение журнала построчно (весь файл в память не загружается).
- Формат строки: `timestamp | level | source | eventCode | message`.
- Проверка пяти непустых полей, даты ISO 8601 в UTC и уровня `TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`.
- Фильтры `--from` (включительно), `--to` (исключительно), `--level`, `--source`.
- Подсчёт всех строк, корректных/ошибочных строк, событий после фильтрации, уровней и источников.
- Top-N кодов только для событий уровня `ERROR`; при равном количестве порядок по коду.
- Номера и причины повреждённых строк в отчёте.
- JSON и CSV, пустой файл, понятная ошибка для отсутствующего файла.
- Раздельные функции парсинга (`parse_line`), фильтрации (`matches_filters`), агрегации (`aggregate_event`), вывода и CLI.
- Тесты `unittest`, HTML-отчёт тестов и покрытия.

## 3. Требования
Python 3.10 или новее. Дополнительные пакеты нужны только для отчёта покрытия: `coverage`.

## 4. Установка в WSL
Откройте WSL и перейдите в папку проекта:
```bash
cd /путь/к/log_analyzer_project
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 5. Запуск
Примеры команд (выполняются из папки проекта):
```bash
python analyzer.py --input logs_events_sample.log
python analyzer.py --input logs_events_sample.log --level ERROR --top 10 --format json --output report.json
python analyzer.py --input logs_events_sample.log --from 03.09.26 --to 05.09.26 --source payment-worker --format csv --output report.csv
python analyzer.py --input logs_events_sample.log --level WARN --source auth-api --format csv
```

`--input` обязателен. Для `--from` и `--to` основной формат — `ДД.ММ.ГГ`, например `03.09.26`. Такая дата означает начало указанного дня по UTC (00:00:00). `--from` включает границу, `--to` не включает её: `--from 03.09.26 --to 05.09.26` охватывает 3 и 4 сентября 2026 года. Для точных временных границ также поддерживается ISO 8601 UTC, например `2026-09-03T12:30:00Z`. Формат входных временных меток в самом журнале остаётся ISO 8601 UTC согласно заданию. `--level` принимает TRACE/DEBUG/INFO/WARN/ERROR. `--top` по умолчанию 5. `--format` — `json` или `csv`, по умолчанию JSON. `--output` необязателен: без него отчёт печатается в терминал.

## 6. Тестирование одной командой
```bash
bash test.sh
```
Команда запускает тесты, создаёт текстовый и HTML-отчёт покрытия, а также HTML-отчёт тестов. Отчёты находятся в `htmlcov/index.html` и `test-report.html`. Метрика покрытия — покрытие строк исполняемого кода по `coverage.py`; исключение из подсчёта — блок `if __name__ == "__main__"`.

## 7. Результаты и отчёты
Пример отчёта для исходного файла журнала: `sample_report.json`. Поле `invalid_rows` перечисляет повреждённые строки с номерами. HTTP/API эндпоинтов нет: приложение запускается локально через CLI.

## 8. Структура проекта
- `analyzer.py` — парсер (`parse_line`), фильтр (`matches_filters`), агрегация (`aggregate_event`), вывод и CLI.
- `tests/test_analyzer.py` — автоматические тесты.
- `logs_events_sample.log` — предоставленный тестовый журнал.
- `requirements.txt` — зависимость отчёта покрытия.
- `test.sh` — единый запуск тестов и отчётов.
