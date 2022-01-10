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

bot = telebot.TeleBot(config.TOKEN)
url = config.google_url
geolocator = Nominatim(user_agent="superWheatherBot")
BotDB = BotDB('static/accountant.db')
translator = Translator(to_lang='en', from_lang='ru')


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
    s = requests.Session()
    print(url, plus, url + plus)
    req = s.get(url + plus)
    soup = BeautifulSoup(req.text, 'html.parser')
    return soup


def get_wheather(city):
    global url
    plus = translator.translate(city)
    output = get_html(url, plus)
    print(output.prettify())
    temp = get_temp(output)
    message = 'Населенный пункт: ' + city + ' \n'
    message += 'Температура: ' + temp + '\n'''
    return message


def get_temp(html_text):
    temp_block = html_text.find('span', {'class': 'txt-xxlarge'})
    print(str(temp_block))
    ans = ''
    temp_part = ''
    sign_part = ''
    i = 0
    for temps in temp_block:
        if i == 0:
            temp_part = temps.text
        else:
            sign_part = temps.text
        i += 1
    temperature = int(temp_part)
    if 'F' in sign_part:
        temperature = int((temperature - 32) * (5 / 9))
        sign_part = '°С'
    return str(temperature) + ' ' + sign_part


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
        return
    except Exception as e:
        print(e)
        bot.send_message(message.chat.id, "К сожалению, в вашем городе погоду узнать не удалось")
        return


bot.polling(none_stop=True)
