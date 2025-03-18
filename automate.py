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
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

db_unique_number = []

def generation_of_unique_number():
    unique_number = random.randint(1000, 99999)
    while unique_number in db_unique_number:
        unique_number = random.randint(1000, 99999)
    db_unique_number.append(unique_number)
    return unique_number

def download_jurisprudence_pdf(url):
    unique_number = generation_of_unique_number()
    output_file = f"telechargements/j-{unique_number}.pdf"

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(output_file, "wb") as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        logger.info(f"✅ Fichier téléchargé : {output_file}")
    else:
        logger.error(f"❌ Échec du téléchargement. Code: {response.status_code}")

# Load URLs from CSV
df = pd.read_csv("data/legiafrica-jurisprudence.csv")

# Create download directory if it doesn't exist
download_dir = os.path.join(os.getcwd(), "telechargements")
os.makedirs(download_dir, exist_ok=True)

# Ensure a unique user data directory for each run
user_data_dir = os.path.join(download_dir, f'user_data_{time.time()}')
os.makedirs(user_data_dir, exist_ok=True)

# Configure Selenium
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
options.add_argument(f"--user-data-dir={user_data_dir}")

service = Service(ChromeDriverManager().install())

driver = webdriver.Chrome(service=service, options=options)
try:
    driver.get("https://legiafrica.com/login")
    wait = WebDriverWait(driver, 10)
    # Login to the site
    email_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="email-field"]')))
    password_input = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="password-field"]')))
    email_input.send_keys("jurisintelligencework@gmail.com")
    password_input.send_keys("JurisIntelligence@2024")

    login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="loginModal"]/div/div/div/div[1]/div[2]/form/div/button')))
    login_button.click()
    logger.info("Connexion réussie")
    time.sleep(1)
    paths = []
    # Process documents in the database
    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        url = row["DETAILS_LINK"]
        driver.get(url)
        time.sleep(2)
        try:
            # Check if the download button exists
            download_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.legiafrica-btn.report')))
            download_button.click()
            time.sleep(2)
            # Get the current URL after the click
            current_url = driver.current_url
            logger.info(f"📄 PDF détecté via bouton : {current_url}")
            download_jurisprudence_pdf(current_url)
        except Exception as e:
            logger.warning(f"⚠️ Bouton de téléchargement non trouvé pour {url}. Tentative avec BeautifulSoup...")
            # Use BeautifulSoup to get an alternative link
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            pdf_link = None
            for link in soup.find_all("a"):
                if "Télécharger" in link.text or "télécharger" in link.text:
                    pdf_link = link.get("href")
                    break  # Take the first link found
            if pdf_link:
                logger.info(f"📄 Lien PDF trouvé avec BeautifulSoup : {pdf_link}")
                if not pdf_link.startswith("http"):
                    pdf_link = "https://legiafrica.com" + pdf_link
                download_jurisprudence_pdf(pdf_link)
            else:
                logger.error(f"❌ Aucun lien PDF trouvé pour {url}")

    df["PDF_PATH"] = paths
    df.to_csv(f"data/split/jurisprudence_part_{df.index[0] // len(df) + 1}.csv", index=False)
finally:
    driver.quit()
