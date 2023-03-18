#import statements required to run the program
import pkg_resources
import time
import pandas as pd
import re
from getpass import getpass
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options


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

#Get Document Name from the user
while True:
    resume_aria_label = input("Please enter filename of Resume uploaded to handshake (For reference go to documents on handshake and grab the filename with extenstion which should be used for application) \n")
    if (len(resume_aria_label) == 0):
        print("Sorry, this field cannot be blank")
        continue
    else:
        break

while True:
    transcript_aria_label = input("Please enter filename of Transcript uploaded to handshake (For reference go to documents on handshake and grab the filename with extenstion which should be used for application) \n")
    if (len(transcript_aria_label) == 0):
        print("Sorry, this field cannot be blank")
        continue
    else:
        break

# Block to check if the user wants to run the code headless or not
chrome_option = Options()
while True:
    is_headless = input("Would you like to run this in the background (Y/N) ? \n")
    if (len(is_headless) == 0):
        print("Sorry, this field cannot be blank")
    else:
        if (is_headless == 'Y'):
            chrome_option.add_argument('--headless=new')
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
except (pd.errors.EmptyDataError, FileNotFoundError):
    jobs_df = pd.DataFrame(columns=jobs_columns)

job_dict = jobs_df.to_dict()

# Initialzing the driver 
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_option)
driver_wait = WebDriverWait(driver,25)

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
    time.sleep(30)
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
    return jobs_array, len(jobs_array)

def job_application(update_job_dict):
    for k,v in update_job_dict['job_link'].items():
        driver.execute_script("window.open('" + v + "')")
        time.sleep(10)
        driver.switch_to.window(driver.window_handles[1])
        driver_wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div[data-hook='container']")))
        job_role_selector = "div[data-hook='container'] > div > h1"
        job_type_selector = "div[data-hook='container'] > div > div[class^= 'style__job-type']"
        company_selector = "a[class^='style__employer-name']"
        location_selector = "a[class^='style__employer-name'] ~ div"
        deadline_selector = "div[data-hook = 'application-deadline'] > div:nth-child(2)"
        posted_date_selector = "div[data-hook = 'posted-date'] > div:nth-child(2)"
        location_type_selector = "div[data-hook = 'location-type'] > div:nth-child(2)"
        update_job_dict['job_role'][k] = driver.find_element(By.CSS_SELECTOR, job_role_selector).text
        update_job_dict['job_type'][k] = driver.find_element(By.CSS_SELECTOR, job_type_selector).text
        update_job_dict['company'][k] = driver.find_element(By.CSS_SELECTOR, company_selector).text
        update_job_dict['location'][k] = driver.find_element(By.CSS_SELECTOR, location_selector).text
        update_job_dict['location_type'][k] = driver.find_element(By.CSS_SELECTOR, location_type_selector).text
        update_job_dict['posted_date'][k] = driver.find_element(By.CSS_SELECTOR, posted_date_selector).text
        update_job_dict['deadline_date'][k] = driver.find_element(By.CSS_SELECTOR, deadline_selector).text
        try:
            time.sleep(3)
            appliedApplication = driver.find_element(By.CSS_SELECTOR, "div[class^='style__application-flow'] > div > div > h2")
            if(appliedApplication.is_displayed()):
                update_job_dict['job_status'][k] = 'Applied'
                driver.execute_script("window.close()")
                driver.switch_to.window(driver.window_handles[0])
                pass
        except (NoSuchElementException, TimeoutException):
            try:
                time.sleep(3)
                applyExternal = driver.find_element(By.CSS_SELECTOR, "button[data-hook='apply-button'] > span > div")
                if((applyExternal.is_displayed()==True) and (applyExternal.text == 'Apply Externally')):
                    update_job_dict['job_status'][k] = 'External Application'
                    driver.execute_script("window.close()")
                    driver.switch_to.window(driver.window_handles[0])
                    pass
                else:
                    WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-hook='apply-button']"))).click()
                    'button[aria-label="' + resume_aria_label + '"]'
                    resumeString = 'button[aria-label="' + resume_aria_label + '"]'
                    transcriptString = 'button[aria-label="' + transcript_aria_label + '"]'
                    submitString = 'span[data-hook="submit-application"] > div > button'
                    try:
                        time.sleep(3)
                        transcriptButton = driver.find_element(By.CSS_SELECTOR, transcriptString)
                        transcriptButton.click()
                        resumeButton = driver.find_element(By.CSS_SELECTOR, resumeString)
                        resumeButton.click()
                        WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, submitString))).click()
                        print("Application Subimtted For ", v)
                        driver.execute_script("window.close()")
                        driver.switch_to.window(driver.window_handles[0])
                        update_job_dict['job_status'][k] = 'Applied'
                    except (NoSuchElementException, TimeoutException):
                        try:
                            time.sleep(3)
                            resumeButton = driver.find_element(By.CSS_SELECTOR, resumeString)
                            resumeButton.click()
                            WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, submitString))).click()
                            print("Application Subimtted For ", v)
                            driver.execute_script("window.close()")
                            driver.switch_to.window(driver.window_handles[0])
                            update_job_dict['job_status'][k] = 'Applied'
                        except (NoSuchElementException, TimeoutException):
                            try:
                                time.sleep(3)
                                WebDriverWait(driver,10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, submitString))).click()
                                print("Application Subimtted For ", v)
                                driver.execute_script("window.close()")
                                driver.switch_to.window(driver.window_handles[0])    
                                update_job_dict['job_status'][k] = 'Applied'
                            except (NoSuchElementException, TimeoutException):
                                update_job_dict['job_status'][k] = 'Failed or Other Reasons'
                                driver.execute_script("window.close()")
                                driver.switch_to.window(driver.window_handles[0])
                                pass
            except (NoSuchElementException, TimeoutException):
                time.sleep(3)
                update_job_dict['job_status'][k] = 'Failed or Other Reasons'
                driver.execute_script("window.close()")
                driver.switch_to.window(driver.window_handles[0])
                pass
    return update_job_dict

    
navigate_to_sso(filter_link, university_name, 
                student_id, student_password) 
duo_sso_login()
update_jobs_array, update_jobs_array_length = job_search_list()
update_job_dict = job_dict

#Adding only new jobs after comparison from previous list into a new update jobs dict
# Regex Pattern to find job id from job links
pattern = re.compile(r'/jobs/(\d+)') 
for i in range(len(update_jobs_array)):
    if update_jobs_array[i] not in list(job_dict['job_link'].values()):
        job_link_len = len(update_job_dict['job_link'].keys())
        update_job_dict['job_link'][job_link_len + 1] = update_jobs_array[i]
        update_job_dict['job_id'][job_link_len + 1] = pattern.search(update_jobs_array[i]).group(1)

update_jobs_df = pd.DataFrame(job_application(update_job_dict))
jobs_df = pd.concat([jobs_df, update_jobs_df], axis=0, ignore_index=True)

#Appending the data back to the file
jobs_df.to_csv(path_to_jobs)