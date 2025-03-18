import os
import random
import requests
import pandas as pd
import time
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Configurer les logs
logger = logging.getLogger(__name__)

logging.info(f"📌 Génération d'un numéro unique pour éviter les conflits de fichiers")

# Génération d'un numéro unique pour éviter les conflits de fichiers
db_unique_number = []
def generation_of_unique_number():
    unique_number = random.randint(1000, 99999)
    if unique_number in db_unique_number:
        return generation_of_unique_number()
    else:
        db_unique_number.append(unique_number)
        return unique_number

# Fonction de téléchargement du PDF
logging.info(f"# 📌 Fonction de téléchargement du PDF")

def download_jurisprudence_pdf(url):
    unique_number = generation_of_unique_number()
    output_file = f"telechargements/j-{unique_number}.pdf"

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(output_file, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        logging.info(f"✅ Fichier téléchargé : {output_file}")
    else:
        logging.error(f"❌ Échec du téléchargement. Code: {response.status_code}")

# Chargement des URLs à partir du fichier CSV
logging.info(f"📌 Chargement des URLs à partir du fichier CSV")

df = pd.read_csv("data/legiafrica-jurisprudence.csv")

# Diviser le DataFrame en 4 parties
logging.info(f"📌 Diviser le DataFrame en 4 parties")
df_split = [df[i::4] for i in range(4)]

# Création du dossier de téléchargement si inexistant
logging.info(f"📌 Création du dossier de téléchargement si inexistant")
download_dir = os.path.join(os.getcwd(), "telechargements")
os.makedirs(download_dir, exist_ok=True)

# Configuration de Selenium
logging.info(f"📌 Configuration de Selenium")
options = Options()
options.add_argument("--disable-notifications")
options.add_argument("--headless")
prefs = {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
}
options.add_experimental_option("prefs", prefs)

# Ensure unique user data directory
user_data_dir = f"/tmp/user_data_{generation_of_unique_number()}"
options.add_argument(f"--user-data-dir={user_data_dir}")

# Initialisation du driver
logging.info(f"📌 Téléchargement du chrome driver")
service = Service(ChromeDriverManager().install())

def process_df_part(df_part):
    driver = webdriver.Chrome(service=service, options=options)
    try:
        driver.get("https://legiafrica.com/login")
        wait = WebDriverWait(driver, 5)
        logging.info(f"📌 Ouverture du site")

        # Connexion au site
        email_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="email-field"]')))
        password_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="password-field"]')))
        email_input.send_keys("jurisintelligencework@gmail.com")
        password_input.send_keys("JurisIntelligence@2024")

        login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="loginModal"]/div/div/div/div[1]/div[2]/form/div/button')))
        login_button.click()
        logging.info(f"Connexion avec succès")

        time.sleep(1)

        paths = []

        # Traitement des documents dans la base de données
        for index, row in tqdm(df_part.iterrows()):
            url = row["DETAILS_LINK"]
            driver.get(url)
            time.sleep(2)

            try:
                # Vérifier si le bouton de téléchargement existe
                download_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.legiafrica-btn.report')))
                download_button.click()
                time.sleep(2)

                # Récupérer l'URL du PDF actuel après le clic
                current_url = driver.current_url
                logging.info(f"📄 PDF détecté via bouton : {current_url}")
                download_jurisprudence_pdf(current_url)

            except Exception as e:
                logging.warning(f"⚠️ Bouton de téléchargement non trouvé pour {url}. Tentative avec BeautifulSoup...")

                # Utilisation de BeautifulSoup pour récupérer un lien alternatif
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')

                pdf_link = None
                for link in soup.find_all("a"):
                    if "Télécharger" in link.text or "télécharger" in link.text:
                        pdf_link = link.get("href")
                        break  # Prendre le premier lien trouvé

                if pdf_link:
                    logging.info(f"📄 Lien PDF trouvé avec BeautifulSoup : {pdf_link}")
                    if not pdf_link.startswith("http"):
                        pdf_link = "https://legiafrica.com" + pdf_link

                    download_jurisprudence_pdf(pdf_link)
                else:
                    logging.error(f"❌ Aucun lien PDF trouvé pour {url}")

        df_part["PDF_PATH"] = paths
        df_part.to_csv(f"data/split/jurisprudence_part_{df_part.index[0] // len(df) + 1}.csv", index=False)

    finally:
        driver.quit()

# Traitement séquentiel des parties du DataFrame
for df_part in df_split:
    process_df_part(df_part)
