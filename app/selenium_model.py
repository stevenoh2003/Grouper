from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import os
import sys
import re
import concurrent.futures

PATH = os.path.join("static/chromedriver")
chrome_options = Options()  
chrome_options.binary_location = "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary"    
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
#chrome_options.headless = True
# Pass the argument 1 to allow and 2 to block
prefs = {
	"profile.default_content_setting_values.media_stream_mic": 2, 
	"profile.default_content_setting_values.media_stream_camera": 2,
	"profile.default_content_setting_values.geolocation": 2,
	"profile.default_content_setting_values.notifications": 1
}
chrome_options.add_experimental_option("prefs",prefs)

def get_google_meet_link(gmail, gmail_password):
	#cwd = /Online Group Generator
	PATH = os.path.join("app/static/chromedriver")
	driver = webdriver.Chrome(executable_path=PATH, options=chrome_options)
	driver.set_window_size(1200, 600)
	#driver.set_window_position(-20000, 0)
	driver.get("https://meet.google.com/new")

	#Logging in to Gmail
	s = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//input[@id='identifierId']")))
	s.send_keys(gmail)
	driver.find_element_by_id("identifierNext").click()
	s = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//input[@name='password']")))
	s.send_keys(gmail_password)
	driver.find_element_by_id("passwordNext").click()

	#Generating Meet links
	s = WebDriverWait(driver, 10).until(EC.url_contains("meet.google.com/"))
	page_source = driver.page_source

	google_meet_link_pattern = re.compile(r"https://meet.google.com/\w{3}-\w{4}-\w{3}")
	match = google_meet_link_pattern.search(page_source)
	link = match.group()	
	driver.quit()
	return link

if __name__ == "__main__":
	NUM_GROUPS = 1
	links = []
	gmail = ""
	gmail_password = ''
	with concurrent.futures.ThreadPoolExecutor() as executor:
		futures = [executor.submit(get_google_meet_link, gmail, gmail_password) for _ in range(NUM_GROUPS)]

	for future in concurrent.futures.as_completed(futures):
		links.append(future.result())