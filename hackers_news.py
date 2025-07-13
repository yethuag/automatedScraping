from bs4 import BeautifulSoup
import requests
import json
import re
from datetime import datetime,timezone

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Mobile Safari/537.36"
}

def scrape_page(url):
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    
    titles = []
    
    for span in soup.find_all("span", class_="titleline"):
        a_tag = span.find("a")
        if a_tag:
            title = a_tag.text.strip()
            link = a_tag["href"]
            story_element = find_story_element(soup, link)
            story_data = {
                "title": title,
                "url": link,
                "id": id_finder(soup, link),
                "domain": domain_finder(link),
                "hours_ago": parse_time_ago(story_element) * 60,
                "score": score_finder(story_element),
                "comments": comment_counter(story_element),
                "author": author_finder(story_element)
            }
            titles.append(story_data)
    
    return titles, soup

def get_multiple_pages(base_url, num_pages=5):
    all_stories = []
    current_url = base_url
    
    for page in range(num_pages):
        print(f"Scraping page {page + 1}: {current_url}")
        
        stories, soup = scrape_page(current_url)
        all_stories.extend(stories)
        more_link = soup.find("a", class_="morelink")
        if more_link and more_link.get("href"):
            current_url = "https://news.ycombinator.com/" + more_link["href"]
        else:
            print("No more pages found")
            break
    
    return all_stories

def id_finder(soup, url):
    try:
        a_tag = soup.find("a", href=url)
        if not a_tag:
            return None
        tr_e = a_tag.find_parent("tr")
        if tr_e and tr_e.get("id"):
            return tr_e.get("id")
    except Exception as ex:
        print(f"Error on {url}: {ex}")
        pass
    return None

def domain_finder(url):
    if not url:
        return None
    if url.startswith('http://'):
        url = url[7:]
    elif url.startswith('https://'):
        url = url[8:]
    domain = url.split('/')[0]
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def score_finder(story_element):
    score = story_element.find("span", class_="score")
    if score:
        score_text = score.text.strip()
        match = re.search(r'(\d+)', score_text)
        if match:
            return int(match.group(1))
    return 0

def parse_time_ago(story_element):
    age_span = story_element.find("span", class_="age")
    if not age_span:
        return 0
        
    time_title = age_span.get("title")
    if not time_title:
        return 0
    
    match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', time_title)
    if match:
        try:
            timestamp_str = match.group(1)
            post_time = datetime.fromisoformat(timestamp_str).replace(tzinfo=timezone.utc)
            current_time = datetime.now(timezone.utc)
            time_diff = current_time - post_time
            return time_diff.total_seconds() / 3600
        except Exception as e:
            print(f"Error parsing time: {e}")
            return 0
    return 0

def comment_counter(story_element):
    if not story_element:
        return 0
    all_links = story_element.find_all('a')
    for link in all_links:
        href = link.get('href', '')
        if 'item?id=' in href:
            text = link.get_text()
            text = text.replace('\xa0', ' ').replace('&nbsp;', ' ')
            text = ' '.join(text.split())
            
            numbers = re.findall(r'\d+', text)
            if numbers and ('comment' in text.lower() or 'discuss' in text.lower()):
                return int(numbers[0])
    return 0

def author_finder(story_element):
    if not story_element:
        return None
    all_authors = story_element.find_all('a', class_='hnuser')
    for author in all_authors:
        if author:
            return author.text.strip()

def find_story_element(soup, url):
    try:
        a_tag = soup.find("a", href=url)
        if not a_tag:
            return None
        story_tr = a_tag.find_parent("tr")
        if story_tr:
            next_tr = story_tr.find_next_sibling("tr")
            if next_tr and next_tr.find("span", class_="age"):
                return next_tr
        return None
    except Exception as ex:
        print(f"Error finding story element for {url}: {ex}")
        return None

def to_json(data, filename="hn_stories.json"):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(data)} stories to {filename}")


if __name__ == "__main__":
    base_url = "https://news.ycombinator.com/newest"
    all_stories = get_multiple_pages(base_url, num_pages=3)
    to_json(all_stories)
    print(f"Total stories scraped: {len(all_stories)}")
    print("Scraping completed.")
    print("You can now use the scraped data for further analysis or processing.")
    print("Thank you for using this script!")
    print("If you have any questions or need further assistance, feel free to ask.")
    print("Remember to respect the website's terms of service and robots.txt file when scraping.")
    print("Happy scraping!")