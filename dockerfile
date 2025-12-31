# Usa uma imagem base leve do Python
FROM python:3.11-slim

# Define variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependências do sistema necessárias (ajuste conforme precisar)
RUN apt-get update && apt-get install -y \
    build-essential \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Cria diretório da aplicação
WORKDIR /app

# Copia requirements.txt e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da aplicação
COPY . .

# Expõe a porta configurada no app.py (9000)
EXPOSE 9000

# Comando para rodar o servidor em produção (Gunicorn com 4 workers)
# Substitua "app:app" pelo caminho correto se precisar (ex: "wsgi:app")
# Por isso:
CMD ["python", "app.py"]

ENV FLASK_ENV=docker
