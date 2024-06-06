from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ServerSelectionTimeoutError

def getDriver(background=True) -> webdriver.Chrome:
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    if background:
        options.add_argument('--headless')
        options.add_argument("--mute-audio")
    driver = webdriver.Chrome(options=options) 
    return driver

def goToLink(link:str, driver: webdriver.Chrome) -> None:
    driver.get(link)

def playButton(driver: webdriver.Chrome) -> None:
    """
    This one is to handle the play button that can appear in case the video didn't start playing automatically
    """
    try:
        play_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "ytp-large-play-button"))
        )
        play_button.click()
        print("play button clicked") 
    except TimeoutException:
        print("The video started playing automatically.")

def getCaptionsContainer(driver: webdriver.Chrome) -> WebElement:
    caption_container = driver.find_element(By.CLASS_NAME, "ytp-caption-window-container")
    return caption_container

def getCaptionsLines(driver: webdriver.Chrome) -> WebElement:
    """
    Extract all caption lines
    """
    caption_lines = driver.find_elements(By.CLASS_NAME, "caption-visual-line")
    return caption_lines

def establish_mongodb_connection(database: str, collection: str) -> Collection:
    """
    Establishes a connection to the MongoDB localhost server and returns a Collection instance.
    """
    try:
        client = MongoClient("mongodb://localhost:27017") # Establish a mongodb connection
        client.server_info()  # Try to get server info to check the connection
    except ServerSelectionTimeoutError:
        print("Failed to connect to MongoDB. Please check your connection.")
        return None, None
        
    db = client[database]                              # Create a database
    collection = db[collection]                        # Create a collection

    return collection