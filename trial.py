import telebot
import config
import requests
import config
from bs4 import BeautifulSoup
from transliterate import translit
from geopy.geocoders import Nominatim
from telebot import types
from db import BotDB
from translate import Translator


def cyr_to_google(text):
    ans = str(text.encode('utf-8'))[2:-1]
    ans1 = ''
    i = 0
    while i < len(ans):
        if ord(ans[i]) == 92:
            ans1 += '%'
            i += 1
        else:
            ans1 += ans[i]
        i += 1
    return ans1.upper()


bot = telebot.TeleBot(config.TOKEN)
url = config.url
geolocator = Nominatim(user_agent="superWheatherBot")
BotDB = BotDB('static/accountant.db')
translator = Translator(to_lang='en', from_lang='ru')

s = requests.Session()
headers = {
    'x-user-agent': "desktop",
    'x-proxy-location': "US",
    'x-rapidapi-host': "google-search3.p.rapidapi.com",
    'x-rapidapi-key': "5611131226msh9e78db53f476b4ep15a23bjsn7498bda906eb"
}

response = requests.request("GET", url + cyr_to_google('погода') + '+'+ cyr_to_google('в')+'+' + cyr_to_google('иннополис'), headers=headers)
print(response.text)
print(cyr_to_google('погода'))
