from bs4 import BeautifulSoup, NavigableString, Tag
import requests
import json
import re

url = 'https://www.aonprd.com/'

class ArchetypeScraper:
    def __init__(self, url):
        self.url = url
        self.href = f'Inquisitions.aspx'
        self.page = requests.get(url + self.href)
        self.soup = BeautifulSoup(self.page.content, 'html.parser')
        self.table = self.soup.find("table")


    def clean_text(self, text):
        # Replace Unicode right single quotation mark with an apostrophe
        cleaned_text = [line.replace('\u2019', "'").replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"') for line in text.split('\n') if line.strip() and line.strip() != "."]
        return ' '.join(cleaned_text).strip()
    
    def remove_parenthesis(self, input_string):
        pattern = r"\(.*?pg\..*?\)"
        result = re.sub(pattern, '', input_string)
        return result
    

# What we want to do is to get the data once we see a <b> tag, use the <b> tag as the key section
# Since it's going to be the same each time we can manually set them (like in the items json file)
    def span_search(self, td_tags):
        # Initialize an empty list to store dictionaries for each iteration
        all_data_dicts = []

        b_tags = self.soup.find_all('b')
        i_tags = self.soup.find_all('i')
        # Initialize an empty dictionary to store the data for this iteration

        for td in td_tags:
            print(td)
            data_dict = {}


        # Append the data dictionary to the list for this iteration
        all_data_dicts.append(data_dict)
                                #{order_name: data_dict}

        # Convert the list of dictionaries to JSON format and print it
        json_output = json.dumps(all_data_dicts, indent=2)
        print(json_output)

  
            

    def get_class_info(self):
        td_tags = list(self.soup.find_all('td'))
        self.span_search(td_tags)            

# Instantiate the ArchetypeScraper class
scraper_instance = ArchetypeScraper(url)

# Call the get_class_info method
scraper_instance.get_class_info()