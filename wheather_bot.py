import urllib

import requests
import telebot
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from telebot import types
from translate import Translator

import config
from db import BotDB

bot = telebot.TeleBot(config.TOKEN)
url = config.url
geolocator = Nominatim(user_agent="superWheatherBot")
BotDB = BotDB('static/accountant.db')
translator = Translator(to_lang='en', from_lang='ru')
s = requests.Session()


@bot.message_handler(commands=['start'])
def welcome(message):
    stick = open('static/AnimatedSticker.tgs', 'rb')
    bot.send_sticker(message.chat.id, stick)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton('Хочу узнать погоду')
    item2 = types.KeyboardButton('Как дела?')
    markup.add(item1, item2)
    if not BotDB.user_exists(message.chat.id):
        BotDB.add_user(message.from_user.id)
        bot.send_message(message.chat.id,
                         "Привет, {0.first_name}! Я бот-помощник, который знает погоду во всей России. Конечно, работаю не без помощи Интернета, но это уже мелочи".format(
                             message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
    else:
        bot.send_message(message.chat.id,
                         "Ого-го! Привет, {0.first_name}! Да я тебя знаю! Рад видеть тебя снова, дружище! Хочешь снова узнать погоду?".format(
                             message.from_user, bot.get_me()), parse_mode='html', reply_markup=markup)
        city_data = BotDB.get_city(message.chat.id)
        if city_data != []:
            city = str(city_data[0][0])
            bot.send_message(message.chat.id,
                             "Я даже помню, где ты в последний раз хотел узнать погоду. Это был " + city + " Сейчас гляну, какая там погода")
            search_weather(message, city)
        else:
            bot.send_message(message.chat.id,
                             "К сожалению, не помню, откуда ты, извини =)")


@bot.message_handler(content_types=['text'])
def message_handler(message):
    if message.chat.type == 'private':
        if message.text == 'Хочу узнать погоду':
            city_data = BotDB.get_city(message.chat.id)
            if city_data != []:
                city = str(city_data[0][0])
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton('Да, мне нужен другой город.')
                item2 = types.KeyboardButton('Нет, спасибо.')
                markup.add(item1, item2)
                bot.send_message(message.chat.id,
                                 "Без проблем. Вернул всё назад", reply_markup=markup)
                bot.send_message(message.chat.id,
                                 "Так-так, в последний раз ты узнавал погоду в " + city + ". Сейчас гляну, какая там погода. Хочешь узнать погоду где-то в другом месте?")
                search_weather(message, city)
            else:
                bot.send_message(message.chat.id,
                                 "К сожалению, не помню название твоего населенного пункте, извини =)")
                bot.send_message(message.chat.id,
                                 "Где именно ты хочешь узнать погоду? Ты можешь отправить нам свое местоположение или просто написать название города")
                keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                button_geo = types.KeyboardButton(text="Отправить местоположение", request_location=True)
                back_button = types.KeyboardButton(text='Вернутся назад')
                keyboard.add(button_geo, back_button)
                bot.send_message(message.chat.id, "Поделись местоположением", reply_markup=keyboard)
        elif message.text == 'Как дела?':
            markup = types.InlineKeyboardMarkup(row_width=2)
            item1 = types.InlineKeyboardButton('Хорошо', callback_data='good')
            item2 = types.InlineKeyboardButton('Ну такое', callback_data='bad')

            markup.add(item1, item2)
            bot.send_message(message.chat.id, 'Все супер! А у тебя?', reply_markup=markup)
        elif message.text == 'Вернутся назад' or message.text == 'Нет, спасибо.':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton('Хочу узнать погоду')
            item2 = types.KeyboardButton('Как дела?')
            markup.add(item1, item2)
            bot.send_message(message.chat.id,
                             "Вернулся в главное меню", reply_markup=markup)
        elif message.text == 'Да, мне нужен другой город.':
            bot.send_message(message.chat.id,
                             "Не терпится начать искать погоду в новом месте. Где на этот раз? Ты можешь отправить нам свое местоположение или просто написать название города")
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button_geo = types.KeyboardButton(text="Отправить местоположение", request_location=True)
            back_button = types.KeyboardButton(text='Вернутся назад')
            keyboard.add(button_geo, back_button)
            bot.send_message(message.chat.id, "Поделись местоположением", reply_markup=keyboard)
        else:
            search_weather(message, '')


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    try:
        if call.data == 'good':
            bot.send_message(call.message.chat.id, 'Вот и отличненько')
        elif call.data == 'bad':
            bot.send_message(call.message.chat.id, 'Бывает...')

        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text='📨',
                              reply_markup=None)

        # bot.answer_callback_query(callback_query_id=call.id, show_alert=False, text='Это текстовое уведомление')
    except Exception as e:
        print(repr(e))


@bot.message_handler(content_types=['location'])
def location(message):
    if message.location is not None:
        st = str(message.location)
        st = st[st.find(':') + 2:]
        long = st[:st.find(',')]
        st = st[st.find(':') + 2:]
        lat = st[:st.find(',')]
        address = float(lat), float(long)
        location = geolocator.reverse(address)
        address = location.raw['address']
        city = address.get('city', '')
        print(city)
        search_weather(message, city)


def get_html(url, plus):
    global s
    headers = {
        'x-user-agent': "desktop",
        'x-proxy-location': "US",
        'x-rapidapi-host': "google-search3.p.rapidapi.com",
        'x-rapidapi-key': "5611131226msh9e78db53f476b4ep15a23bjsn7498bda906eb"
    }
    addlink = cyr_to_google('погода') + '+' + cyr_to_google('в') + '+' + cyr_to_google(
        plus)
    print(url + addlink)
    req = s.get(url + addlink, headers=headers)

    soup = BeautifulSoup(req.text, 'html.parser')
    return soup


def get_wheather(city):
    global url
    output = get_html(url, city)
    temp = get_temp(output)
    message = '🌆 Населенный пункт: ' + city + ' \n'
    message += '⛅ В целом: ' + temp[2] + '\n'
    message += '🌡 Температура: ' + temp[0] + '\n'
    message += '✅ Ощущается как: ' + temp[1] + '\n'
    message += '🌪️ Ветер: ' + temp[2] + '\n'
    return message


def get_temp(html_text):
    info = str(html_text)
    print('find:')
    if info.find("https://www.gismeteo.ru/weather-") != -1:
        info = info[info.find("https://www.gismeteo.ru/weather-"):]
        gismeteo_url = info[:info.find('"')]
    else:
        info = info[info.find("https://www.gismeteo.com/weather-"):]
        gismeteo_url = info[:info.find('"')]
        gismeteo_url = gismeteo_url.replace('.com', '.ru', 1)
    print(gismeteo_url)
    answer = get_gismeteo(gismeteo_url)
    return answer


def search_weather(message, alt):
    try:
        if alt == '':
            alt = message.text
        if BotDB.get_city(message.chat.id) == []:
            BotDB.add_city(message.chat.id, alt)
        else:
            BotDB.set_city(message.chat.id, alt)
        m_to_send = get_wheather(alt)
        bot.send_message(message.chat.id, m_to_send)
        photo_urls = get_photo_url(alt)
        f = open('out.jpg', 'wb')
        try:
            img_data = requests.get(photo_urls[0]).content
            with open('out.jpg', 'wb') as handler:
                handler.write(img_data)
            bot.send_photo(message.chat.id, img_data)
        except Exception as e:
            print(e)
            f.write(urllib.request.urlopen(photo_urls[1]).read())
            f.close()
            img = open('out.jpg', 'rb')
            bot.send_photo(message.chat.id, img)
            img.close()
        return
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "К сожалению, в вашем городе погоду узнать не удалось")
        return


