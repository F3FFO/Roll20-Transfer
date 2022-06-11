# sys
import argparse
import os
import sys
from os.path import exists

# selenium
import selenium as webd
import selenium.webdriver.support.ui as support_ui
import selenium.webdriver.support.expected_conditions as EC
import selenium.webdriver.firefox.options as opt
import selenium.webdriver.firefox.service as srv
import selenium.webdriver.common.by as by

# local
import utility
import export.export_data as export


DRIVER = "./geckodriver"
CONFIG_FILE = "config.prop"
CONST_URL = "https://app.roll20.net/login"


def setup_selenium():
    options = opt.Options()
    if not args.debug:
        options.add_argument("--headless")
    utility.vprint(args, f"init driver...")
    service = srv.Service(executable_path=DRIVER)
    utility.vprint(args, f"driver found -> {DRIVER}")
    return webd.webdriver.Firefox(service=service, options=options)


def take_login_input():
    login = {}
    login["username"] = input()
    login["password"] = input()
    return login


def read_config():
    if exists(CONFIG_FILE):
        separator = "="
        login = {}

        with open(CONFIG_FILE) as f:
            for line in f:
                if separator in line:
                    # Find the name and value by splitting the string
                    name, value = line.split(separator, 1)

                    # Assign key value pair to dict
                    login[name.strip()] = value.strip()
        return login

    utility.error("config.prop not found!")
    return take_login_input()


def login(driver, username, psw):
    driver.find_element(by.By.ID, "email").send_keys(username)
    driver.find_element(by.By.ID, "password").send_keys(psw)
    driver.find_element(by.By.ID, "login").click()


def get_match(driver):
    try:
        support_ui.WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (by.By.XPATH, "//div[@class='col-md-8 homegamelist']")
            )
        )
        matches = driver.find_elements(
            by.By.XPATH,
            "//div[@class='col-md-8 homegamelist']/div[@class='listing']/div[@class='gameinfo']/a[1]",
        )
        index = 1
        for item in matches:
            print("\t{}) {}".format(index, item.text))
            index = index + 1

    except:
        utility.error("no match found!")


def select_match(driver, match):
    try:
        match_name = driver.find_element(
            by.By.XPATH,
            "//div[@class='col-md-8 homegamelist']/div[@class='listing']["
            + match
            + "]/div[@class='gameinfo']/a[1]",
        )
        utility.vprint(args, f"match selected -> {match_name.text}")
        driver.find_element(
            by.By.XPATH,
            "(//div[@class='col-md-8 homegamelist']/div[@class='listing'])["
            + match
            + "]/div[2]/a[2]",
        ).click()

    except:
        utility.error("match error selected!")


def get_character_sheet(driver):
    try:
        support_ui.WebDriverWait(driver, 15, 1).until(
            EC.presence_of_element_located((by.By.ID, "rightsidebar"))
        )
        driver.find_element(by.By.ID, "ui-id-2").click()
        support_ui.WebDriverWait(driver, 15, 1).until(
            EC.presence_of_element_located((by.By.ID, "journalfolderroot"))
        )
        driver.implicitly_wait(3)
        list = driver.find_elements(by.By.CLASS_NAME, "character")
        index = 1
        for elem in list:
            print("\t{}) {}".format(index, elem.text))
            index = index + 1

    except:
        utility.error("ERROR: opening character sheet!")


def select_character_sheet(driver, character):
    try:
        elem = driver.find_elements(by.By.CLASS_NAME, "character")
        elem = elem[character - 1]
        character_id = elem.get_attribute("data-itemid")
        character_name = elem.text
        utility.vprint(args, f"character selected -> {character_name}")
        elem.click()
        return character_id, character_name

    except:
        utility.error("ERROR: opening character sheet!")


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

    # init selenium driver
    driver = setup_selenium()
    utility.vprint(args, f"driver initilized")

    # load url
    driver.get(CONST_URL)
    utility.vprint(args, f"loading url -> {CONST_URL}")

    # login to roll20
    utility.vprint(args, f"logging in")
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
    driver.switch_to.frame(driver.find_element(by.By.NAME, f"iframe_{character_id}"))
    driver.refresh

    if args.export:
        # create folder if not exist
        if not os.path.exists("./out"):
            os.makedirs("./out")
        character_name = character_name.lower()
        character_name = character_name.replace(" ", "_")

        # export character
        with open(f"./out/{character_name}.md", "w") as file:
            export.export_bio(args, driver, file)

    # switch to default content
    driver.switch_to.default_content()
    # driver.quit()
