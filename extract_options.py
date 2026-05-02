import requests
from bs4 import BeautifulSoup
import json
import time

def extract_options(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    tasks = []
    for li in soup.find_all('input', {'name': 'selected_task'}):
        tasks.append({'value': li['value'], 'label': li.parent.text.strip()})
    
    targets = []
    for li in soup.find_all('input', {'name': 'selected_target'}):
        targets.append({'value': li['value'], 'label': li.parent.text.strip()})
    
    return tasks, targets

# Extract options from previously downloaded files
function_tasks, function_targets = extract_options('function_mode.html')
parameter_tasks, parameter_targets = extract_options('parameter_mode.html')
transform_tasks, transform_targets = extract_options('transform_mode.html')

options = {
    'Function': {'tasks': function_tasks, 'targets': function_targets},
    'Parameter': {'tasks': parameter_tasks, 'targets': parameter_targets},
    'Transform': {'tasks': transform_tasks, 'targets': transform_targets}
}

with open('db_options.json', 'w') as f:
    json.dump(options, f, indent=4)

print("Options extracted and saved to db_options.json")
