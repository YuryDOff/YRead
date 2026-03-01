"""
Регистрация приложения в Openverse и получение client_id / client_secret.
Токен затем автоматически обновляется бэкендом каждые ~9 ч (см. app.services.openverse_auth).

Использование (из каталога backend):
  python scripts/openverse_register.py your@email.com

Или без аргумента — будет запрошен email.
Учётные данные дописываются в backend/.env (OPENVERSE_CLIENT_ID, OPENVERSE_CLIENT_SECRET).
Важно: подтвердите почту по ссылке из письма Openverse, иначе лимиты останутся анонимными.
"""
import os
import re
import sys

import httpx

# Корень backend при запуске из backend/
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BACKEND_DIR, ".env")
REGISTER_URL = "https://api.openverse.org/v1/auth_tokens/register/"
TOKEN_URL = "https://api.openverse.org/v1/auth_tokens/token/"


def register(email: str, name: str = "YRead Reference Search") -> tuple[str, str]:
    """Регистрация приложения. Возвращает (client_id, client_secret)."""
    body = {
        "name": name,
        "description": "Reference image search for book characters and locations in the YRead app.",
        "email": email,
    }
    with httpx.Client(timeout=15.0) as client:
        r = client.post(REGISTER_URL, json=body)
        r.raise_for_status()
        data = r.json()
    return data["client_id"], data["client_secret"]


def get_token(client_id: str, client_secret: str) -> tuple[str, int]:
    """Получить access token. Возвращает (access_token, expires_in)."""
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    with httpx.Client(timeout=15.0) as client:
        r = client.post(
            TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        body = r.json()
    return body["access_token"], int(body.get("expires_in", 36000))


def ensure_env_has_openverse(client_id: str, client_secret: str) -> None:
    """Дописать или обновить OPENVERSE_CLIENT_ID и OPENVERSE_CLIENT_SECRET в .env."""
    if not os.path.exists(ENV_PATH):
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.write("\n# Openverse (auto-added by scripts/openverse_register.py)\n")
            f.write(f"OPENVERSE_CLIENT_ID={client_id}\n")
            f.write(f"OPENVERSE_CLIENT_SECRET={client_secret}\n")
        print(f"Created {ENV_PATH} with OPENVERSE_CLIENT_ID and OPENVERSE_CLIENT_SECRET.")
        return

    with open(ENV_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    def set_var(text: str, name: str, value: str) -> str:
        pattern = re.compile(rf"^({re.escape(name)})=.*$", re.MULTILINE)
        if pattern.search(text):
            return pattern.sub(f"{name}={value}", text)
        if text.strip() and not text.endswith("\n"):
            text = text + "\n"
        return text + f"{name}={value}\n"

    content = set_var(content, "OPENVERSE_CLIENT_ID", client_id)
    content = set_var(content, "OPENVERSE_CLIENT_SECRET", client_secret)

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated {ENV_PATH}: OPENVERSE_CLIENT_ID and OPENVERSE_CLIENT_SECRET saved.")


def main():
    email = (sys.argv[1:] or [None])[0]
    if not email or "@" not in email:
        email = input("Enter email for Openverse registration: ").strip()
    if not email or "@" not in email:
        print("Invalid email. Exiting.")
        sys.exit(1)

    # Уникальное имя, чтобы избежать "registration with this name already exists"
    name = f"YRead Reference Search - {email}"
    print(f"Registering app: {name}")
    try:
        client_id, client_secret = register(email, name=name)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            try:
                err = e.response.json()
                if "name" in err and "already exists" in str(err.get("name", [])):
                    print("An app with a similar name is already registered. Using a unique name.")
                    name = f"YRead Reference Search {email}"
                    client_id, client_secret = register(email, name=name)
            except Exception:
                raise
        else:
            raise

    print("Registration OK. Saving credentials to backend/.env ...")
    ensure_env_has_openverse(client_id, client_secret)
    print("Credentials saved to: backend/.env")
    print("  OPENVERSE_CLIENT_ID=...")
    print("  OPENVERSE_CLIENT_SECRET=...")

    token, expires_in = get_token(client_id, client_secret)
    print(f"\nAccess token obtained (expires in {expires_in}s).")
    print("The backend will auto-refresh the token every ~9 hours. No need to set OPENVERSE_ACCESS_TOKEN.")
    print("Restart the backend to start using Openverse with the new credentials.")


if __name__ == "__main__":
    main()
