# Używamy oficjalnego obrazu Pythona
FROM python:3.11-slim

# Ustawienie zmiennych środowiskowych (Poprawiony format key=value)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Ustawienie katalogu roboczego
WORKDIR /app

# Instalacja zależności systemowych
RUN apt-get update && apt-get install -y \
    fonts-freefont-ttf \
    libfreetype6-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
# Kopiowanie i instalacja zależności Pythona
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiowanie reszty kodu aplikacji
COPY . .

# Tworzenie katalogu na grafiki
RUN mkdir -p uploads

# Eksponowanie portu Streamlit
EXPOSE 8501

# Komenda startowa
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]