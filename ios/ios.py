from bs4 import BeautifulSoup, NavigableString
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import os 
import json

class iOS:
    def __init__(self, url):
        self.url = url
        
        self.header = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.137 Safari/537.36"
        }
        #self.service = Service('/Users/earnsmacbookair/Desktop/chromedriver_mac64/chromedriver')
        self.service = Service('../../chromedriver_mac64/chromedriver')
        
        self.compact_count = {}
        
        self.expanded_count = {}

        self.app_info = {}
                
        self.compact_dict = {}
        
        self.data_linked = {}
        
        self.data_not_linked = {}
        
        self.data_track = {}
        
        self.update_collection_categories() # update data_linked, data_not_linked, data_track dictionary
        
        self.scrape_compact_labels() # update the compact label dictionary
        
        self.scrape_appinfo() # update the app info dictionary
        
        self.count_labels() # update the total count dictionaries (compact and expanded)
        
        
    def list_to_text(self, content_list):
        """Converts a BeautifulSoup ResultSet to a list of strings. 
        Each element in the ResultSet is converted to its text representation.

        Args:
            content_list (bs4.element.ResultSet): A ResultSet object containing the HTML elements to be converted into text.

        Returns:
            list: a list of strings
        """
        res = []
        for elem in content_list:
            res.append(elem.text.strip())
        return res
    
    def convert_shorthand_to_number(self,shorthand):
        """
        Converts shorthand notation to a full number.
        E.g. 7.5M -> 7500000, 5K -> 5000

        Args:
            shorthand (str): Shorthand notation to be converted.

        Returns:
            float: Converted number.
        """
        if shorthand[-1].upper() == 'M':
            return float(shorthand[:-1]) * 1e6
        elif shorthand[-1].upper() == 'K':
            return float(shorthand[:-1]) * 1e3
        else:
            return float(shorthand)
    
    def scrape_appinfo(self):
        """
        Fetches the app information from the URL and stores it in a dictionary called app_info.

        No parameters or return values.
        """
        res = requests.get(self.url, headers=self.header)
        if res.status_code == requests.codes.ok:
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Find the title
            title = soup.find('h1', {'class': "product-header__title app-header__title"}).get_text(strip=True)
            
            # Find the age rating
            age_dt = soup.find('dt', string='Age Rating')
            age_dd = age_dt.find_next_sibling('dd')
            age_rating = "".join(t for t in age_dd.contents if isinstance(t, NavigableString)).strip()
            if "," in age_rating:
                age = age_rating.split(",")
                rating = age[0]
                kids = age[1]
            else:
                rating = age_rating
                kids = False

            # Find the category
            category_dt = soup.find('dt', string='Category')
            category_dd = category_dt.find_next_sibling('dd')
            category = category_dd.get_text(strip=True)
            
            # Find the price
            price_dt = soup.find('dt', string='Price')
            price_dd = price_dt.find_next_sibling('dd')
            price = price_dd.get_text(strip=True)

            # Find the ratings
            ratings = soup.find("figcaption", {"class": "we-rating-count star-rating__count"})
            if ratings == None:
                app_rating = 0.0
                no_of_rating = 0
            else: 
                ratings = ratings.get_text(strip=True).split()
                app_rating = float(ratings[0])
                no_of_rating = int(self.convert_shorthand_to_number(ratings[2]))
            
            # Find in App Purchases
            app_purchases = soup.find("li", {"class", "inline-list__item inline-list__item--bulleted app-header__list__item--in-app-purchase"})
            if app_purchases == None:
                app_purchases = False
            else:
                app_purchases = True
                
            # Add URL and get ID from it 
            app_id = self.url.split("/id")[-1]
            
            self.app_info = {"App Name": title,
                            "App Category": category,
                            "URL": self.url, 
                            "App ID": int(app_id), 
                            "Price": price, 
                            "App Rating": app_rating, 
                            "No. of Ratings": no_of_rating,
                            "Offers In-App Purchases": app_purchases,
                            "Age Rating": rating,
                            "Kids": kids}
        else:
            print(f"Error fetching URL: {self.url} - Status code: {res.status_code}")
                         
    def scrape_compact_labels(self):
        """
        Scrapes the compact privacy labels from the URL and stores it in a dictionary called compact_dict.

        No parameters or return values.
        """
        res = requests.get(self.url, headers=self.header)
        if res.status_code == requests.codes.ok:
            soup = BeautifulSoup(res.text, "html.parser")
            try:
                cards = soup.find_all("div", {'class': "app-privacy__card"})
                for card in cards:
                    collection_cat = card.find("h3", {'class':"privacy-type__heading"}).text
                    if collection_cat == "No Details Provided" or collection_cat == "Data Not Collected":
                        description = card.find("p", {'class':"privacy-type__description"}).text.strip()
                        self.compact_dict[collection_cat] = [description]
                    else:
                        items = card.find("ul",{"class":"privacy-type__items"})
                        self.compact_dict.setdefault(collection_cat, [])
                        category = items.find_all('span', {'class': "privacy-type__grid-content privacy-type__data-category-heading"})
                        category_text = self.list_to_text(category)
                        self.compact_dict[collection_cat].extend(category_text)
            except AttributeError as e:
                print(f"Failed to scrape compact label. Unable to find element: {e}")
        else: 
                print(f"Error fetching URL: {self.url} - Status code: {res.status_code}")
            
            
    def update_collection_categories(self):
        """
        Fetches data from the app's expanded privacy section using Selenium.
        The data is stored in three dictionaries, data_linked, data_not_linked and data_track

        No parameters or return values.
        """
        # Set up the WebDriver
        # creating selenium service
        driver = webdriver.Chrome(service=self.service) # creating web browser instance 

        # Open the url
        driver.get(self.url)

        # Wait for the page to load completely
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//button[text()="See Details"]')))

        # Click the button to open the pop up
        button = driver.find_element(By.XPATH, '//button[text()="See Details"]')
        
        try:
            # button.click()
            driver.execute_script("arguments[0].click();", button)
        except Exception as e:
            print(f"An error occurred when trying to click the button: {e}")

        # Wait for the modal content to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "app-privacy__modal-section")))

        # Now the pop up should be open, so you can get its content
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        try: 
            
            modal_content_sections = soup.find_all("div", {'class':"app-privacy__modal-section"})
            for header in modal_content_sections:
                collection_cat = header.find("h2", {'class':"privacy-type__heading"})
                if collection_cat != None:
                    if collection_cat.text == "Data Linked to You":
                        # Find all h3 and div tags of interest
                        tags = header.find_all(['h3', 'div'], {'class': ['privacy-type__purpose-heading', 'privacy-type__grid']})
                        purpose = ''  # Variable to hold the current purpose
                        for tag in tags:
                            if 'privacy-type__purpose-heading' in tag['class']:
                                # If the tag is a purpose heading, update the current purpose
                                purpose = tag.text.strip()
                                if purpose == "Developer’s Advertising or Marketing":
                                    purpose = "Developer's Advertising or Marketing"
                            elif 'privacy-type__grid' in tag['class']:
                                content = tag.find("div", {"class":"privacy-type__grid-content"})
                                category = content.find("h4",{"class": "privacy-type__data-category-heading"}).text.strip()
                                type_list = content.find_all("li")
                            
                                self.data_linked.setdefault(purpose, {})
                                
                                for elem in type_list:
                                    type = elem.text.strip()
                                    
                                    self.data_linked[purpose].setdefault(category, [])
                                    
                                    self.data_linked[purpose][category].append(type)
                                    
                    elif collection_cat.text == "Data Not Linked to You":
                        # Find all h3 and div tags of interest
                        tags = header.find_all(['h3', 'div'], {'class': ['privacy-type__purpose-heading', 'privacy-type__grid']})
                        purpose = ''  # Variable to hold the current purpose
                        for tag in tags:
                            if 'privacy-type__purpose-heading' in tag['class']:
                                # If the tag is a purpose heading, update the current purpose
                                purpose = tag.text.strip()
                                if purpose == "Developer’s Advertising or Marketing":
                                    purpose = "Developer's Advertising or Marketing"
                            elif 'privacy-type__grid' in tag['class']:
                                content = tag.find("div", {"class":"privacy-type__grid-content"})
                                category = content.find("h4",{"class": "privacy-type__data-category-heading"}).text.strip()
                                type_list = content.find_all("li")
                                
                                self.data_not_linked.setdefault(purpose, {})
                                
                                for elem in type_list:
                                    type = elem.text.strip()
                                    
                                    self.data_not_linked[purpose].setdefault(category, [])

                                    self.data_not_linked[purpose][category].append(type)
                                    
                                    
                    elif collection_cat.text == "Data Used to Track You":
                        grids = header.find_all("div", {'class':"privacy-type__grid"})
                        for cat in grids:
                            content = cat.find("div", {"class":"privacy-type__grid-content"})
                            category = content.find("h3",{"class": "privacy-type__data-category-heading"}).text.strip()
                            type_list = content.find_all("li")
                                
                            self.data_track.setdefault(category, [])
                            
                            for elem in type_list:
                                type = elem.text.strip()
                                
                                self.data_track[category].append(type)
                            
        except AttributeError as e:
            print(f"Failed to scrape expanded label. Unable to find element: {e}")    
        
        finally:
            # Always quit the driver, whether an exception occurred or not
            driver.quit()           
                
                            
    def count_labels(self):
        """
        Counts the occurrences of each term in the compact and expanded privacy labels and stores the 
        results in two dictionaries called compact_count and expanded_count

        No parameters or return values.
        """
        for data_dict in [self.data_linked, self.data_not_linked]:
            for purpose, categories in data_dict.items():
                # Update the count for the purpose 
                self.expanded_count.setdefault(purpose, 0)
                self.expanded_count[purpose] += 1
                
                for category, types in categories.items():
                    # Update the count for the category word
                    self.expanded_count.setdefault(f'category_{category}', 0)
                    self.expanded_count[f'category_{category}'] += 1

                    # Update the count for each type word
                    for type_word in types:
                        self.expanded_count.setdefault(f'type_{type_word}', 0)
                        self.expanded_count[f'type_{type_word}'] += 1
                        
        # Process self.data_track separately
        for category, types in self.data_track.items():
            # Update the count for the category word
            self.expanded_count.setdefault(f'category_{category}', 0)
            self.expanded_count[f'category_{category}'] += 1

            # Update the count for each type word
            for type_word in types:
                self.expanded_count.setdefault(f'type_{type_word}', 0)
                self.expanded_count[f'type_{type_word}'] += 1
                
        for collection_cat, category in self.compact_dict.items():
            self.compact_count.setdefault(collection_cat, 0)
            self.compact_count[collection_cat] += 1
            
            for cat in category:
                self.compact_count.setdefault(cat, 0)
                self.compact_count[cat] += 1
    
    
    def get_expanded_count(self, string, category=False, type=False):
        """_summary_

        Args:
            string (str): The term to look for.
            category (bool, optional): Whether to search for category. Defaults to False.
            type (bool, optional): Whether to search for type. Defaults to False.

        Returns:
            tuple: The term it looked for and the count of the term in the expanded privacy labels.
        """
        # Normalize the string to lower case and remove spaces
        normalized_string = string.lower().replace(" ", "")
        
        if category:
            key_prefix = 'category_'
        elif type: 
            key_prefix = 'type_'
        else:
            key_prefix = ''

        # Normalize the keys to lower case and remove spaces
        normalized_dict = {k.lower().replace(" ", ""): v for k, v in self.expanded_count.items()}

        # Key for search
        search_key = key_prefix + normalized_string
        
        # Return key
        return_key = key_prefix + string

        # Return the count from the dictionary
        return (return_key, normalized_dict.get(search_key, 0))
            
    
    def get_compact_count(self, string):
        """Returns the count of a given term in the compact privacy labels.

        Args:
            string (str): The term to look for.

        Returns:
            int: The count of the term in the compact privacy labels.

        """
        # Normalize the string to lower case and remove spaces
        normalized_string = string.lower().replace(" ", "")
        
        # Normalize the keys to lower case and remove spaces
        normalized_dict = {k.lower().replace(" ", ""): v for k, v in self.compact_count.items()}
        
        # Return the count from the dictionary
        return normalized_dict.get(normalized_string, 0)
        
                            
    def write_to_json(self):
        """
        Writes all the scraped and computed data to a JSON file.

        No parameters or return values.
        """
        directory_path = 'json_files'
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        all_data = {
            "app_info": self.app_info,
            "compact_dict": self.compact_dict,
            "data_linked": self.data_linked,
            "data_not_linked": self.data_not_linked,
            "data_track": self.data_track,
        }

        file_path = os.path.join(directory_path, str(self.app_info['App ID']) + '.json')

        with open(file_path, "w") as file:
            json.dump(all_data, file, indent=4)
                            

