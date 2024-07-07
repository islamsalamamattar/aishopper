# Moonshine HomeChef

## Description

Cooking app offering personalized recipes, meal planning, and cooking tutorials based on users' dietary preferences and skill levels.


## Installation

#### clone repository
```bash
git clone https://github.com/islamsalamamattar/moonshine-homechef.git
```

#### create venv & install requirements
```bash
cd moonshine-homechef
pip install virtualenv
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### create postgres DB
```
psql -U postgres
```
```
CREATE DATABASE fastapidb;
CREATE USER dbadmin WITH PASSWORD 'dbpassword';
ALTER ROLE dbadmin SET client_encoding TO 'utf8';
ALTER ROLE dbadmin SET default_transaction_isolation TO 'read committed';
ALTER ROLE dbadmin SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE fastapidb TO dbadmin;
GRANT ALL PRIVILEGES ON SCHEMA public TO dbadmin;
\q
```

#### create a secret key for hashing passwords
```bash
openssl rand -hex 32
```

#### create .env to store enviroment variables
```bash
nano .env
```
```python
PROJECT_NAME="AI Shopper backend"
DATABASE_URL=postgresql+asyncpg://dbadmin:dbpassword@localhost:5432/fastapidb
debug_logs="log.txt"

SECRET_KEY = "725ec5caaa370a5a821b84346c7fb4b88146ee89046dab323562ee9d16bbbd36"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 180
REFRESH_TOKEN_EXPIRES_MINUTES = 43200

API_KEY = "sk-xxx
GROQ_API_KEY = "xxx"
```

#### Intiate alembic migrations and update script
```bash
alembic init app/alembic
cat env.py.example > app/alembic/env.py
```
#### Generate intial migration and upgrade head
```bash
alembic revision --autogenerate -m "Create User & BlackListToken Tables"
alembic upgrade head
```

#### Start the app
```
uvicorn app.main:app --reload --port 4567
```

### Access DB from server CLI
```
psql -U dbadmin -d fastapidb
```

## Project structure
```
moonshine-homechef
├─ app
│  ├─ __init__.py
│  ├─ agents
│  │  ├─ chatAgent
│  │  │  ├─ chains.py
│  │  │  ├─ prompt_templates.py
│  │  │  ├─ prompts.py
│  │  │  └─ tools.py
│  │  ├─ prompt_chains_old.py
│  │  └─ prompt_template_old.py
│  ├─ alembic
│  │  ├─ README
│  │  ├─ env.py
│  │  ├─ script.py.mako
│  │  └─ versions
│  ├─ core
│  │  ├─ __init__.py
│  │  ├─ config.py
│  │  ├─ database.py
│  │  ├─ exceptions.py
│  │  └─ jwt.py
│  ├─ llms
│  │  ├─ dalleApi.py
│  │  ├─ groqApi.py
│  │  └─ openaiApi.py
│  ├─ main.py
│  ├─ models
│  │  ├─ __init__.py
│  │  ├─ ingredient.py
│  │  ├─ instructions.py
│  │  ├─ interaction.py
│  │  ├─ jwt.py
│  │  ├─ profile.py
│  │  ├─ recipe.py
│  │  ├─ reply.json
│  │  ├─ tips_variations.py
│  │  └─ user.py
│  ├─ routers
│  │  ├─ __init__.py
│  │  ├─ auth.py
│  │  ├─ chat.py
│  │  ├─ profile.py
│  │  └─ recipe.py
│  ├─ schemas
│  │  ├─ chatcompletion.py
│  │  ├─ chatcompletionchunk.py
│  │  ├─ ingredient.py
│  │  ├─ jwt.py
│  │  ├─ mail.py
│  │  ├─ profile.py
│  │  ├─ prompt.py
│  │  ├─ recipe.py
│  │  └─ user.py
│  ├─ static
│  │  ├─ assets
│  │  │  ├─ css
│  │  │  ├─ img
│  │  │  ├─ js
│  │  │  ├─ less
│  │  │  ├─ plugins
│  │  │  └─ scss
│  │  ├─ recipies.json
│  │  └─ templates
│  └─ utils
│     ├─ __init__.py
│     ├─ appUtils.py
│     ├─ authUtils.py
│     ├─ extract_json.py
│     ├─ extract_json_recipe.py
│     ├─ hash.py
│     ├─ mail.py
│     ├─ save_recipe.py
│     └─ utcnow.py
├─ README.md
├─ nginx.config
├─ requirements.txt
└─ systemd.service
```


## Stack
[Python:](https://www.python.org/) The programming language used for development.  
[FastAPI:](https://fastapi.tiangolo.com/) A modern, fast (high-performance) web framework for building APIs with Python.  
[SQLAlchemy:](https://www.sqlalchemy.org/) A powerful and flexible ORM (Object-Relational Mapping) library for working with relational databases.  
[Pydantic:](https://docs.pydantic.dev/latest/) A data validation and settings management library, used for defining schemas and validating data in FastAPI applications.  
[Alembic:](https://alembic.sqlalchemy.org/) A lightweight database migration tool for SQLAlchemy, facilitating easy management of database schema changes.  
[PostgreSQL:](https://www.postgresql.org/) A robust open-source relational database management system.  
[Asyncpg:](https://github.com/MagicStack/asyncpg) An asynchronous PostgreSQL database driver for Python.  
[Passlib:](https://pypi.org/project/passlib/) A password hashing library for secure password storage.  
[Pydantic-settings:](https://pypi.org/project/pydantic-settings/) A Pydantic extension for managing settings and configurations.  
[Python-jose:](https://pypi.org/project/python-jose/) A JWT (JSON Web Tokens) implementation for Python.  
[Python-multipart:](https://pypi.org/project/python-multipart/) A library for parsing multipart/form-data requests, often used for file uploads in FastAPI applications.  
[Uvicorn:](https://www.uvicorn.org/) ASGI server implementation used to run FastAPI applications.

## License
This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

## Acknowledgements
Special thanks to the authors and contributors of  
[FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy](https://www.sqlalchemy.org/), and [Alembic](https://pypi.org/project/alembic/) for their fantastic work and contributions.  
Additionally, I acknowledge the following project for providing inspiration and insights:  
[sabuhibrahim/ FastAPI JWT Authentication Full Example](https://github.com/sabuhibrahim/fastapi-jwt-auth-full-example)  
[ThomasAitken/ demo-fastapi-async-sqlalchemy](https://github.com/ThomasAitken/demo-fastapi-async-sqlalchemy)
