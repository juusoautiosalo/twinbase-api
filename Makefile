.PHONY: requirements check-venv

update-iaa:
	docker compose run --rm iaa-configurator
	docker compose restart ssi-proxy

check-venv:
	@test -n "$(VIRTUAL_ENV)" && \
	echo "Using virtual environment: $(VIRTUAL_ENV)" || \
	(echo "Virtual environment is not activated"; exit 1)

pip-tools: check-venv
	pip install --upgrade pip pip-tools

requirements: check-venv
	pip-compile --generate-hashes --resolver backtracking -o requirements.txt requirements.in
	pip-compile --generate-hashes --resolver backtracking -o dev-requirements.txt dev-requirements.in 

sync: check-venv
	pip-sync dev-requirements.txt requirements.txt

update-dependencies: requirements sync