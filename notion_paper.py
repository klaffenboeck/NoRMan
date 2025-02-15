import requests
import re
from datetime import datetime, timezone
import pprint
import json

with open('configs/notion_config.json', 'r') as file:
    notion_config = json.load(file)

NOTION_TOKEN = notion_config["NOTION_TOKEN"]
DATABASE_ID = notion_config["DATABASE_ID"]

headers = {
    "Authorization": "Bearer " + NOTION_TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def get_pages():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {"page_size": 5}
    response = requests.post(url, json=payload, headers=headers)

    data = response.json()

    import json
    with open('db.json', 'w', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    results = data["results"]
    return results

#get_pages()

def get_page(title):
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    payload = {
        "filter": {
            "property": "Key",
            "title": {
                "equals": title
            }
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def validate_key_availability(title):
    res = get_page(title)
    #pprint.pprint(res)
    if res["results"]:
        print("IS NOT AVAILABLE")
        return False
    print("IS AVAILABLE")
    return True

def create_page(data: dict):
    prepped_data = prep_data(data)
    pprint.pprint(prepped_data)
    create_url = "https://api.notion.com/v1/pages"
    payload = {"parent": {"database_id": DATABASE_ID}, "properties": prepped_data}
    res = requests.post(create_url, headers=headers, json=payload)
    print(res.status_code)
    return res

# key = "Klaffenboeck2025"
# title = "The ModelPaper to Rule Them All This Year"
# match = re.search(r'\d{4}',key)
# number_string = match.group()
# number = int(number_string)
# year = number
# data = {
#     "Key": {"title": [{"text": {"content": key}}]},
#     "Year": {"number": year},
#     "Title": {"rich_text": [{"text": {"content": title}}]}
# }

def prep_data(data: dict):
    # retdata = {
    #     "Key": {"title": [{"text": {"content": data["key"]}}]},
    #     #"Year": {"number": int(data["year"])},
    #     #"Title": {"rich_text": [{"text": {"content": data["title"]}}]},
    #     #"Abstract": {"rich_text": [{"text": {"content": data["abstract"]}}]},
    #     "Bibtex": {"rich_text": [{"text": {"content": data["bibtex"]}}]},
    #     #"Project_tag": {"multi_select": [{"name": data["project"]}]},
    #     "Papertrail": {"rich_text": [{"text": {"content": data["papertrail"]}}]},
    #     # "Type": {"select": {"name": data["type"]}},
    #     #"Notes": {"rich_text": [{"text": {"content": data["notes"]}}]},
    #     "Link/DOI": {"url": data["link_doi"]}
    # }
    retdata = {}
    if "key" in data and data["key"]:
        retdata["Key"] = {"title": [{"text": {"content": data["key"]}}]}
    if "papertrail" in data and data["papertrail"]:
        retdata["Papertrail"] = {"rich_text": [{"text": {"content": data["papertrail"]}}]}
    if "bibtex" in data and data["bibtex"]:
        retdata["Bibtex"] = {"rich_text": [{"text": {"content": data["bibtex"]}}]}
    if "year" in data and data["year"]:
        retdata["Year"] = {"number": int(data["year"])}
    if "title" in data and data["title"]:
        retdata["Title"] = {"rich_text": [{"text": {"content": data["title"]}}]}
    if "project" in data and data["project"]:
        retdata["Project_tag"] = {"multi_select": [{"name": data["project"]}]}
    if "abstract" in data and data["abstract"]:
        retdata["Abstract"] = {"rich_text": [{"text": {"content": data["abstract"]}}]}
    if data["count"]:
        retdata["Citation count"] = {"number": int(data["count"])}
    if "type" in data and data["type"]:
        retdata["Type"] = {"select": {"name": data["type"]}}
    if "notes" in data and data["notes"]:
        retdata["Notes"] = {"rich_text": [{"text": {"content": data["notes"]}}]}
    if "link_doi" in data and data["link_doi"]:
        retdata["Link/DOI"] = {"url": data["link_doi"]}
    if "journal" in data and data["journal"]:
        retdata["Journal"] = {"rich_text": [{"text": {"content": data["journal"]}}]}
    if "venue" in data and data["venue"]:
        retdata["Venue"] = {"select": {"name": data["venue"]}}
    return retdata

#create_page(data)



def send_data(data={}):
    print(f"Data sent to notion")
