from bs4 import BeautifulSoup
from urllib.request import urlopen
from urllib.parse import quote, urlparse, parse_qs
import requests
import json
import time
import csv
import random

USER_AGENT = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36'}

def format_url(url):
    url = url.replace("https", "http")
    url = url.replace("www.","")
    if url.endswith("/"):
        url = url[:-1]
    return url

search_host = "https://html.duckduckgo.com/html/?q="
query_url = "https://bytes.usc.edu/cs572/f23-se-ar-chhh/hw/HW1/100QueriesSet4.txt"
google_json_url = "https://bytes.usc.edu/cs572/f23-se-ar-chhh/hw/HW1/Google_Result4.json"

response = requests.get(google_json_url)
if response.status_code != 200:
    print("Failed to retrieve data from the JSON endpoint. Status code:", response.status_code)
    exit()
google_json_data = response.json()

soup = BeautifulSoup(requests.get(query_url).text, 'html.parser')
urls = [url.strip() for url in soup.prettify().split('\n') if url.strip()]
data = {}

corr_data = [['Queries', 'Number of Overlapping Results', 'Percent Overlap', 'Spearman Coefficient']]
sum_overlaps, sum_percent_overlap, sum_corr = 0.0, 0.0, 0.0
size = len(urls)
top_result_count = 10
for i, url in enumerate(urls):
    print("Current: " + str(i))
    retry = 0
    while True:
        search_url = '+'.join(url.split())
        query = search_host + search_url
        soup = BeautifulSoup(requests.get(query, headers=USER_AGENT).text, 'html.parser')
        results = soup.find_all('a', class_='result__a', href=True)
        links = []
        for result in results:
            href = result['href']
            parsed_url = urlparse(href)
            query_params = parse_qs(parsed_url.query)
            uddg_value = query_params.get('uddg', None)
            if uddg_value:
                link = uddg_value[0]
                try:
                    links.index(link)
                except ValueError:
                    links.append(link)
                if len(links) == top_result_count:
                    break
        if len(links) == top_result_count:
            break
        print("Attempt for " + str(i) + ": " + str(retry))
        retry += 1
        time.sleep(random.randint(6,20))

    data[url] = links

    links = [format_url(link) for link in links]
    diff_square_sum = 0
    overlaps = 0
    for google_index, google_url in enumerate(google_json_data[url]):
        try:
            google_url = format_url(google_url)
            duck_index = links.index(google_url)
            overlaps += 1
            diff_square_sum += (google_index - duck_index) ** 2
        except ValueError:
            pass
    percent_overlap = round((overlaps / 10.0) * 100.0, 2)
    if overlaps == 0:
        corr = 0.00
    elif overlaps == 1:
        if diff_square_sum == 0:
            corr = 1.00
        else:
            corr = 0.00
    else:
       corr = round(1 - (6.0*diff_square_sum)/(overlaps*(overlaps**2 - 1)),2)
    corr_data.append(["Query " + str(i + 1), overlaps, percent_overlap, corr])
    sum_overlaps += overlaps
    sum_percent_overlap += percent_overlap
    sum_corr += corr
    time.sleep(random.randint(5,10))

corr_data.append(["Averages", round(sum_overlaps / size,2), round(sum_percent_overlap / size,2), round(sum_corr / size,2)])

json_file_path = "links.json"
with open(json_file_path, "w") as file:
    json.dump(data, file, indent=4)

csv_file_path = "results.csv"
with open(csv_file_path, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerows(corr_data)