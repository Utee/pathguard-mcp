FROM python:3.13-slim

WORKDIR /app

# Install the package itself so the pathguard-mcp entry point is available.
COPY pyproject.toml README.md ./
COPY pathguard_mcp ./pathguard_mcp
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["pathguard-mcp", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
