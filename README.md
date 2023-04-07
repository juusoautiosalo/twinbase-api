# Twinbase API

Developing an HTTP API for Twinbase

# Setup

## Clone and move to repository
```sh
git clone https://gitlab.com/JuusoAut/privacy-preserving-self-sovereign-identities.git

git clone --branch no-auth https://github.com/juusoautiosalo/twinbase-api.git

cd twinbase-api
```

## Deployment (with SSI-proxy)

Prerequisites
- Docker and Docker compose

### Set environment variables
Configure environment variables or `.env` file to match environment variables used in [`docker-compose.yml`](docker-compose.yml) (`${}`).
```
nano .env
```
Example contents:
```
TWINBASE_API_GITHUB_TOKEN=github_pat_1234567890qwerty
IAA_OWNER_DID=did:key:z6Mkk4YdpLxAxWkDULdBVifCjVDPh3WvhbkDL1W4miwoHEQb
```
Explanations:
- `TWINBASE_API_GITHUB_TOKEN`: Create a fine-grained access token at https://github.com/settings/personal-access-tokens/new
  - Repository access => Only select repsitories => [Your Twinbase instance repository]
  - Permissions => Repository permissions => Contents => Access: Read and write
  - Press "Generate token" and copy the token to the variable
- `IAA_OWNER_DID`: Create an owner DID according to instructions at https://gitlab.com/JuusoAut/privacy-preserving-self-sovereign-identities

### Start services
```
docker compose up --build --detach
```
See Swagger documentation at http://localhost:9000/docs
- Requests via the swagger interface don't work.
- Set up DIDs, credentials, tokens, and headers according to these instructions to send requests:
  https://gitlab.com/JuusoAut/privacy-preserving-self-sovereign-identities

### Update IAA configuration and reboot SSI-proxy
Run following on host machine:
```
make update-iaa
```

### Stop services
```
docker compose down
```

### Remove all unused docker images
```
docker image prune --all
```

## Development

Prerequisites
- Python 3.7 or above
- `make`
  - If make is not available you may check [Makefile](Makefile) for the commands

### Create virtual environment and install requirements

```sh
# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

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




