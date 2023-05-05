from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

try:
    opts = webdriver.FirefoxOptions()
    opts.add_argument('--headless')
    driver = webdriver.Firefox(options=opts)
    # Set maximum wait time (in seconds) for finding elements
    driver.implicitly_wait(5)

    driver.get("http://google.com")

# Clean up properly on error
except Exception as e:
    print('Encountered exception - closing browser\n')
    driver.close()
    raise e