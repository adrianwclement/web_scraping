import requests
import json
from bs4 import BeautifulSoup

class DataScraper:
    def __init__(self, url, header):
        self.url = url
        self.header = header
        self.data_dict = {}

    def scrape_data(self):
        res = requests.get(self.url, headers=self.header)
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
                h4_texts = []
                purposes_texts = []

                for h4_elem, purposes_elem in zip(h4_elements, purposes_elements):
                    if h4_elem.find_previous('h3') == h3_elem:
                        h4_texts.append(h4_elem.text)
                        purposes_texts.append(purposes_elem.text)

                data_items = {}
                for data, purpose in zip(h4_texts, purposes_texts):
                    data_items[data] = [purpose]

                sub_dict[h3_text] = data_items

            self.data_dict[elem.text] = sub_dict

    def save_data_to_file(self, filename):
        # Serializing json
        json_object = json.dumps(self.data_dict, indent=4)
        with open(filename, 'w') as file:
            json.dump(self.data_dict, file)
            file.write(json_object)


url= "https://play.google.com/store/apps/datasafety?id=com.facebook.katana"
header ={
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.106 Safari/537.36"
}
filename = 'android_data.json'


scraper = DataScraper(url, header)
scraper.scrape_data()
scraper.save_data_to_file(filename)
