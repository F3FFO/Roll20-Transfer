# selenium
import selenium.webdriver.support.ui as support_ui
import selenium.webdriver.support.expected_conditions as EC
import selenium.webdriver.common.by as by

# markdown
import markdownify

# local
import utility


def export_bio(args, driver, file):
    try:
        support_ui.WebDriverWait(driver, 10).until(
            EC.invisibility_of_element((by.By.ID, "animation-container"))
        )
        support_ui.WebDriverWait(driver, 15, 1).until(
            EC.presence_of_element_located(
                (by.By.XPATH, "//div[@class='bioinfo tab-pane']")
            )
        )
        note = driver.find_element(by.By.XPATH, "//div[@class='bioinfo tab-pane']")
        utility.vprint(args, "bio found!\nwriting bio...")
        file.write(
            markdownify.markdownify(
                note.get_attribute("outerHTML"), heading_style="ATX"
            )
        )
        utility.vprint(args, "bio writed!")
    except:
        utility.error("ERROR: exporting bio!")
