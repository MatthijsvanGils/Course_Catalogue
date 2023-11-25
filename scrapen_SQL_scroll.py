import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import csv
from sqlalchemy import create_engine, text
import re
import sqlalchemy
from sqlalchemy.exc import IntegrityError

# Database connection setup
db_connection_string = os.environ['DB_CONNECTION_STRING']
engine = create_engine(
    db_connection_string,
    connect_args={
        "ssl": {
            "ssl_ca": "/etc/ssl/cert.pem"
        }
    }
)

# Webdriver setup
chrome_options = webdriver.ChromeOptions()

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

# Navigate to the course overview page
url = 'https://uvt.osiris-student.nl/#/onderwijscatalogus/extern/cursussen'
driver.get(url)

time.sleep(5)

# Switch to the English version of the website
osi_language = driver.find_elements(By.CLASS_NAME, 'osi-language')[0]
actions = ActionChains(driver)
actions.move_to_element(osi_language).click().perform()

time.sleep(2)

expand_more_btn = driver.find_elements(By.TAG_NAME, "osi-icon-button")[4]
time.sleep(1)
actions = ActionChains(driver)
actions.move_to_element(expand_more_btn).click().perform()
time.sleep(2)

search_btn = driver.find_elements(By.CLASS_NAME, "button-inner")[13]
time.sleep(1)
actions = ActionChains(driver)
actions.move_to_element(search_btn).click().perform()
time.sleep(2)

k = 18

checkbox = driver.find_elements(By.TAG_NAME, "ion-checkbox")[k]
time.sleep(1)
actions = ActionChains(driver)
actions.move_to_element(checkbox).click().perform()
time.sleep(2)

close = driver.find_elements(By.TAG_NAME, "ion-buttons")[2]
time.sleep(1)
actions = ActionChains(driver)
actions.move_to_element(close).click().perform()
time.sleep(2)

m = 19

