import requests
import json
from bs4 import BeautifulSoup
import re
import os
import time


class AndroidScraper:
    def __init__(self, compact_url):
        self.compact_url = compact_url
        self.header = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.106 Safari/537.36"
            }
        self.expanded_dict = {}
        self.compact_dict = {}
        self.info_collection = {
            "App name": "",
            "App category": "",
            "URL": "",
            "App ID": "",
            "Average rating": "",
            "Total reviews": "",
            "Contains ads": False,
            "In-app purchases": False,
            "Downloads": "",
            "Price": ""
            }
        self.all_data = {}


    # scrapes all desired app data
    def scrape_data(self):
        # scrapes expanded label info
        # determine expanded label url
        expanded = self.compact_url.split("details?")
        expanded_url = "datasafety?".join(expanded)

        res = requests.get(expanded_url, headers=self.header)
        soup = BeautifulSoup(res.text, 'html.parser')

        data_collection = soup.find_all('h2', {'class': "q1rIdc"})

        for elem in data_collection:
            y = elem.find_next_sibling('div', {'class': "XgPdwe"})

            h3_elements = y.find_all('h3', {'class': "aFEzEb"})
            h4_elements = y.find_all('h4', {'class': "pcmFvf"})
            purposes_elements = y.find_all('div', {'class': "FnWDne"})

            sub_dict = {}

            for h3_elem in h3_elements:
                h3_text = h3_elem.text

                # accounting for no purposes associated with security practices
                if elem.text == "Security practices":
                    data_items = {}
                    sub_dict[h3_text] = None
                
                # all other data type categories
                else:
                    h4_texts = []
                    h4_texts_temp = []
                    purposes_texts = []

                    # accounting for data types ending in " · Optional"
                    for h4_elem, purposes_elem in zip(h4_elements, purposes_elements):
                        if h4_elem.find_previous('h3') == h3_elem:
                            h4_texts_temp.append(h4_elem.text)
                            for type_text in h4_texts_temp:
                                if len(type_text) >= 12 and type_text[-10] == "·":
                                    type_text = type_text[0:-11]
                                    h4_texts.append(type_text)
                                else:
                                    h4_texts.append(type_text)

                            purposes_texts.append(purposes_elem.text)

                    # removes duplicates from list
                    h4_texts = list(dict.fromkeys(h4_texts))

                    data_items = {}
                    for data, purpose in zip(h4_texts, purposes_texts):
                        data_items[data] = [purpose]

                    sub_dict[h3_text] = data_items

            self.expanded_dict[elem.text] = sub_dict


        # scrapes compact label info
        res = requests.get(self.compact_url, headers=self.header)
        soup = BeautifulSoup(res.text, 'html.parser')

        # find compact label info
        raw_data = soup.find_all('div', {'class': "wGcURe"})
        for elem in raw_data:
            compact_list = re.split(r'(?<=[a-z])(?=[A-Z])', elem.text, 1)
            
            # accounting for labels with no description (ex. data can be deleted)
            if len(compact_list) > 1:
                self.compact_dict[compact_list[0]] = compact_list[1]
            else:
                self.compact_dict[compact_list[0]] = None


        # scrapes a lot of app info
        res = requests.get(self.compact_url, headers=self.header)
        soup = BeautifulSoup(res.text, 'html.parser')

        # find app name
        name_data = soup.find('h1', {'itemprop': "name"})
        app_name = name_data.text
        self.info_collection["App name"] = app_name

        # find app categories
        category_data = soup.find_all('div', {'class': "Uc6QCc"})
        for elem in category_data:
            category_list = re.findall('[A-Z][^A-Z]*', elem.text)

            # addresses issue with categories being sliced on a "&"
            for num in range(len(category_list)):
                if category_list[num - 1][-2] == "&":
                    merge_category = str(category_list[num - 1]) + str(category_list[num])
                    category_list.pop(num - 1)
                    category_list.pop(num - 1)
                    category_list.insert(0, merge_category)
            self.info_collection["App category"] = category_list
        
        # find app url
        for link in soup.find_all('link', {'rel': "canonical", 'href': re.compile("^https://")}):
            app_url = link.get('href')
            self.info_collection["URL"] = app_url

        # find app ID
        split_pattern = r"id=|&hl"
        split_result = re.split(split_pattern, app_url)
        app_ID = split_result[1]
        self.info_collection["App ID"] = app_ID

        # finds average app rating
        try:
            rating_data = soup.find('div', {'class': "TT9eCd"})
            temp_app_rating = rating_data.text
            app_rating = temp_app_rating.split("s")
            self.info_collection["Average rating"] = app_rating[0]
        
        except:
            self.info_collection["Average rating"] = "No ratings"

        # finds total number of reviews
        reviews_data = soup.find('div', {'class': "g1rdde"})
        app_reviews_list = reviews_data.text.split()
        app_reviews = app_reviews_list[0]
        if app_reviews != "Downloads":
            if app_reviews[-1] == "M":  # addresses rating num ending in millions
                app_reviews = app_reviews[0:-1] + "000000"
            elif app_reviews[-1] == "K":  # addresses rating num ending in thousands
                app_reviews = app_reviews[0:-1] + "000"
            app_reviews = app_reviews.replace(".", "")
            self.info_collection["Total reviews"] = app_reviews
        else:
            self.info_collection["Total reviews"] = "No reviews"

        # finds whether the app contains ads or has in-app purchases
        in_app_data_list = soup.find_all('span', {'class': "UIuSk"})
        for elem in in_app_data_list:
            if elem.text == "Contains ads":
                self.info_collection["Contains ads"] = True
            elif elem.text == "In-app purchases":
                self.info_collection["In-app purchases"] = True
        
        # finds num of downloads
        downloads_data = soup.find_all('div', {'class': "wVqUob", 'class': "ClM7O"})

        # checker for if app has ratings/reviews or not
        if len(downloads_data) > 2 and downloads_data[1].text != "":
            num_downloads = downloads_data[1].text
        else:
            num_downloads = downloads_data[0].text
        
        if num_downloads[-2] == "M":  # addresses rating num ending in millions
            num_downloads = num_downloads[0:-2] + "000000+"
        elif num_downloads[-2] == "K":  # addresses rating num ending in thousands
            num_downloads = num_downloads[0:-2] + "000+"
        elif num_downloads[-2] == "B":  # addresses rating num ending in billions
            num_downloads = num_downloads[0:-2] + "000000000+"
        self.info_collection["Downloads"] = num_downloads
        
        # grabs price of the app
        price_data = soup.find('meta', {'itemprop': "price"})
        price_data_list = (str(price_data)).split('"')
        if len(price_data_list[1]) >= 2:
            app_price = price_data_list[1]
            self.info_collection["Price"] = app_price
        else:
            app_price = "$" + price_data_list[1] + ".00"
            self.info_collection["Price"] = app_price

        # combines all data collections into one dictionary
        self.all_data = {**self.info_collection, **self.compact_dict, **self.expanded_dict}
    

    def write_to_json(self):
        """
        Writes all the scraped and computed data to a JSON file.
        No parameters or return values.
        """
        directory_path = 'json_android_files'
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        file_path = os.path.join(directory_path, str(self.info_collection['App ID']) + '.json')

        with open(file_path, "w") as file:
            json.dump(self.all_data, file, indent=4)    


