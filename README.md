# Twinbase API

Developing an HTTP API for Twinbase

## Deploy

Prerequisites
- Python 3.6 or above

### Clone and move to repository
```sh
git clone https://github.com/juusoautiosalo/twinbase-api.git

cd twinbase-api
```

### Create virtual environment

```sh
# Create and activate virtual environment (recommended)
python3 -m venv env
source env/bin/activate

# Install requirements with pip
pip install -r requirements.txt
```

### Add any necessary environment variables

See the code (main.py) to see what you need: `os.getenv('ENV_VARIABLE_X')` means the variable is used.


### Run server
```
# Development:
uvicorn main:app --reload

# Production:
uvicorn main:app --host 0.0.0.0
```