while m < 100:

    i = 0
    j = 0  # Reset i and j here

    search_btn = driver.find_elements(By.CLASS_NAME, "button-inner")[13]
    time.sleep(1)
    actions = ActionChains(driver)
    actions.move_to_element(search_btn).click().perform()
    time.sleep(2)

    checkbox = driver.find_elements(By.TAG_NAME, "ion-checkbox")[m]
    time.sleep(1)
    actions = ActionChains(driver)
    actions.move_to_element(checkbox).click().perform()
    time.sleep(2)

    checkbox = driver.find_elements(By.TAG_NAME, "ion-checkbox")[m-1]
    time.sleep(1)
    actions = ActionChains(driver)
    actions.move_to_element(checkbox).click().perform()
    time.sleep(2)

    close = driver.find_elements(By.TAG_NAME, "ion-buttons")[2]
    time.sleep(1)
    actions = ActionChains(driver)
    actions.move_to_element(close).click().perform()
    time.sleep(2)


    soup = BeautifulSoup(driver.page_source, 'html.parser')
    num_courses = soup.find('osi-elastic-search-result').get_text().strip().split("\n")[0].strip()
    num_courses = int(num_courses)

    print(num_courses)

    while i < num_courses:
        # Navigate to and interact with each course page
        course = driver.find_elements(By.TAG_NAME, 'osi-course-item')[i]
        actions = ActionChains(driver)
        actions.move_to_element(course).click().perform()
        print(f'opened course number {i + 1}')
        
        time.sleep(5)

        MAX_RETRIES = 3  # Define how many times you want to retry

        for btn_index in range(11, 14):
            retries = 0  # Reset retry counter for each button
            
            while retries < MAX_RETRIES:
                try:
                    expand_more_btn = driver.find_elements(By.TAG_NAME, "osi-icon-button")[btn_index]
                    time.sleep(1)
                    actions = ActionChains(driver)
                    actions.move_to_element(expand_more_btn).click().perform()
                    time.sleep(4)
                    break  # Exit the retry loop if the action was successful
                    
                except IndexError:
                    print(f"Failed to click button at index {btn_index}. Attempt {retries + 1} of {MAX_RETRIES}.")
                    course = driver.find_elements(By.TAG_NAME, 'osi-course-item')[i]
                    actions = ActionChains(driver)
                    actions.move_to_element(course).click().perform()
                    print(f'opened course number {i + 1}')

                # If you've reached the max retries and still failing, you might want to handle it
                if retries == MAX_RETRIES:
                    print(f"Failed to click button at index {btn_index} after {MAX_RETRIES} attempts. Skipping...")


        # Extract data from the page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        try:
            course_name = soup.find('span', class_='font-heading-1 osi-white text text-md').get_text().strip().split("\n")[0].strip()
        except IndexError:
            course_name = 'Unknown'

        try:
            course_code = soup.find('span', class_='font-heading-1 osi-white text text-md').get_text().strip().split("\n")[1].strip().replace(')', '').replace('(','')
        except IndexError:
            course_code = 'Unknown'

        Degree = "Bachelor" if "B" in course_code else "Master" if "M" in course_code else "Post-master" if "P" in course_code else "Unknown"

        try:
            ECTS = int(course_code.split('-')[-1].replace(')', ''))
        except (IndexError, ValueError):
            ECTS = 'Unknown'

        try:
            language = soup.find_all('osi-body')[0].get_text().strip()
        except IndexError:
            language = 'Unknown'

        try:
            aims = soup.find_all('osi-body')[2].get_text().strip()
        except IndexError:
            aims = 'Unknown'

        try:
            content = soup.find_all('osi-body')[3].get_text().strip()
        except IndexError:
            content = 'Unknown'

        try:
            tests = ', '.join([line.strip() for line in soup.find_all(class_='info-container-body')[0].get_text().strip().split('\n') if line.strip()])
        except IndexError:
            tests = 'Unknown'

        try:
            block = soup.find_all(class_='info-container-body')[1].get_text().strip()
        except IndexError:
            block = 'Unknown'

        try:
            lecturers = ', '.join([line.strip() for line in soup.find_all(class_='info-container-body')[2].get_text().strip().split('\n') if line.strip()])
        except IndexError:
            lecturers = 'Unknown'

        # Navigate back to the course list
        close = driver.find_element(By.CLASS_NAME, "bar-button-clear")
        actions = ActionChains(driver)
        actions.move_to_element(close).click().perform()

        time.sleep(2)

        try:
            school = soup.find_all(class_='font-li-body osi-black-87 font-size-')[j].get_text().replace('School:', '').strip()
        except IndexError:
            school = 'Unknown'

        course_dict = {
            'course_name': course_name, 
            'course_code': course_code,
            'language': language,
            'aims': aims,
            'content': content, 
            'Degree': Degree,
            'ECTS': ECTS,
            'school': school, 
            'tests': tests,
            'block': block,
            'lecturers': lecturers
        }
        
        # Insert data into the database using the engine
        with engine.connect() as conn:
            insert_query = text('''
                INSERT INTO courses_1 (course_name, course_code, language, aims, content, Degree, ECTS, school, tests, block, lecturers)
                VALUES (:course_name, :course_code, :language, :aims, :content, :Degree, :ECTS, :school, :tests, :block, :lecturers)
            ''')

            try:
                conn.execute(insert_query, course_dict)
                print(f'Successfully scraped course number {i + 1}, {course_name}')
            except IntegrityError as e:
                # Handle the duplicate key error here
                # You can update the existing row with the new data
                update_query = text('''
                    UPDATE courses_1
                    SET course_name = :course_name, 
                        language = :language, 
                        aims = :aims, 
                        content = :content, 
                        Degree = :Degree, 
                        ECTS = :ECTS, 
                        school = :school, 
                        tests = :tests, 
                        block = :block, 
                        lecturers = :lecturers
                    WHERE course_code = :course_code
                ''')
                
                conn.execute(update_query, course_dict)
                print(f'Course number {i + 1}, {course_name} already in database')

            time.sleep(5)
            i += 1
            j += 4
        
    # Scroll down to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    m += 1