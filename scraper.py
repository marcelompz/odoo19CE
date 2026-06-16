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
        
        products = soup.find_all('div', class_='product-item')
        count = 0
        for p in products:
            title_el = p.find('h3', class_='product-item__title')
            name = title_el.text.strip() if title_el else ''
            
            price_el = p.find('div', class_='product-item__price')
            price = price_el.text.strip() if price_el else ''
            # sometimes price is inside a span inside a different class
            if not price:
                price_el = p.find('span', class_='product-row__price-value')
                price = price_el.text.strip() if price_el else ''
                
            img_el = p.find('img', class_='product-item__thumbnail')
            if not img_el:
                img_el = p.find('img', class_='product-row__thumbnail')
            img_url = img_el.get('src') if img_el else ''
            
            if name:
                writer.writerow([name, price, img_url])
                count += 1
                
        print(f"Successfully scraped {count} products and saved to /opt/odoo/odoo8084/electropar_products.csv")
