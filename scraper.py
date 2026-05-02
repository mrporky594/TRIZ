import requests
from bs4 import BeautifulSoup
import json
import time
import os

BASE_URL = "https://wbam2244.dns-systems.net/EDB/index.php"

def scrape_results(mode, task, target):
    payload = {
        'PageRequest': 'EDBdisplayQueryResults',
        'selected_task': task['value'],
        'selected_target': target['value'],
        'filter': 'both',
        'Preserved_Mode_Name': mode
    }
    
    try:
        response = requests.post(BASE_URL, data=payload, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error scraping {mode} - {task['label']} - {target['label']}: {e}")
        return None

def parse_results(html):
    if not html:
        return [], []
    
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    # Each effect is in a 'results-row' div
    rows = soup.find_all('div', class_='results-row')
    for row in rows:
        title_div = row.find('div', class_='results-title')
        desc_div = row.find('div', class_='results-desc')
        note_div = row.find('div', class_='results-note')
        
        if not title_div:
            continue
            
        a_tag = title_div.find('a')
        if a_tag:
            effect_id = a_tag.get('id', '')
            title = a_tag.text.strip()
            link = a_tag.get('href', '')
        else:
            # Some titles might not have links
            title = title_div.text.strip()
            effect_id = "" # Fallback
            link = ""
            
        desc = desc_div.text.strip() if desc_div else ""
        note = note_div.text.strip() if note_div else ""
        
        results.append({
            'id': effect_id,
            'title': title,
            'description': desc,
            'note': note,
            'link': link
        })
    
    return results

def main():
    with open('db_options.json', 'r') as f:
        options = json.load(f)
    
    all_effects = {} # key: id (or title), value: effect data
    mappings = []
    
    # To avoid re-scraping if we resume
    if os.path.exists('scraped_data_raw.json'):
        with open('scraped_data_raw.json', 'r') as f:
            data = json.load(f)
            all_effects = data.get('effects', {})
            mappings = data.get('mappings', [])
            already_scraped = set([(m['mode'], m['task_label'], m['target_label']) for m in mappings])
    else:
        already_scraped = set()

    for mode, data in options.items():
        print(f"Scraping mode: {mode}")
        for task in data['tasks']:
            for target in data['targets']:
                if (mode, task['label'], target['label']) in already_scraped:
                    continue
                
                print(f"  {task['label']} -> {target['label']}...", end=' ', flush=True)
                html = scrape_results(mode, task, target)
                if html:
                    results = parse_results(html)
                    print(f"found {len(results)} effects.")
                    
                    effect_ids = []
                    for res in results:
                        # Use title as fallback key if ID is missing
                        key = res['id'] if res['id'] else res['title']
                        if key not in all_effects:
                            all_effects[key] = res
                        effect_ids.append(key)
                    
                    mappings.append({
                        'mode': mode,
                        'task_label': task['label'],
                        'target_label': target['label'],
                        'effect_ids': effect_ids
                    })
                    
                    # Periodic save
                    if len(mappings) % 10 == 0:
                        with open('scraped_data_raw.json', 'w') as f:
                            json.dump({'effects': all_effects, 'mappings': mappings}, f, indent=4)
                else:
                    print("failed.")
                
                time.sleep(0.5) # Gentle rate limiting

    with open('scraped_data_raw.json', 'w') as f:
        json.dump({'effects': all_effects, 'mappings': mappings}, f, indent=4)
    print("Scraping complete!")

if __name__ == "__main__":
    main()
