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
print(requirement_path)
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

# Create a path to the file in your computer
path_to_jobs = Path(input("Please enter the path where you want the jobs to stored or already have stored \n"))
path_to_jobs.touch(exist_ok=True)

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

