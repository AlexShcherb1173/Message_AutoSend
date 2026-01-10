"""
db_env_check.py — вспомогательный диагностический скрипт для проверки окружения и подключения к PostgreSQL.

Назначение:
    • Выводит все переменные окружения, начинающиеся с префикса "PG".
    • Проверяет наличие не-ASCII символов в критичных переменных окружения,
      используемых для соединения с БД (DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT).
    • Пробует установить соединение с PostgreSQL с помощью psycopg2.
    • Полезен для диагностики проблем с кодировками, .env-файлом или передачей переменных в процесс.

Использование:
    python db_env_check.py

Требования:
    - Установленный пакет psycopg2.
    - Доступ к PostgreSQL по указанным параметрам (или переопределённым в .env).
"""

import os
import unicodedata

import psycopg2

# --- Шаг 1. Просмотр переменных окружения, связанных с PostgreSQL ---
print("PG* in process env:")
for key, value in sorted(os.environ.items()):
    if key.startswith("PG"):
        print(" ", key, "=>", repr(value))


def non_ascii(s: str):
    """
    Возвращает список всех не-ASCII символов в строке `s`.

    Args:
        s (str): Проверяемая строка.

    Returns:
        list[tuple[str, str, str]]:
            Каждый элемент — кортеж вида:
                (символ, шестнадцатеричный код, Unicode-имя)
            Пример: [('й', '0x439', 'CYRILLIC SMALL LETTER SHORT I')]

    Пример:
        >>> non_ascii("password123")
        []
        >>> non_ascii("пароль123")
        [('п', '0x43f', 'CYRILLIC SMALL LETTER PE'), ...]
    """
    return [(c, hex(ord(c)), unicodedata.name(c, "")) for c in s if ord(c) > 127]


# --- Шаг 2. Проверка критических переменных окружения на не-ASCII символы ---
print("\nCheck non-ASCII characters in critical DB vars:")
critical_vars = ("DB_NAME", "DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT")
for key in critical_vars:
    value = os.getenv(key, "")
    print(f"  {key:12} => {value!r}   bad: {non_ascii(value)}")


# --- Шаг 3. Попытка подключения к PostgreSQL ---
print("\nConnecting...")

# Удаляем все переменные PG*, чтобы psycopg2 не подменял параметры окружением.
for key in list(os.environ):
    if key.startswith("PG"):
        os.environ.pop(key, None)

try:
    # ⚙️ Параметры можно заменить на свои или брать из .env
    conn = psycopg2.connect(
        dbname="message_autosend",
        user="postgres",
        password="postgres",
        host="127.0.0.1",
        port=5432,
    )
    print("✅ Connection successful!")
except psycopg2.Error as e:
    print("❌ Connection failed:", e)
else:
    conn.close()
    print("✅ Connection closed cleanly.")
