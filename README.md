# Quuuizer

Это простой Quiz бот, разработанный на Python через библиотеку `aiogram` с использованием асинхронного программирования.

Квиз содержит 10 вопросов по языку Python.

Команды бота:

1. `/start` - начать работу с ботом
2. `/quiz` - начать/перезапустить квиз
3. `/statistics` - показать статистику игроков

## Онлайн доступ

Какое-то время квиз бот будет доступен онлайн по следующей ссылке: [@QuuuizerBot](https://t.me/QuuuizerBot)

## Локальный запуск

Для локального запуска необходимо создать файл конфигурации в формате `toml`, где необходимо указать токен бота через которого будет работать квиз. Пример структуры и содержимого можно посмотреть в файле `example_config.toml`. Свой файл необходимо назвать либо `config.toml`, либо так, как хочется, но в таком случае нужно вверху файла `main.py` поменять содержимое константы `CONFIG_NAME`.

Далее установить зависимости и запустить проект можно двумя способами.

### Через менеджер uv

1. Установить менеджер **uv**
2. Открыть терминал в папке с проектом
3. Выполнить команду `uv sync`
4. Запустить проект с помощью команды `uv run main.py`

### Через обычный Python

1. Установить зависимости из `requirements.txt` используя `pip`
2. Запустить любым удобным способом через файл main.py
