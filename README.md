# 🚀 SoftClub Support Bot

> **SoftClub Support Bot** — это асинхронный Telegram-бот на базе **Aiogram 3**, предназначенный для обработки обращений, вопросов и жалоб студентов учебного центра программирования **SoftClub**.

---

## 🛠 Технологический стек

| Компонент | Технология | Описание |
| :--- | :--- | :--- |
| **Language** | `Python 3.10+` | Основной язык разработки |
| **Framework** | `Aiogram 3.x` | Современная асинхронная библиотека для Telegram Bot API |
| **Database** | `PostgreSQL` | Надежная реляционная база данных |
| **DB Driver** | `asyncpg` | Высокопроизводительный асинхронный клиент для PostgreSQL |
| **Environment** | `python-dotenv` | Управление переменными окружения через `.env` файл |
| **State Management** | `FSM (Aiogram)` | Конечный автомат для обработки многошаговых диалогов |

---

## 🏗 Архитектура и структура проекта

- `main.py` — Точка входа, обработчики команд, FSM и маршрутизация хэндлеров
- `services.py` — Бизнес-логика и сервисные функции взаимодействия с БД
- `sql.py` — Подключение к PostgreSQL (pool) и миграции (создание таблиц)
- `buttons.py` — Модуль генерации клавиатур (InlineKeyboardMarkup)
- `.env` — Файл конфигурации и секретов (токен, параметры БД)
- `requirements.txt` — Список зависимостей проекта

### 📐 Схема базы данных (ER-diagram)

```text
  +-----------------------------------+       +-----------------------------------+
  |               users               |       |              tickets              |
  +-----------------------------------+       +-----------------------------------+
  | user_id (PK) : BIGINT             |<------| ticket_id (PK) : BIGSERIAL        |
  | name         : VARCHAR(255)       |  1  N | user_id (FK)   : BIGINT           |
  | role         : VARCHAR(20)        |-------| user_name      : VARCHAR(255)       |
  | created_at   : TIMESTAMPTZ        |       | question       : TEXT             |
  +-----------------------------------+       | status         : VARCHAR(20)      |
                                              | answer         : TEXT             |
                                              | admin_id       : BIGINT           |
                                              | created_at     : TIMESTAMPTZ      |
                                              | answered_at    : TIMESTAMPTZ      |
                                              +-----------------------------------+
