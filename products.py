from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urljoin
import time
import csv
from datetime import datetime

# Headless option
options = webdriver.ChromeOptions()
options.add_argument('--headless')

# Initialize Chrome webdriver
driver = webdriver.Chrome(options=options)
driver.maximize_window()

# Define URLs for different shop types
shop_types = [
    'https://wheelhouseph.com/menu/ventura/',
    'https://wheelhouseph.com/menu/port-hueneme/',
    'https://wheelhouseph.com/menu/venice/'
]

# Get current date and time for CSV file name
now = datetime.now()
timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
csv_file = f'{timestamp}.csv'

# Write CSV header once
fieldnames = ['Product Name', 'Brand', 'Price', 'Picture', 'Description', 'THC content', 'CBD content', 'Flower type', 'Category']
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
product_counter = 0
# Iterate over each shop type
for shop_type in shop_types:
    # Open the shop URL
    driver.get(shop_type)

    # Handle any pop-up dialogs
    try:
        first_dialog = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.klaviyo-close-form'))
        )
        first_dialog.click()
    except:
        pass

    try:
        second_dialog = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.PrimaryButton__Container-sc-1jgafuz-0'))
        )
        second_dialog.click()
    except:
        pass

    # Find product categories
    product_categories = driver.find_elements(By.CSS_SELECTOR, '.CategoryButton__OuterContainer-sc-4x8jok-0 a')

    # URLs to skip
    skip_urls = ['https://wheelhouseph.com/menu/ventura/', 'https://wheelhouseph.com/menu/port-hueneme/', 'https://wheelhouseph.com/menu/venice/']

    # Iterate over each product category
    for product_category in product_categories:
        category_url = product_category.get_attribute('href')
        base_url = 'https://wheelhouseph.com'
        complete_category_url = urljoin(base_url, category_url)

        # Skip if URL is in skip list
        if complete_category_url in skip_urls:
            continue

        # Open new tab and navigate to category URL
        driver.execute_script("window.open('about:blank', '_blank');")
        driver.switch_to.window(driver.window_handles[-1])
        driver.get(complete_category_url)

        time.sleep(3)

        # Zoom in for better visibility
        driver.execute_script("document.body.style.zoom = '5%'")

        time.sleep(3)

        # Find products in the category
        products = driver.find_elements(By.CSS_SELECTOR, '.MultiRowProductsList__ListElement-sc-1jbr0mc-2')

        # Open CSV file for appending
        with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            # Iterate over each product
            for product in products:
                element = None
                while not element:
                    try:
                        element = product.find_element(By.CSS_SELECTOR, '.product-card__image-container a')
                    except NoSuchElementException:
                        driver.execute_script("window.scrollTo(0, window.scrollY + window.innerHeight);")
                        time.sleep(2)

                # Extract product details
                href_value = element.get_attribute('href')
                complete_url = urljoin(base_url, href_value)

                driver.execute_script("window.open('about:blank', '_blank');")
                driver.switch_to.window(driver.window_handles[-1])
                driver.get(complete_url)

                image = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.product-info__image-container img'))).get_attribute('src')

                details = driver.find_element(By.CSS_SELECTOR, '.product-info__product-detail-container')

                brand_elements = details.find_elements(By.CSS_SELECTOR, '.product-info__brand-container span')
                brand = brand_elements[0].text if brand_elements else None

                name = details.find_element(By.CSS_SELECTOR, '.product-info__product-name').text

                flower_element = details.find_elements(By.CSS_SELECTOR, '.product-info__main-tags-container .simple-flower-type-indicator__container span')
                flower = flower_element[0].text if flower_element else None

                main_tags_elements = details.find_elements(By.CSS_SELECTOR, '.product-info__main-tags-container .potency-tag__container')
                main_tags = [tag.text for tag in main_tags_elements]
                THC = next((tag.strip() for tag in main_tags if 'THC' in tag), None)
                CBD = next((tag.strip() for tag in main_tags if 'CBD' in tag), None)

                description_element = details.find_elements(By.CSS_SELECTOR, '.read-more__text')
                description = description_element[0].text if description_element else None

                price_price = details.find_element(By.CSS_SELECTOR, '.product-info__price-display-price').text
                price_size_elements = details.find_elements(By.CSS_SELECTOR, '.product-info__price-display-size')
                price_size = price_size_elements[0].text if price_size_elements else None

                categories = [category_element.find_element(By.CSS_SELECTOR, 'a').text.strip() for category_element in details.find_elements(By.CSS_SELECTOR, '.product-info__secondary-tag')]

                # Write product data to CSV
                data = {
                    'Product Name': name,
                    'Brand': brand,
                    'Price': f"{price_price}   {price_size}",
                    'Picture': image,
                    'Description': description,
                    'THC content': THC,
                    'CBD content': CBD,
                    'Flower type': flower,
                    'Category': ', '.join(categories),
                }
                product_counter = product_counter + 1
                print(f"{product_counter}\)  {complete_category_url} | {shop_type}")
                print(data)
                writer.writerow(data)

                # Close current tab and switch back to the main tab
                driver.close()
                driver.switch_to.window(driver.window_handles[-1])

                WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.product-card__image-container a')))

        # Close the current tab and switch back to the main tab
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

# Close the browser
driver.quit()
