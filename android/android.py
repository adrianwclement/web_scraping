header = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.106 Safari/537.36"
}
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time

def scrape_all_pages(url):
    s = Service("/Users/eusilakitur/Downloads/chromedriver_mac64/chromedriver")
    driver = webdriver.Chrome(service=s)
    driver.get(url)
    prefix = "https://play.google.com "
    scraped_data = []

    old_scroll_position = 0
    new_scroll_position = None

    while new_scroll_position != old_scroll_position:
        old_scroll_position = driver.execute_script("return window.scrollY;")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_scroll_position = driver.execute_script("return window.scrollY;")
        

    # Create BeautifulSoup object with the page source
    soup = BeautifulSoup(driver.page_source, "html.parser")

    # Scrape the desired data
    links = soup.find_all("a", {'class':"Si6A0c ZD8Cqc"})
    scraped_data.extend([prefix + link['href'] for link in links if 'href' in link.attrs])

    # Close the Selenium WebDriver
    driver.quit()

    return scraped_data

# Example usage
url = 'https://play.google.com/store/apps'

scraped_data = scrape_all_pages(url)

# Print the scraped data
print(scraped_data)
print(len(scraped_data))