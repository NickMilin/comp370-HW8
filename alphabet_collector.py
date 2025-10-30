from bs4 import BeautifulSoup
import re
import requests
import argparse
import json
import os
from collections import defaultdict, deque
import string

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}
url = "https://www.whosdatedwho.com/dating/"

def parse_args():
    parser = argparse.ArgumentParser(description="Scrape relationship links from WhosDatedWho using alphabetical sampling")
    parser.add_argument('number', help='Number of celebrities to collect per character')
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
    cache_path = os.path.join(curr_dir, "data", 'starting_a.html')
    with open(cache_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    soup = BeautifulSoup(html_content, "html.parser")
    return soup

def get_first_n_celebrities_per_character(character, n):
    link = f"https://www.whosdatedwho.com/lists/celebrities-with-name-starting-with-{character}"
    
    soup = getScrape(link)
    celeb_list = soup.find_all("li", class_="ff-grid-box ff-list")
    if not celeb_list:
        print(f"No celebrities found for character: {character}")
        return []
    
    for i in range(min(n, len(celeb_list))):
        anchor = celeb_list[i].find("a")
        if not anchor:
            continue

        name_tag = anchor.find("div", class_="ff-name")
        if not name_tag:
            continue
        name = name_tag.get_text(strip=True).lower()
        link = anchor.get("href")
        yield name, link


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

def get_relationships(n):
    lowercase_letters = string.ascii_lowercase

    # Use set for unique people and deque for efficient queue operations
    master_dict = defaultdict(set)

    for character in lowercase_letters:
        for name, link in get_first_n_celebrities_per_character(character, n):
            people, links = extract_relations(link)
            master_dict[name].update(set(people))

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

    data = get_relationships(int(args.number))
    write_output(data, output_path)

if __name__ == "__main__":
    main()
