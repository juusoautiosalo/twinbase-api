# Twinbase API

Developing an HTTP API for Twinbase

# Setup

## Clone and move to repository
```sh
git clone https://github.com/juusoautiosalo/twinbase-api.git

cd twinbase-api
```

## Deployment (with SSI-proxy)

Prerequisites
- Docker and Docker compose

Configure environment variables or `.env` file to match environment variables used in [`docker-compose.yml`](docker-compose.yml) (`${}`).

For example, configure following to file `./.env`:
```
TWINBASE_API_GITHUB_TOKEN=
IAA_OWNER_DID=
```

### Start services
```
docker compose up --build --detach
```

### Update IAA configuration and reboot SSI-proxy
Run following on host machine:
```
make update-iaa
```

## Development

Prerequisites
- Python 3.7 or above
- `make`
  - If make is not available you may check [Makefile](Makefile) for the commands

### Create virtual environment and install requirements

```sh
# Create and activate virtual environment (recommended)
python3 -m venv env
source env/bin/activate

# Install pip-tools to manage requiremenets
make pip-tools

# Install requirements to virtual enviroment with pip-tools
make sync
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




