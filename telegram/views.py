__author__ = "@KhanHarry"

import time

from datetime import datetime
import re
import telebot
from django.db.models import F
from rest_framework.response import Response
from rest_framework.views import APIView
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import settings
from product.models import Category
from .const import USER_STEP, BUTTONS, CHANNEL_ID
from .models import TgUser, Cart, Order
from .services import enter_first_name, get_products, get_product, enter_qty_for_cart, enter_phone_number, enter_address

bot = telebot.TeleBot(settings.BOT_TOKEN)


# sharsharamagazinbot

# baxtuzbot
# manageuzbot
# testingforprogrambot

class UpdateBot(APIView):
    def post(self, request):
        json_string = request.body.decode('UTF-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return Response({'code': 200})


def send_text_choice(message, text):
    reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

    reply_keyboard.row(KeyboardButton(BUTTONS['CATALOG']))
    reply_keyboard.row(KeyboardButton(BUTTONS['MY_ORDERS']), KeyboardButton(BUTTONS['CART']))
    reply_keyboard.row(KeyboardButton(BUTTONS['NEWS']), KeyboardButton(BUTTONS['CONTACT']))
    reply_keyboard.row(KeyboardButton('🇺🇿 Tilni almashtirish'))

    bot.send_message(chat_id=message.from_user.id, text=text, reply_markup=reply_keyboard)


@bot.message_handler(commands=['start'])
def start_message(message):
    if TgUser.objects.filter(user_id=message.from_user.id).exists():
        TgUser.objects.filter(user_id=message.from_user.id).update(step=0)

        text = 'Assalomu alaykum, {}!' \
               '\nMen BAXT XK ning Toshkentdagi rasmiy botiman.' \
               '\nMen Sizni mahsulotlarimiz bilan tanistirib, buyurtma berishda yordam beraman.' \
               '\nMahsulotlarni 🥄 Katalog bo‘limidan tanlang' \
            .format(message.chat.first_name)
        send_text_choice(message, text)


    else:
        TgUser.objects.create(user_id=message.from_user.id, step=USER_STEP['ENTER_FIRST_NAME'])
        TgUser.objects.filter(user_id=message.from_user.id).update(step=0)

        text = 'Assalomu alaykum, {}!' \
               '\nMen BAXT XK ning Toshkentdagi rasmiy botiman.' \
               '\nMen Sizni mahsulotlarimiz bilan tanistirib, buyurtma berishda yordam beraman.' \
               '\nMahsulotlarni 🥄 Katalog bo‘limidan tanlang' \
            .format(message.chat.first_name)
        send_text_choice(message, text)
        # text = 'Пожалуйста, выберите язык / Iltimos, tilingizni tanlang ⬇️'
        # reply_markup = InlineKeyboardMarkup()
        # reply_markup.add(InlineKeyboardButton("🇺🇿 uz", callback_data='🇺🇿 uz'),
        #                  InlineKeyboardButton("🇷🇺 ru", callback_data='🇷🇺 ru'))
        #
        # bot.send_message(message.from_user.id, text, reply_markup=reply_markup)


# @bot.message_handler(commands=['start'])
# def send_text(message):
#     text = 'Пожалуйста, выберите язык / Iltimos, tilingizni tanlang ⬇️'
#
#     reply_markup = InlineKeyboardMarkup()
#     reply_markup.add(InlineKeyboardButton("🇺🇿 uz", callBACK_MENU_data='🇺🇿 uz'),
#                      InlineKeyboardButton("🇷🇺 ru", callBACK_MENU_data='🇷🇺 ru'))
#
#     bot.send_message(message.from_user.id, text, reply_markup=reply_markup)

@bot.message_handler(regexp=BUTTONS['BACK_MENU'])
def back_menu(message):
    user = TgUser.objects.filter(user_id=message.from_user.id).get()
    user.step = USER_STEP['DEFAULT']
    user.save()
    start_message(message)


@bot.message_handler(regexp=BUTTONS['CONTACT'])
def contact_info(message):
    text = '📞 Telefon: \n+99890-000-00-00\n🌐 Ijtimoiy tarmoqlar:\n'
    send_text_choice(message, text)


@bot.message_handler(regexp=BUTTONS['CLEAR_CART'])
def clear_cart_message(message):
    Cart.objects.filter(user__user_id=message.from_user.id, status=True).delete()
    send_text_choice(message, '✅ Savat tozalandi')


@bot.message_handler(regexp=BUTTONS['CANCEL_BOOK'])
def cancel_book(message):
    Cart.objects.filter(user__user_id=message.from_user.id, status=True).delete()
    start_message(message)


@bot.message_handler(regexp=BUTTONS['CONFIRM'])
def confirm_book(message):
    text = 'Rahmat! Buyurtmangiz ishlov berish uchun jo\'natildi 👍\n\n' \
           'Operator javobini kuting.' \
           '\n\nBuyurtma raqami №'
    # bot.send_message(514411336, message.message_id - 1)  # Harry
    bot.send_message(514411336, message.message_id-1)  # Harry
    send_text_choice(message, text)


@bot.message_handler(regexp=BUTTONS['CREATE_ORDER'])
def order_create_message(message):
    user_cart_qs = Cart.objects.filter(status=True, user__user_id=message.from_user.id).annotate(
        total=F('product__price') * F('qty'))
    if user_cart_qs:
        total_sum = 0
        text = 'Yangi buyurtma: {}\n\n'.format(datetime.now())
        text += 'ISM: {}\n\n'.format(user_cart_qs.first().user.first_name)
        for user_cart in user_cart_qs:
            total_sum += user_cart.total
            text += '{} x{}'.format(user_cart.product.name, user_cart.qty)
        text += '\n\nSumma: {}'.format(total_sum)
        reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        reply_keyboard.add(KeyboardButton('📞 Raqamni ulashish', request_contact=True))
        bot.send_message(message.from_user.id,
                         'O‘z raqamingizni xalqaro formatda yuboring (998xxxxxxxxx) yoki "📞 Raqamni ulashish " tugmasini bosing',
                         reply_markup=reply_keyboard)
        # bot.send_message(CHANNEL_ID, text)
    else:
        text = 'Sizning savatingiz bo\'sh 😔\n' \
               'Bosh savat bilan taom tayyorlab bo\'lmaydi.\n' \
               ':) Katalog bo\'limidagi mahsulotlardan tanlang'

        bot.send_message(message.from_user.id, text)
    user = TgUser.objects.filter(user_id=message.from_user.id).get()
    user.step = USER_STEP['ENTER_PHONE_NUMBER']
    user.save()


@bot.callback_query_handler(func=lambda c: True)
def inli(message):
    data = message.message.json['reply_markup']['inline_keyboard']
    for i in range(1, len(data), 2):
        product_name = re.search(r'✏ (.*)\d', data[i - 1][0]['text']).group(1)[:-2]
        cart_qs = Cart.objects.filter(user__user_id=message.from_user.id, product__name=product_name).last()
        if cart_qs:
            if message.data == product_name + ' product_del':
                cart_qs.delete()
            elif message.data == product_name + ' product_minus':
                cart_qs.qty -= 1
                cart_qs.save()
            elif message.data == product_name + ' product_plus':
                cart_qs.qty += 1
                cart_qs.save()
    bot.delete_message(message.from_user.id, message.message.message_id)
    bot.delete_message(message.from_user.id, message.message.message_id - 1)
    cart_message(message)


@bot.message_handler(regexp=BUTTONS['CATALOG'])
def catalog(message):
    category_qs = Category.objects.all().values_list('name', flat=True)
    reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    text = 'Kategoriyani tanlang 👇🏻\n\n' \
           'Yetkazib berish shartlari:\n' \
           '— Yetkazib berish bepul, ammo faqat Toshkent shahri ichida ishlaydi;\n' \
           '— Minimal buyurtma: 80 000 so‘m;\n' \
           '— Soat 00:00 dan 17:00 gacha rasmiylashtirilgan buyurtmalar keyingi kuni yetkazib beriladi; \n' \
           '— Soat  17:00 dan 00:00 gacha rasmiylashtirilgan buyurtmalar bir kalendar kunidan keyin yetkaziladi*. \n' \
           '*Yakshanba va davlat bayramlari ish kunlari hisoblanmaydi.'

    buttons = [KeyboardButton(text) for text in category_qs]
    reply_markup.add(*buttons)
    reply_markup.add(KeyboardButton(BUTTONS['CREATE_ORDER']))
    reply_markup.add(KeyboardButton(BUTTONS['CART']), KeyboardButton(BUTTONS['BACK_MENU']))
    bot.send_message(message.from_user.id, text, reply_markup=reply_markup)


@bot.message_handler(regexp=BUTTONS['NEWS'])
def news(message):
    bot.send_message(message.from_user.id, 'Hozirda hech qanday aksiya otkazilmayapti.')


@bot.message_handler(regexp=BUTTONS['MY_ORDERS'])
def my_orders(message):
    orders = Order.objects.filter(user_id=message.from_user.id)
    text = ''
    if orders:
        cart_qs = Cart.objects.filter(status=True, user__user_id=message.from_user.id).annotate(
            total=F('product__price') * F('qty'))
        user = TgUser.objects.filter(user_id=message.from_user.id, step=USER_STEP['ENTER_FIRST_NAME']).last()
        for order in orders:
            text = f'Buyurtma №{order.id}\n\n'
            text += 'Ismingiz: ' + message.text + f'\nTelefon raqami {user.number}\n\nSavatda: \n'
            total_sum = 0
            for cart in cart_qs:
                total_sum += cart.total
                text += f'{cart.product.name} (x{cart.qty}) {cart.total} so\'m\n'
            text += f'\nBuyurtmaning yakuniy summasi: {total_sum}so\'m'
            bot.send_message(message.from_user.id, text)
    else:
        text = 'Hozirda hech narsa yoq'
    bot.send_message(message.from_user.id, text)


@bot.message_handler(regexp=BUTTONS['CONTACT'])
def contact_admin(message):
    text = 'NISHON BAXT XK\n' \
           '📞 Telefon:\n' \
           '+99899-999-00-00\n' \
           '🌐 Ijtimoiy tarmoqlar:\n'
    bot.send_message(message.from_user.id, text)


@bot.message_handler(regexp='🇺🇿/🇷🇺 Tilni almashtirish')
def change_language(message):
    text = 'Пожалуйста, выберите язык / Iltimos, tilingizni tanlang ⬇️'
    reply_markup = InlineKeyboardMarkup()
    reply_markup.add(InlineKeyboardButton("🇺🇿 uz", callback_data='🇺🇿 uz'),
                     InlineKeyboardButton("🇷🇺 ru", callback_data='🇷🇺 ru'))

    bot.send_message(message.from_user.id, text, reply_markup=reply_markup)


@bot.message_handler(regexp=BUTTONS['CART'])
def cart_message(message):
    cart_qs = Cart.objects.filter(status=True, user__user_id=message.from_user.id).annotate(
        total=F('product__price') * F('qty'))
    text = 'Sizning savatingiz: \n\n'
    if cart_qs:
        total_sum = 0
        inline_keyboard_markup = InlineKeyboardMarkup(3)

        for cart in cart_qs:
            text += f'{cart.product.name} x ({cart.qty}) = {cart.total} so\'m\n'
            total_sum += cart.total
            inline_keyboard_markup.row(
                InlineKeyboardButton(f'✏ {cart.product.name} ({cart.qty} dona)', callback_data='calll'))
            inline_keyboard_markup.add(
                InlineKeyboardButton('➖', callback_data=cart.product.name + ' product_minus'),
                InlineKeyboardButton('❌', callback_data=cart.product.name + ' product_del'),
                InlineKeyboardButton('➕', callback_data=cart.product.name + ' product_plus'))
        text += '\nJami: {} so\'m'.format(total_sum)

        reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
        reply_keyboard.row(KeyboardButton(BUTTONS['CREATE_ORDER']))
        reply_keyboard.row(KeyboardButton(BUTTONS['BACK_MENU']), KeyboardButton(BUTTONS['CLEAR_CART']))
        bot.send_message(message.from_user.id, 'Keyingi harakatlarni tanlang', reply_markup=reply_keyboard)
        bot.send_message(message.from_user.id, text, reply_markup=inline_keyboard_markup)
    else:
        text = 'Sizning savatingiz bo\'sh 😔\n' \
               'Bosh savat bilan taom tayyorlab bo\'lmaydi.\n' \
               ':) Katalog bo\'limidagi mahsulotlardan tanlang'

        bot.send_message(message.from_user.id, text)
        catalog(message)


@bot.message_handler(content_types=['contact'])
def read_contact(message):
    enter_phone_number(message, bot)


@bot.message_handler(content_types=['location'])
def read_location(message):
    enter_address(message, bot)


@bot.message_handler(content_types=['text'])
def text_message(message):
    switcher = {
        USER_STEP['ENTER_FIRST_NAME']: enter_first_name,
        USER_STEP['DEFAULT']: get_products,
        USER_STEP['GET_PRODUCT']: get_product,
        USER_STEP['ENTER_QTY']: enter_qty_for_cart,
        USER_STEP['ENTER_PHONE_NUMBER']: enter_phone_number,
        USER_STEP['ENTER_ADDRESS']: enter_address,
    }
    print(TgUser.objects.filter(user_id=message.from_user.id).last().step)
    func = switcher.get(TgUser.objects.filter(user_id=message.from_user.id).last().step, lambda: start_message(message))
    func(message, bot)
