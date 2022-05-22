import argparse
import os
import sys
from thefuzz import fuzz
from os.path import exists
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from time import sleep

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
    # TODO add a not
    if args.debug:
        options.add_argument("--headless")
    service = Service(executable_path="./geckodriver")
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
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.homegamelist"))
        )
        matches = driver.find_elements(
            By.XPATH,
            "//div[@class='col-md-8 homegamelist']/div[@class='listing']/div[2]/a[1]",
        )
        index = 1
        for item in matches:
            print("\t{}) {}".format(index, item.text))
            index = index + 1
    except:
        error("no match found!")


def select_match(driver, match):
    try:
        temp = driver.find_element(
            By.XPATH,
            "(//div[@class='col-md-8 homegamelist']/div[@class='listing'])["
            + match
            + "]/div[2]/a[2]",
        )
        res = temp.get_attribute("href")
        temp.click()
        return res
    except:
        error("match error selected!")


def open_character_sheet(driver):
    try:
        WebDriverWait(driver, 15, 1).until(
            EC.presence_of_element_located((By.ID, "rightsidebar"))
        )
        driver.find_element(By.ID, "ui-id-2").click()
        # TODO remove
        # sleep(3)
        pg = input("Name of the pg: ")
        vprint(f"Input name: {pg}")
        list = driver.find_elements(By.CLASS_NAME, "character")
        index = 0
        for elem in list:
            lev = fuzz.partial_ratio(pg.lower(), elem.text.lower())
            vprint(
                f"Levenshtein distance between {pg.lower()} and {elem.text.lower()} is: {lev}"
            )
            if lev > 60:
                vprint(f"Character found!")
                break
            index = index + 1

        res = list[index].get_attribute("data-itemid")
        list[index].click()
        return res
    except:
        error("ERROR: opening character sheet!")


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

    driver = setup_selenium()
    driver.get(CONST_URL)

    data_login = read_config()
    login(driver, data_login["username"], data_login["password"])
    get_match(driver)
    match = input("Choose the game: ")
    match_href = select_match(driver, match)
    character_id = open_character_sheet(driver)

    print(f"----\n{match_href}\n{character_id}\n----")

    # debug
    # with open("output", "w") as file:
    #    file.write(driver.page_source)

    driver.switch_to.active_element

    # print(driver.find_element(By.XPATH, "/html/body/div[50]").text)
    # div = driver.find_element(
    #    By.XPATH,
    #    "//div[@data-characterid='-MsLT4b4wQiFyyX-ytrM']",
    # )

    # iframe = div.find_element(By.NAME, "iframe_-MsLT4b4wQiFyyX-ytrM")
    # iframe = div.find_elements(By.TAG_NAME, "iframe")[0]

    driver.switch_to.frame("iframe_-MsLT4b4wQiFyyX-ytrM")

    # print(driver.find_element(By.XPATH, "/html/body/div[1]/div/ul/li[1]/a").text)
    with open("output2", "w") as file:
        file.write(driver.page_source)

    # driver.switch_to.default_content()

    driver.close()
    # driver.quit()
