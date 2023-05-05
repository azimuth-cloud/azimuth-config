from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

try:
    driver = webdriver.Firefox()
    # Set maximum wait time (in seconds) for finding elements
    driver.implicitly_wait(5)

    driver.get("http://localhost:8080")

# Clean up properly on error
except Exception as e:
    print('Encountered exception - closing browser\n')
    driver.close()
    raise e