def cyr_to_google(text):
    ans = str(text.encode('utf-8'))[2:-1]
    ans1 = ''
    i = 0
    while i < len(ans):
        if ord(ans[i]) == 92:
            ans1 += '%'
            i += 1
        elif ans[i] == '-' or ans[i] == ',' or ans[i] == ' ':
            ans1 += '+'
        else:
            ans1 += ans[i]
        i += 1
    return ans1.upper()


def get_gismeteo(url):
    global s
    if '/weekly' in url:
        url = url[:url.find('/weekly')]
        url += '/'
    if '/10-days' in url:
        url = url[:url.find('/10-days')]
        url += '/'
    url += 'now'
    print(url)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0'}
    req = s.get(url, headers=headers)
    soup = BeautifulSoup(req.text, 'html.parser')
    return get_now_info(soup)


def get_now_info(soup):
    spans = soup.find('div', {'class': 'weather-value'})
    span1 = spans.find('span')
    w_feel = soup.find('div', {'class': 'weather-feel'})
    feel_c = w_feel.find('span', {'class': 'unit_temperature_c'})
    sky = soup.find('div', {'class': 'now-desc'})
    wind = soup.find('div', {'class': 'now-info-item wind'})
    ans = [span1.text + '°C', feel_c.text + '°C', sky.text, wind.text]
    return ans


def get_photo_url(city):
    url_new = 'https://yandex.ru/images/search?text=' + cyr_to_google(city) + '&family=yes'
    print(url_new)
    response = requests.get(url_new)
    soup = BeautifulSoup(response.text, 'html.parser')
    text_second = str(soup.find('div', {'class': 'serp-item_pos_1'}))
    text_first = str(soup.find('div', {'class': 'serp-item_pos_0'}))
    text_first = text_first[:text_first.find('.jpg') + 5]
    text_second = text_second[text_second.find('url') + 3:]
    text_first = text_first[text_first.rfind('url') + 6:]
    text_second = text_second[text_second.find('url') + 6:]
    text_first = text_first[:text_first.find('"')]
    text_second = text_second[:text_second.find('"')]
    print(text_first, text_second)
    return [text_first, text_second]


bot.polling(none_stop=True)
