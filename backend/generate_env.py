"""
Generates a production-ready .env file with a strong, random JWT secret.

Run this ONCE on your deployment server (VPS), from the project root:
    python backend/generate_env.py

It will create backend/.env if one doesn't already exist. If .env already
exists, it will NOT overwrite it (to avoid accidentally rotating a secret
that's already in use — rotating it invalidates every logged-in user's
session).
"""
import os
import secrets

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(HERE, ".env")


def main():
    if os.path.exists(ENV_PATH):
        print(f"⚠️  {ENV_PATH} already exists — not overwriting.")
        print("    Delete it manually first if you really want to regenerate the secret")
        print("    (this will log out every currently-logged-in user).")
        return

    jwt_secret = secrets.token_hex(32)  # 64-character random hex string

    env_content = f"""APP_NAME=School Management System
DEBUG=False

DATABASE_URL=sqlite:///./school.db

JWT_SECRET={jwt_secret}
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

CORS_ORIGINS=*

LOG_FILE=logs/app.log
API_V1_PREFIX=/api/v1
"""

    with open(ENV_PATH, "w") as f:
        f.write(env_content)

    print(f"✅ Created {ENV_PATH} with a secure random JWT_SECRET.")
    print("   Keep this file private — never commit it to git (it's already in .gitignore).")


if __name__ == "__main__":
    main()
