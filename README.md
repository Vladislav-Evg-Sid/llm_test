# LLM Test

Проект запускается через Docker Compose и использует локальную GGUF-модель для `llama.cpp`.

## Загрузка модели

1. Найди GGUF-модель на Hugging Face или другом ресурсе.

2. Перейди в директорию для моделей на сервере:

   ```bash
   cd llm_app/models
   ```

   Если директории еще нет, создай ее:

   ```bash
   mkdir -p llm_app/models
   cd llm_app/models
   ```

3. Скачай модель:

   ```bash
   wget --header="Authorization: Bearer hf_ТВОЙ_ТОКЕН" "https://huggingface.co/URL_ДО_МОДЕЛИ.gguf"
   ```

   Для публичных моделей токен может быть не нужен:

   ```bash
   wget "https://huggingface.co/URL_ДО_МОДЕЛИ.gguf"
   ```

4. Если нужен токен Hugging Face:

   1. Открой Hugging Face.
   2. Перейди в `личный кабинет -> Settings -> Access Tokens -> Create`.
   3. Создай токен с правами `Read`.
   4. Введи название и сохрани токен.

   Токен показывается только один раз. После создания его нельзя будет посмотреть на сайте повторно.

5. Как получить URL до модели на Hugging Face:

   1. Открой страницу модели.
   2. Перейди во вкладку `Files and versions`.
   3. Нажми на файл модели с расширением `.gguf`.
   4. Скопируй URL из браузера.
   5. В URL замени `blob` на `resolve`.

   Пример:

   ```text
   https://huggingface.co/owner/model/blob/main/model.gguf
   ```

   Нужно заменить на:

   ```text
   https://huggingface.co/owner/model/resolve/main/model.gguf
   ```

6. Дождись скачивания модели.

7. В корневом `.env` поменяй `LLAMA_MODEL_FILE` на имя скачанного файла без пути:

   ```env
   LLAMA_MODEL_FILE=model.gguf
   ```

   Путь `llm_app/models` уже прописан в `docker-compose-server.yml`, поэтому указывать его в `.env` не нужно.

## Запуск

1. Проверь корневой `.env`: подключения к сервисам, порты и имя модели в `LLAMA_MODEL_FILE`.

2. Запусти проект:

   ```bash
   docker compose -f docker-compose-server.yml up
   ```

   Не добавляй `--build` к обычному запуску: сборка может занять очень много времени.

3. Если менял код приложения, пересобери только `web`:

   ```bash
   docker compose -f docker-compose-server.yml build web
   ```

   После этого снова запусти compose:

   ```bash
   docker compose -f docker-compose-server.yml up
   ```

4. Использование модели без системного промпта используй эндпоинт `textreports/generate`

## Проброс портов на сервер

Для доступа к эндпоинтам сервиса из браузера на ПК нужно подключиться к серверу с пробросом портов: `ssh user_name@id -L server_port:local_port`.

Для наших портов: `ssh user_name@id -L 8008:localhost:8008`