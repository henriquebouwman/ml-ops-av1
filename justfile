# Uso: uv run just <receita>   (o just vem como dependência de desenvolvimento)

set dotenv-load := true

modelo := if env("OLLAMA_MODEL", "") == "" { "qwen2.5vl:3b" } else { env("OLLAMA_MODEL") }

# Lista as receitas
default:
    @just --list

# Instala o ambiente exatamente como no uv.lock
setup:
    uv sync --frozen

# Baixa o modelo no Ollama (precisa de internet e do Ollama rodando)
model:
    ollama pull {{modelo}}

# Sobe o serviço em http://localhost:3000 (Swagger na raiz)
serve:
    uv run bentoml serve service:LeituraMedidor --port 3000

# Roda os testes (precisa do Ollama rodando com o modelo baixado)
test:
    uv run pytest -v

# Envia uma foto ao serviço já no ar e mostra a resposta
demo foto="examples/example02.jpg":
    curl -s -F "image=@{{foto}}" http://localhost:3000/extract | uv run python -m json.tool --no-ensure-ascii
