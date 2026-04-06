# Telegram bot для продажи подписок на 2 приватных канала

Готовый проект на `aiogram 3`, `SQLite`, `SQLAlchemy`, `APScheduler`.

## Что умеет

- показывает тарифы
- принимает оплату через Telegram Stars
- поддерживает оплату через CryptoBot / Crypto Pay
- активирует или продлевает подписку
- выдаёт одноразовые invite links в приватные каналы
- показывает профиль пользователя и его подписки
- даёт меню донатов
- снимает доступ после истечения срока подписки
- периодически проверяет зависшие платежи CryptoBot

## Важно перед запуском

1. Создай бота через `@BotFather`.
2. Для цифровых товаров внутри Telegram используй Telegram Stars.
3. Если нужен CryptoBot, создай приложение в `@CryptoBot` → `Crypto Pay` и получи `CRYPTO_PAY_TOKEN`.
4. Добавь бота администратором в оба приватных канала.
5. Дай права:
   - Invite Users via Link
   - Ban Users
6. Узнай `chat_id` обоих приватных каналов.
7. Скопируй `.env.example` в `.env` и заполни значения.

## Быстрый старт локально

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python run.py
```

## Запуск в Docker

```bash
cp .env.example .env
docker compose up --build -d
```

## Команды в боте

- `/start` — открыть главное меню
- `/my` — мои подписки
- `/profile` — мой профиль

## Новые переменные окружения

```env
DONATE_URL=
CRYPTO_PAY_TOKEN=
CRYPTO_PAY_BASE_URL=https://pay.crypt.bot/api
CRYPTO_PAY_ASSET=USDT
CRYPTO_USDT_PER_STAR=0.01
DONATE_XTR_AMOUNTS=100,250,500
DONATE_CRYPTO_AMOUNTS=5,10,25
CHECK_PENDING_CRYPTO_EVERY_MINUTES=3
```

## Как устроена оплата

### Telegram Stars
- бот создаёт invoice c `currency=XTR`
- после `successful_payment` активирует подписку
- выдаёт ссылки на вход

### CryptoBot
- бот создаёт invoice через Crypto Pay API
- показывает кнопку на оплату
- пользователь может нажать `Проверить оплату`
- параллельно бот сам проверяет pending-платежи по расписанию
- после подтверждения активирует подписку и выдаёт доступ

## Донаты

В меню есть две точки входа для донатов:
- `⭐ Донат звёздами` — быстрая кнопка прямого доната в Telegram Stars
- `Донаты` — меню со Stars, CryptoBot и опциональной внешней ссылкой `DONATE_URL`

## Структура

```text
app/
  bot.py
  config.py
  db.py
  keyboards.py
  models.py
  seed.py
  handlers/
    payments.py
    start.py
    subscriptions.py
  services/
    channel_service.py
    order_service.py
    payment_service.py
    plan_service.py
    subscription_service.py
    user_service.py
  utils/
    text.py
run.py
```

## Примечания

- База по умолчанию — SQLite. Для production лучше перейти на PostgreSQL.
- Если пользователь не вступил по ссылке, revoke при истечении срока просто будет пропущен без ошибки.
- Инвайты одноразовые и имеют срок жизни, который задаётся в `.env`.
- При первом запуске проект автоматически добавляет недостающую колонку `payment_method` в таблицу `payments`.
