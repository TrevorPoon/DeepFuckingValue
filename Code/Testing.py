import undetected_chromedriver as uc
import time



driver = uc.Chrome(use_subprocess=False)
driver.get('google.com')
time.sleep(4)