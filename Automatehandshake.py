#import statements required to run the program
import pkg_resources
import time
import pandas as pd
import sys
from getpass import getpass
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

requirement_path = Path(__file__).with_name("requirements.txt")
requirements = pkg_resources.parse_requirements(requirement_path.open())
for requirement in requirements:
    try:
        pkg_resources.require(str(requirement))
    except pkg_resources.VersionConflict:
        continue


# Get link with the filtered search of jobs which the user wants to apply
while True:
    filter_link = input("Please enter the filterd link for the jobs you want to apply \n")
    # Check if the input provided is a link or not and is a handshake link
    if (len(filter_link) == 0):
        print("This field cannot be blank")
        continue
    else:
        if not((filter_link.startswith("https:") or filter_link.startswith("http:")) and ("handshake" in filter_link)):
            print("Please check the link provided again, make sure the link is from hankshake")
            continue
        else:
            break

# Get the university name of the user
while True:
    university_name = input("Please Enter the name of your University \n")
    if (len(university_name) == 0):
        print("Sorry, this field cannot be blank")
        continue
    else:
        break

# Get creds of the user for SSO Login
while True:
    student_id = input("Enter your student id (id for SSO login) \n")
    student_password = getpass("Enter your password (password for SSO login) \n")
    if (len(student_id) == 0 or len(student_password) == 0):
        print("Either of the creds are blank, please check again")
        continue
    else:
        break

        
#Creating the file if it doesnt exist else reading the csv into a dataframe
path_to_jobs = Path(__file__).with_name("jobs.csv")
jobs_columns = [
    'job_id', 'job_link', 'job_status', 
    'job_role', 'job_type', 'company', 
    'location', 'location_type', 'posted_date', 
    'deadline_date'
    ]
try:
    jobs_df = pd.read_csv(path_to_jobs)
except pd.errors.EmptyDataError:
    jobs_df = pd.DataFrame(columns=jobs_columns)

# Initialzing the driver 
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
driver_wait = WebDriverWait(driver,10)

def navigate_to_sso(filter_link, university_name, 
                    student_id, student_password):
    # function to load the main page, navigate to your school sso login
    driver.get(filter_link)
    drop_down_element = '#s2id_school-login-select'
    driver_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, drop_down_element))).click()

    # filtering the university name and selecting it
    filter_element_selector = '#s2id_autogen1_search'
    university_entry = driver_wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, filter_element_selector)))
    university_entry.send_keys(university_name)
    university_element_selector = "ul[class^='select2-results']"
    university_element = driver_wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, university_element_selector)))
    time.sleep(2.5)
    if (university_element.text == university_name):
        university_element.click()

    # Waiting for the sso login page to load so you can hop onto the Mothership
    sso_element_selector = "a[class = 'sso-button']"
    sso_element = driver_wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, sso_element_selector)))
    if (sso_element.is_displayed()):
        sso_element.click()
    
    # Wait for the SSO Page to load and walk into the Mothership
    student_id_selector = "input[id='username']"
    student_password_selector = "input[id='password']"
    sign_in_selector = "input[name='submit']"
    sign_in_element = driver_wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, sign_in_selector)))
    if (sign_in_element.is_displayed()):
        driver.find_element(By.CSS_SELECTOR, student_id_selector).send_keys(student_id)
        driver.find_element(By.CSS_SELECTOR, student_password_selector).send_keys(student_password)    
        sign_in_element.click()

def duo_sso_login():
    # ASU uses duo as two factor authentication 
    # if your school uses anything else please change here
    time.sleep(2.5)
    driver_wait.until(EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, '#duo_iframe')))
    driver_wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#auth_methods > fieldset:nth-child(1) > div.row-label.push-label > button"))).click()

def job_search_list():
    jobs_array = []
    WebDriverWait(driver,30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "main[id='skip-to-content']")))
    total_pages = driver.find_element(By.CSS_SELECTOR, "button[data-hook='search-pagination-previous'] ~ div").text.split('/')
    no_of_pages = int(total_pages[1].strip())
    for pages in range(0, no_of_pages):
        WebDriverWait(driver,30).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "button[data-hook^='search-pagination-next']")))
        jobs_element_selector = "div[class^='style__cards__'] a[href]"
        jobs_element = driver_wait.until(EC.visibility_of_all_elements_located((By.CSS_SELECTOR, jobs_element_selector)))
        for jobs in jobs_element:
            jobs_array.append(jobs.get_attribute('href'))
        next_page_selector = "button[data-hook^='search-pagination-next']"
        driver_wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, next_page_selector))).click()
    return jobs_array
    
navigate_to_sso(filter_link, university_name, 
                student_id, student_password) 
duo_sso_login()

if (jobs_df.empty):
    jobs_df = pd.DataFrame(columns=jobs_columns)
    jobs_data = pd.DataFrame({"job_link": job_search_list()}, index=len(job_search_list()))
    jobs_df = jobs_df.append(jobs_data)