# def crawl_app_links(url):
#     try:
#         if url in processed_apps:  # base case
#             return
#         print(f"processing link: {url}")
#         app = AndroidScraper(url)
#         app.scrape_data
#         app.write_to_json()
#         processed_apps[url] = True
#         similar_apps = similar_app_scraper(url)
#         for link in similar_apps:  # recurisve case
#             if link in processed_apps:
#                 continue
#             else:
#                 crawl_app_links(link)
    
#     except Exception as e:
#         print(f"error occured at URL: {url} - {e}")



# def main():
#     start_time = time.time()

    
#     base_url = "https://play.google.com/store/apps/details?id="
#     basic_url = "https://play.google.com/store/apps/details?id=com.snapchat.android"
#     # basic_url = "https://play.google.com/store/apps/details?id=com.mojang.minecraftpe"
#     master_list = ["com.snapchat.android"]
#     count = 0

#     # # for loop that looks for similar app urls of apps in the master_list
#     # for url in master_list:
#     #     # just scrapes urls for certain num of apps
#     #     if count > 100:
#     #         break
#     #     full_url = base_url + url
#     #     basic_results = similar_app_scraper(full_url)
#     #     master_results = url_list(master_list, basic_results)
#     #     count += 1
    
#     # print(len(master_results))

#     # for url in master_results:
#     # compact_url = base_url + url
#     # scrapes all app data and saves it to a file
#     scrape = AndroidScraper(basic_url)
#     scrape.scrape_data()
#     scrape.write_to_json()

#     end_time = time.time()
#     print(end_time-start_time)


# if __name__ == "__main__":
#     main()
