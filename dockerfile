# Étape 1 : Utiliser une image de base avec Python
FROM python:3.10-slim

# Étape 2 : Installer les dépendances du système pour Selenium et Chrome
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    libx11-dev \
    libxext6 \
    libxrender1 \
    libglib2.0-0 \
    libfontconfig1 \
    libxi6 \
    libgdk-pixbuf2.0-0 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    xz-utils \
    libappindicator3-1 \
    libdbus-1-3 \
    xvfb \
    ca-certificates \
    libasound2 \
    xdg-utils \  
    && rm -rf /var/lib/apt/lists/*

# Étape 3 : Télécharger et installer Google Chrome stable
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb
RUN apt --fix-broken install -y

# Étape 4 : Télécharger la dernière version de ChromeDriver
RUN LATEST_VERSION=$(wget -q -O - https://chromedriver.storage.googleapis.com/LATEST_RELEASE) && \
    wget https://
