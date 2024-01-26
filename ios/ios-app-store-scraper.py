import json
from bs4 import BeautifulSoup
import requests
from ios import iOS
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import queue 

class AppStoreScraper:
    def __init__(self):
        self.header = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.5615.137 Safari/537.36"
        }
        
        #self.service = Service('/Users/earnsmacbookair/Desktop/chromedriver_mac64/chromedriver')        
        self.service = Service('../../../chromedriver_mac64/chromedriver')
        
        self.driver = None

        self.categories = {
            "weather-apps": "6001",
            "utilities-apps": "6002",
            "travel-apps": "6003",
            "sports-apps": "6004",
            "social-networking-apps": "6005",
            "shopping-apps": "6024",
            "reference-apps": "6006",
            "productivity-apps": "6007",
            "photo-video-apps": "6008",
            "news-apps": "6009",
            "navigation-apps": "6010",
            "music-apps": "6011",
            "medical-apps": "6020",
            "magazines-newspapers-apps": "6021",
            "lifestyle-apps": "6012",
            "health-fitness-apps": "6013",
            "graphics-design-apps": "6027",
            "food-drink-apps": "6023",
            "finance-apps": "6015",
            "entertainment-apps": "6016",
            "education-apps": "6017",
            "developer-tools-apps": "6026",
            "business-apps": "6000",
            "books-apps": "6018",
            "action-games": "7001",
            "adventure-games": "7002",
            "board-games": "7004",
            "card-games": "7005",
            "casino-games": "7006",
            "casual-games": "7003",
            "family-games": "7009",
            "music-games": "7011",
            "puzzle-games": "7012",
            "racing-games": "7013",
            "role-playing-games": "7014",
            "simulation-games": "7015",
            "sports-games": "7016",
            "strategy-games": "7017",
            "trivia-games": "7018",
            "word-games": "7019"
        }
        self.chart_types = ["top-free", "top-paid"]
        self.base_url = "https://apps.apple.com/us/charts/iphone/{category}/{id}?chart={chart_type}"
        self.kids_apps = ["https://apps.apple.com/us/charts/iphone/kids-apps/36?ageId=0&ageId=0&chart=top-free",
        "https://apps.apple.com/us/charts/iphone/kids-apps/36?ageId=0&ageId=0&chart=top-paid"]

        self.top_charts = ["https://apps.apple.com/us/charts/iphone/top-free-apps/36",
                    "https://apps.apple.com/us/charts/iphone/top-paid-apps/36",
                    "https://apps.apple.com/us/charts/iphone/top-free-games/6014",
                    "https://apps.apple.com/us/charts/iphone/top-paid-games/6014"]
        
        self.links = []
        
        self.processed_apps = {}
            
        self.generate_links()
        
    def load_processed_apps(self, directory):
        """Loads the names of the processed apps from a given directory into the processed_apps dictionary.

        Args:
            directory (str): Directory where the JSON files are stored.
        """
        for filename in os.listdir(directory):
            if filename.endswith(".json"):  # make sure the files are .json
                app_name = filename.rstrip('.json')  # remove .json from filename to get app name
                self.processed_apps[app_name] = True
                
    def generate_links(self):
        """Generates a list of links for each category and chart type 
        and extends it with kids apps and top charts links.

        No parameters or return values.
        """
        for category, id in self.categories.items():
            for chart_type in self.chart_types:
                link = self.base_url.format(category=category, id=id, chart_type=chart_type)
                if link is not None:
                    self.links.append(link)

        self.links.extend(self.kids_apps)
        self.links.extend(self.top_charts)

    def search_app_link(self, url):
        """Searches for app links on the given URL page.

        Args:
            url (str): URL of the page to search for app links.

        Returns:
            list[str]: List of app links found on the page.
        """
        res = requests.get(url, headers=self.header)
        if res.status_code == requests.codes.ok:
            soup = BeautifulSoup(res.text, "html.parser")
            
            links = soup.find_all("a", {'class': "we-lockup targeted-link"})

            urls = [link['href'] for link in links if 'href' in link.attrs]
            
            return urls
    
    def scroll_to_bottom(self):
        """Scrolls to the bottom of the page using JavaScript.

        """
        old_scroll_position = 0
        new_scroll_position = None

        while new_scroll_position != old_scroll_position:
            old_scroll_position = self.driver.execute_script(
                "return window.scrollY;"
            )
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(2)
            new_scroll_position = self.driver.execute_script(
                "return window.scrollY;"
            )
    
    def search_see_all_links_scroll(self, url):
        """Scrolls page and searches for all links on the given URL page.

        Args:
            url (str): URL of the page to search for all links.

        Returns:
            list[str]: List of all links found on the page.
        """
        
        self.driver = webdriver.Chrome(service=self.service)
        self.driver.get(url)

        # Scrolls to the bottom of the page
        self.scroll_to_bottom()
        
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        
        links = soup.find_all("a", {'class': "we-lockup targeted-link l-column--grid small-valign-top we-lockup--in-app-shelf l-column small-6 medium-3 large-2"})

        urls = [link['href'] for link in links if 'href' in link.attrs]
            
        self.driver.quit()
        
        return urls
    
    def search_see_all_links(self, url):
        """Searches for all links on the given URL page.

        Args:
            url (str): URL of the page to search for all links.

        Returns:
            list[str]: List of all links found on the page.
        """
        res = requests.get(url, headers=self.header)
        if res.status_code == requests.codes.ok:
            
            soup = BeautifulSoup(res.text, "html.parser")
            
            links = soup.find_all("a", {'class': "we-lockup targeted-link l-column--grid small-valign-top we-lockup--in-app-shelf l-column small-6 medium-3 large-2"})

            urls = [link['href'] for link in links if 'href' in link.attrs]
                            
            return urls
        
    def create_see_all_link(self, url):
        """Creates a URL for the 'See All' page.

        Args:
            url (str): Base URL to append the 'See All' query parameter to.

        Returns:
            str: URL for the 'See All' page.
        """
        see_all_page = url + "?see-all=customers-also-bought-apps"
        
        return see_all_page

    def crawl_app_links(self):
        """
        Run BFS and process each valid link
        """
      
        working_queue = queue.SimpleQueue()  
        
        working_dict = {}
        try: 
            print(self.processed_apps)

            for link in self.links:
                app_links = self.search_app_link(link)
                for app in app_links:
                    app_key = app.split("/id")[-1]
                    if app_key in working_dict or app_key in self.processed_apps:
                        continue
                    working_dict[app_key] = True
                    working_queue.put(app)
                    
            print(f"The queue currently has {working_queue.qsize()} items.")
                
        except Exception as e:
                print(f"Error occurred at URL: {app} - {e}")
        
        while not working_queue.empty():
            url = working_queue.get()
            
            try:
                if url.split("/id")[-1] in self.processed_apps:
                    continue
                
                print(f"Processing link: {url}")
                app = iOS(url) 
                app.write_to_json()
                
                self.processed_apps[url.split("/id")[-1]] = True
                
                see_all_link = self.create_see_all_link(url) # create the see all page link
                app_links = self.search_see_all_links(see_all_link)  # create list of valid links
                
                for link in app_links:
                    if link.split("/id")[-1] not in self.processed_apps:
                        working_queue.put(link)
                        
            except Exception as e:
                print(f"Error occurred at URL: {url} - {e}")
    
    def load_json_and_generate_queue(self, directory):
        """
        Loads JSON files from the given directory, extracts the URL, and applies 
        the `create_see_all_link` and `search_see_all_links` functions to generate a queue
        of app links.
        """
        working_queue = queue.SimpleQueue()

        # Load the JSON files
        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                with open(os.path.join(directory, filename)) as f:
                    data = json.load(f)

                url = data['app_info']['URL']  # extract the URL

                see_all_link = self.create_see_all_link(url)  # create the see all page link
                app_links = self.search_see_all_links(see_all_link)  # create list of valid links

                for link in app_links:
                    if link.split("/id")[-1] not in self.processed_apps:
                        working_queue.put(link)

        return working_queue
    
    def restart_crawler(self, directory):
        """
        Restarts the crawling process by loading the processed apps, 
        generating the queue of app links from the JSON files, and 
        processing the links in the queue.
        """

        # Load JSON files and generate queue
        working_queue = self.load_json_and_generate_queue(directory)

        # Continue processing as per the crawl_app_links function
        while not working_queue.empty():
            url = working_queue.get()

            try:
                if url.split("/id")[-1] in self.processed_apps:
                    continue

                print(f"Processing link: {url}")
                app = iOS(url) 
                app.write_to_json()

                self.processed_apps[url.split("/id")[-1]] = True

                see_all_link = self.create_see_all_link(url) # create the see all page link
                app_links = self.search_see_all_links(see_all_link)  # create list of valid links

                for link in app_links:
                    if link.split("/id")[-1] not in self.processed_apps:
                        working_queue.put(link)

            except Exception as e:
                print(f"Error occurred at URL: {url} - {e}")
        
def main():
    directory = "json_files"
    scrape = AppStoreScraper()
    scrape.load_processed_apps(directory)
    scrape.restart_crawler(directory)
    # scrape.crawl_app_links()  


if __name__ == "__main__":
    main()
