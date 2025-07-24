# Makefile para gerenciamento de projeto Python (macOS/Linux)

.PHONY: install-brew install-python create-venv install-poetry install-deps ensure-venv activate run

### Configuração inicial ###
install-brew:
	@if [ "$(shell uname)" = "Darwin" ] && ! command -v brew &>/dev/null; then \
		/bin/bash -c "$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; \
		echo 'eval "$$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc; \
		source ~/.zshrc; \
	fi

install-python: install-brew
	@if ! command -v python3 &>/dev/null; then \
		brew install python; \
	fi

### Ambiente Virtual ###
create-venv:
	@if [ ! -d ".venv" ]; then \
		python3 -m venv .venv; \
		echo "✅ .venv criado. Ative com: eval \"\$$(make activate)\""; \
	fi

# Ativação automática via eval
activate:
	@if [ -d ".venv" ]; then \
		echo "source $$(pwd)/.venv/bin/activate"; \
	else \
		echo "echo '❌ .venv não existe. Crie com: make create-venv'"; \
		exit 1; \
	fi

### Poetry e Dependências ###
install-poetry: create-venv
	@if ! command -v poetry &>/dev/null; then \
		eval "$$(make activate)"; \
		curl -sSL https://install.python-poetry.org | python3 -; \
		echo "✋ Adicione ao PATH: export PATH=$$HOME/.local/bin:$$PATH"; \
	fi

install-deps: create-venv
	@eval "$$(make activate)"; \
	poetry install

### Execução ###
run: install-deps
	@echo "▶️  Executando main.py via Poetry..."
	@eval "$$(make activate)"; \
	poetry run python src/iramuteq_preprocessor/main.py

### Atalhos ###
setup: install-python create-venv install-poetry install-deps
	@echo "\n✅ Setup completo! Ambiente pronto."
	@echo "Para ativar o .venv, execute:"
	@echo "   eval \"\$$(make activate)\""
