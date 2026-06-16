import urllib.request
from bs4 import BeautifulSoup
import csv

url = "https://www.electropar.com.py/categorias/ferreteria-en-general-4?srsltid=AfmBOooeNMtbnehkk0tv1GIWbFZKRDKsIsJmz45cttqO3gVEyAwA3YyH"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

with urllib.request.urlopen(req) as response:
    html = response.read().decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    
    with open('/opt/odoo/odoo8084/electropar_products.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Name', 'Price', 'Image_URL'])
        
        main = soup.find('main', class_='main')
        if main:
            print("Main element text length:", len(main.text))
            for tag in main.find_all(True):
                print(tag.name, tag.get('class'))
        else:
            print("No main element found.")
