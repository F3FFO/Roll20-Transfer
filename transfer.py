import argparse
import os
import sys
from os.path import exists
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
import markdownify

DRIVER = "./geckodriver"
CONFIG_FILE = "config.prop"
CONST_URL = "https://app.roll20.net/login"


def error(str):
    if is_ci:
        print(f"\n ! {str}\n")
    else:
        print(f"\n\033[41m{str}\033[0m\n")
    sys.exit(1)


def vprint(str):
    if args.verbose:
        print(str)


def setup_selenium():
    options = Options()
    if not args.debug:
        options.add_argument("--headless")
    vprint(f"init driver...")
    service = Service(executable_path=DRIVER)
    vprint(f"driver found -> {DRIVER}")
    return webdriver.Firefox(service=service, options=options)


def read_config():
    if exists(CONFIG_FILE):
        separator = "="
        login = {}

        # I named your file conf and stored it
        # in the same directory as the script
        with open(CONFIG_FILE) as f:
            for line in f:
                if separator in line:
                    # Find the name and value by splitting the string
                    name, value = line.split(separator, 1)

                    # Assign key value pair to dict
                    # strip() removes white space from the ends of strings
                    login[name.strip()] = value.strip()
        return login
    else:
        error("config.prop not found!")


def login(driver, username, psw):
    driver.find_element(By.ID, "email").send_keys(username)
    driver.find_element(By.ID, "password").send_keys(psw)
    driver.find_element(By.ID, "login").click()


def get_match(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@class='col-md-8 homegamelist']")
            )
        )
        matches = driver.find_elements(
            By.XPATH,
            "//div[@class='col-md-8 homegamelist']/div[@class='listing']/div[@class='gameinfo']/a[1]",
        )
        index = 1
        for item in matches:
            print("\t{}) {}".format(index, item.text))
            index = index + 1
    except:
        error("no match found!")


def select_match(driver, match):
    try:
        match_name = driver.find_element(
            By.XPATH,
            "//div[@class='col-md-8 homegamelist']/div[@class='listing']["
            + match
            + "]/div[@class='gameinfo']/a[1]",
        )
        vprint(f"match selected -> {match_name.text}")
        driver.find_element(
            By.XPATH,
            "(//div[@class='col-md-8 homegamelist']/div[@class='listing'])["
            + match
            + "]/div[2]/a[2]",
        ).click()
    except:
        error("match error selected!")


def get_character_sheet(driver):
    try:
        WebDriverWait(driver, 15, 1).until(
            EC.presence_of_element_located((By.ID, "rightsidebar"))
        )
        driver.find_element(By.ID, "ui-id-2").click()
        WebDriverWait(driver, 15, 1).until(
            EC.presence_of_element_located((By.ID, "journalfolderroot"))
        )
        driver.implicitly_wait(3)
        list = driver.find_elements(By.CLASS_NAME, "character")
        index = 1
        for elem in list:
            print("\t{}) {}".format(index, elem.text))
            index = index + 1

    except:
        error("ERROR: opening character sheet!")


def select_character_sheet(driver, character):
    try:
        elem = driver.find_elements(By.CLASS_NAME, "character")
        elem = elem[character - 1]
        character_id = elem.get_attribute("data-itemid")
        character_name = elem.text
        vprint(f"character selected -> {character_name}")
        elem.click()
        return character_id, character_name
    except:
        error("ERROR: opening character sheet!")


def export_bio(driver, file):
    try:
        WebDriverWait(driver, 10).until(
            EC.invisibility_of_element((By.ID, "animation-container"))
        )
        WebDriverWait(driver, 15, 1).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@class='bioinfo tab-pane']")
            )
        )
        note = driver.find_element(By.XPATH, "//div[@class='bioinfo tab-pane']")
        vprint("bio found!\nwriting bio...")
        file.write(
            markdownify.markdownify(
                note.get_attribute("outerHTML"), heading_style="ATX"
            )
        )
        vprint("bio writed!")
    except:
        error("ERROR: exporting bio!")


is_ci = "CI" in os.environ and os.environ["CI"] == "true"

# Environment checks
if sys.version_info < (3, 6):
    vprint(f"Your python verion is {sys.version_info}")
    error("Requires Python 3.6+")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Roll20")
    parser.set_defaults(func=lambda x: None)
    parser.add_argument("-d", "--debug", action="store_true", help="debug mode")
    parser.add_argument(
        "-e", "--export", action="store_true", help="export character sheet"
    )
    parser.add_argument(
        "-i", "--import", action="store_true", help="import character sheet"
    )
    parser.add_argument("-u", "--update", action="store_true", help="update webdriver")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    args = parser.parse_args()

    # init selenium
    driver = setup_selenium()
    vprint(f"driver initilized")
    driver.get(CONST_URL)
    vprint(f"loading url -> {CONST_URL}")

    # login to roll20
    vprint(f"logging in")
    data_login = read_config()
    login(driver, data_login["username"], data_login["password"])

    # get and select match
    get_match(driver)
    match = input("Choose the game: ")
    select_match(driver, match)

    # get and select character
    get_character_sheet(driver)
    character = input("Choose the character: ")
    character_id, character_name = select_character_sheet(driver, int(character))

    # switch to character frame
    driver.switch_to.active_element
    iframe = driver.find_element(By.NAME, f"iframe_{character_id}")
    driver.switch_to.frame(iframe)
    driver.refresh

    if args.export:
        # create folder if not exist
        if not os.path.exists("./out"):
            os.makedirs("./out")
        character_name = character_name.lower()
        character_name = character_name.replace(" ", "_")
        # export character
        with open(f"./out/{character_name}.md", "w") as file:
            export_bio(driver, file)

    # switch to default content
    driver.switch_to.default_content()
    # driver.quit()
