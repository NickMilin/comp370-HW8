from bs4 import BeautifulSoup
import re
import requests
import argparse
import json
import os
from collections import defaultdict, deque

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}
url = "https://www.whosdatedwho.com/dating/"

def parse_args():
    parser = argparse.ArgumentParser(description="Scrape relationship links from Whosdatedwho using snowball sampling")
    parser.add_argument('celebrity', help='Celebrity name to search for. ex: "Orlando Bloom"')
    parser.add_argument('number', help='Total number of celebrities we want to collect')
    parser.add_argument('-o', '--output', help='Output JSON file (optional, defaults to stdout)')
    return parser.parse_args()

def getScrape(link):  
    print(f"Scraping URL: {link}")
    response = requests.get(link, headers=headers)
    html_content = response.content
    soup = BeautifulSoup(html_content, "html.parser")
    return soup

def load_html_cache():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    cache_path = os.path.join(curr_dir, "data", 'orlando_bloom.html')
    with open(cache_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, "html.parser")
    return soup

def extract_relations(link):
    soup = getScrape(link)

    dating_history = soup.find("div", class_="ff-dating-history ff-panel")
    if not dating_history:
        print("Dating history section not found.")
        return [], []
    
    person = dating_history.find_all("div", class_="ff-grid-box")

    if not person:
        print("No dating partners found.")
        return [], []
    
    people = []
    links = []
    for p in person:
        # Get the anchor tag to get name
        # Could also get it from id but in case there are any discrepancies
        anchor = p.find("a")
        if not anchor:
            continue
        
        name_tag = anchor.find("h4") 
        if not name_tag:
            continue
        
        name = name_tag.get_text(strip=True).lower()
        link = anchor.get("href")
        people.append(name)
        links.append(link)

    return people, links

def get_relationships(name, link, number):
    # Use set for unique people and deque for efficient queue operations
    master_dict = defaultdict(set)
    name_queue = deque()
    link_queue = deque()
    names_seen = set()
    total_collected = 0

    # Stop when we have enough people or no more links to follow
    while total_collected < number or not name_queue:
        people, links = extract_relations(link)

        for i in range(len(people)):
            person_name = people[i]
            person_link = links[i]
            if person_name not in names_seen:
                name_queue.append(person_name)
                link_queue.append(person_link)
                total_collected += 1

        people = set(people)
        master_dict[name].update(people)

        name = name_queue.popleft()
        link = link_queue.popleft()
        
        names_seen.add(name)
        


    return master_dict

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)  # Convert sets to lists
        return json.JSONEncoder.default(self, obj)

def write_output(data, output_path=None):
    json_output = json.dumps(data, cls=SetEncoder, indent=4)
    if output_path is None:
        print(json_output)
    else:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_output)
        print(f"Output successfully saved to {output_path}")

def main():
    args = parse_args()
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(curr_dir, args.output) if args.output else None
    
    name_formatted = args.celebrity.replace(" ", "-").lower()
    link = url + name_formatted     

    data = get_relationships(args.celebrity, link, int(args.number))
    write_output(data, output_path)

if __name__ == "__main__":

    main()