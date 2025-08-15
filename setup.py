from setuptools import setup, find_packages

setup(
    name="bestfriend",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Flask",
        "Flask-SQLAlchemy",
        "Flask-Login",
        "Flask-Limiter",
        "Flask-WTF",
        "Flask-Migrate",
        "gunicorn",
        "psycopg2-binary",
        "redis",
        "SQLAlchemy",
        "alembic",
        "pgvector",
        "faster-whisper",
        "requests",
        "cryptography",
        "bcrypt",
        "python-dotenv",
        "WTForms",
        "python-multipart",
        "rq",
        "Pillow",
    ],
    extras_require={
        "test": [
            "pytest",
            "pytest-cov",
            "pytest-flask",
        ],
    },
)
