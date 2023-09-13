import os
import re
import requests
import bs4 as BeautifulSoup
from dotenv import load_dotenv

load_dotenv()
ANYDEAL_API_KEY = os.getenv('ANYDEAL_API_KEY')
anydeal_base_url = 'https://api.isthereanydeal.com/v01/game/prices/'
plains = 'elitedangerous'
shops = 'steam%2Cepic%2Chumblestore'

requests_url = f'https://api.isthereanydeal.com/v01/game/prices/?key={ANYDEAL_API_KEY}&plains=elitedangerous&shops=steam%2Cepic%2Chumblestore'


def anydealAPIget():
    response = requests.get(requests_url)
    if response.status_code == 200:
        return response.json()
    else:
        return False


def check_on_sale(game_data, threshold_price=29.99):
    for item in game_data['list']:
        if item['price_new'] < threshold_price:
            return True
    return False


def getFdevStorePrice():
    url = 'https://www.frontierstore.net/usd/elite-dangerous.html'
    # Send a GET request to the URL
    response = requests.get(url)

    # Create a BeautifulSoup object from the response content
    soup = BeautifulSoup.BeautifulSoup(response.content, 'html.parser')

    # Find the elements with the class "price"
    price_elements = soup.find_all(class_='price')
    if len(price_elements) > 1:
        price = re.sub(r'[^a-zA-Z0-9.]', '', price_elements[1].text)
        return price
    price = re.sub(r'[^a-zA-Z0-9.]', '', price_elements[0].text)
    return price


def getSteamPrice():
    url = f'https://store.steampowered.com/app/359320/'
    response = requests.get(url)
    soup = BeautifulSoup.BeautifulSoup(response.content, 'html.parser')

    price = soup.find(class_="game_purchase_price").text.strip()

    return price


print(getFdevStorePrice())