def main():
    # instagram = iOS("https://apps.apple.com/us/app/instagram/id389801252")
    # instagram.write_to_json()
    
    # game = iOS("https://apps.apple.com/us/app/slay-the-spire/id1491530147")
    # game = iOS("https://apps.apple.com/us/app/device-6/id680366065")

    # print(game.compact_dict)
    # game.write_to_json()
    
    # app = iOS("https://apps.apple.com/us/app/slay-the-spire/id1491530147")
    app = iOS("https://apps.apple.com/us/app/stars-and-planets/id1170904676")
    print(app.app_info)
    app.scrape_appinfo()
    print(app.compact_count)
    print(app.expanded_count)
    # app.write_to_json()

    # print(instagram.app_info)
    # print(instagram.compact_dict)
    # print(instagram.get_expanded_count("other purposes"))
    # print(instagram.get_expanded_count("analytics"))
    # print(instagram.get_expanded_count("contacts", type=True))
    # print(instagram.get_expanded_count("contacts", category=True))

# "https://apps.apple.com/us/app/slay-the-spire/id1491530147" - "data not collected"
# "https://apps.apple.com/us/app/device-6/id680366065" - "no details provided"

# https://apps.apple.com/us/genre/ios-books/id6018

if __name__ == "__main__":
    main()
                    
                    
