from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import pandas as pd
import smtplib
import configparser
from email.message import EmailMessage
from pathlib import Path
import schedule
import time as tm


def scraper(driver,url,max_pages):

    driver.get(url)
    results= []
    
    decline_cookies = driver.find_element(By.CSS_SELECTOR,".cc-nb-reject")
    decline_cookies.click()

    link = driver.find_element(By.PARTIAL_LINK_TEXT, "Koně")
    link.click()

    page_counter = 0

    while page_counter< max_pages:
        items =  driver.find_elements(By.CSS_SELECTOR,".inzeraty")

        for itemId in range(len(items)):
            items = driver.find_elements(By.CSS_SELECTOR, ".inzeraty")
            items[itemId].find_element(By.CSS_SELECTOR,".nadpis a").click()
            ad_name = driver.find_element(By.CSS_SELECTOR,"h1").text
            price = driver.find_element(By.XPATH, "/html/body/div/div[3]/div[2]/table/tbody/tr/td[1]/table/tbody/tr[5]/td[2]/b").text
            contact_name = driver.find_element(By.XPATH, "/html/body/div/div[3]/div[2]/table/tbody/tr/td[1]/table/tbody/tr[1]/td[2]/b/span").text
            contact_number = driver.find_element(By.XPATH, "/html/body/div/div[3]/div[2]/table/tbody/tr/td[1]/table/tbody/tr[2]/td[2]/span/span").text
            contact_locality = driver.find_element(By.XPATH, "/html/body/div/div[3]/div[2]/table/tbody/tr/td[1]/table/tbody/tr[3]/td[3]/a[2]").text
            ad_date = driver.find_element(By.XPATH,"/html/body/div/div[3]/div[2]/div[1]/div[1]/span").text.split("[")[-1]
            ad_date = ad_date[:-1].strip()
            ad_text = driver.find_element(By.XPATH,"/html/body/div/div[3]/div[2]/div[3]").text

            
            results.append((ad_name,price,contact_name,contact_number,contact_locality, ad_date,ad_text))


            driver.back()
        try:
            next_page = driver.find_element(By.XPATH,"/html/body/div/div[3]/div[2]/div[25]/a[8]")
            next_page.click()
            page_counter += 1

        except NoSuchElementException:
            print("No element found")
            break
        
    driver.quit()
    return results

def send_email(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)

    smtp_server = config.get("SMTP", "smtp_server")
    smtp_port = config.getint("SMTP", "smtp_port")
    smtp_username = config.get("AUTHENTICATION", "username")
    smtp_password = config.get("AUTHENTICATION", "password")

    msg_subject = config.get("EMAIL_CONTENTS", "SUBJECT")
    msg_from = config.get("EMAIL_CONTENTS", "FROM")
    msg_recipients = config.get("EMAIL_CONTENTS", "RECIPIENTS").split(",")
    msg_content = config.get("EMAIL_CONTENTS", "CONTENT")
    msg_attachment_path = config.get("EMAIL_CONTENTS","ATTACHMENT")

    msg_attachment_path = Path(msg_attachment_path)

    msg = EmailMessage()
    msg["Subject"] = msg_subject
    msg["From"] = msg_from
    msg["To"] = msg_recipients
    msg.set_content(msg_content)

    with msg_attachment_path.open("rb") as fp:
        msg.add_attachment(
            fp.read(),
            maintype="text", subtype="csv",
            filename=msg_attachment_path.name
        )

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            print("Connecting...")
            smtp.starttls()
            smtp.ehlo()
            smtp.login(smtp_username, smtp_password)
            print("Connection successful!")
            smtp.send_message(msg)
            print("Email sent successfully!")
    except Exception as e:
        print("Connection failed:", e)

def scrape_then_send_email():
    driver = webdriver.Firefox()
    url = "https://www.bazos.cz/"

    results = scraper(driver,url,3)

    df = pd.DataFrame(results, columns=["Ad_name", "Price", "Contact_name", "Contact_number", "Contact_locality", "Ad_date", "Ad_desc"])
    df.to_csv("output.csv", index=False)

    send_email("settings.config")

def main():
    config = configparser.ConfigParser()
    config.read("settings.config")

    interval = config.get("SCHEDULE", "INTERVAL").lower()
    time = config.get("SCHEDULE", "TIME")
    print(f"The script will be executed every {interval} at {time}")

    if interval == "day":
        schedule.every().day.at(time).do(scrape_then_send_email)
    elif interval == "monday":
        schedule.every().monday.at(time).do(scrape_then_send_email)
    elif interval == "tuesday":
        schedule.every().tuesday.at(time).do(scrape_then_send_email)
    elif interval == "wednesday":
        schedule.every().wednesday.at(time).do(scrape_then_send_email)
    elif interval == "thursday":
        schedule.every().thursday.at(time).do(scrape_then_send_email)
    elif interval == "friday":
        schedule.every().friday.at(time).do(scrape_then_send_email)
    elif interval == "saturday":
        schedule.every().saturday.at(time).do(scrape_then_send_email)
    elif interval == "sunday":
        schedule.every().sunday.at(time).do(scrape_then_send_email)
    
    while True:
        schedule.run_pending()
        tm.sleep(1)


if __name__ == "__main__":
    main()