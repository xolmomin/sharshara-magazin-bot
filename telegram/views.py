import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from django.shortcuts import render
from django.conf import settings
from django.http.response import HttpResponse
from .models import TgUser, Cart
from .const import USER_STEP, BUTTONS, CHANNEL_ID
from django.db.models import F
from .services import enter_first_name, get_products, get_product, enter_qty_for_cart
from product.models import Category
from datetime import datetime
bot = telebot.TeleBot(settings.BOT_TOKEN)


def web_hook_view(request):
    if request.method == 'POST':
        bot.process_new_updates([telebot.types.Update.de_json(request.body.decode("utf-8"))])
        return HttpResponse(status=200)
    return HttpResponse('404 not found')


@bot.message_handler(commands=['start'])
def start_message(message):
    if TgUser.objects.filter(user_id=message.from_user.id).exists():
        TgUser.objects.filter(user_id=message.from_user.id).update(step=0)

        text = 'Nima buyurtma beramiz ?'
        category_qs = Category.objects.all().values_list('name', flat=True)
        reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

        buttons = [KeyboardButton(text=text) for text in category_qs]
        buttons.append(KeyboardButton(text=BUTTONS['CART']))
        reply_markup.add(*buttons)

        bot.send_message(message.from_user.id, text, reply_markup=reply_markup)
    else:
        TgUser.objects.create(user_id=message.from_user.id, step=USER_STEP['ENTER_FIRST_NAME'])

        text = 'Salom Mini burget bot ga xush kelibsiz!!!\n\n'
        text += 'Ismingizni kiriting:'
        bot.send_message(message.from_user.id, text)


@bot.message_handler(regexp=BUTTONS['BACK'])
def back_message(message):
    start_message(message)


@bot.message_handler(regexp=BUTTONS['CLEAR_CART'])
def clear_cart_message(message):
    Cart.objects.filter(user__user_id=message.from_user.id, status=True).delete()
    bot.send_message(message.from_user.id, '✅ Savat tozalandi')
    start_message(message)


@bot.message_handler(regexp=BUTTONS['CREATE_ORDER'])
def order_create_message(message):
    user_cart_qs = Cart.objects.filter(status=True, user__user_id=message.from_user.id).annotate(total=F('product__price') * F('qty'))
    if user_cart_qs:
        total_sum = 0
        text = 'Yangi buyurtma: {}\n\n'.format(datetime.now())
        text += 'ISM: {}\n\n'.format(user_cart_qs.first().user.first_name)
        for user_cart in user_cart_qs:
            total_sum += user_cart.total
            text += '{} x{}'.format(user_cart.product.name, user_cart.qty)
        text += '\n\nSumma: {}'.format(total_sum)
        bot.send_message(message.from_user.id, 'Buyurtmangiz qabul qilindi')
        bot.send_message(CHANNEL_ID, text)
        user_cart_qs.delete()
    else:
        bot.send_message(message.from_user.id, 'Savatingiz bo\'sh')


@bot.message_handler(regexp=BUTTONS['CART'])
def cart_message(message):
    cart_qs = Cart.objects.filter(status=True, user__user_id=message.from_user.id).annotate(total=F('product__price') * F('qty'))
    text = 'Savat: \n\n'
    if cart_qs:
        total_sum = 0
        for cart in cart_qs:
            total_sum += cart.total
            text += f'{cart.product.name} (x{cart.qty}) {cart.total}so\'m\n'
        text += '\nJami: {}so\'m'.format(total_sum)
    else:
        text += 'bo\'sh (Пусто)'

    reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    buttons = [
        KeyboardButton(text=BUTTONS['CREATE_ORDER']),
        KeyboardButton(text=BUTTONS['CLEAR_CART']),
        KeyboardButton(text=BUTTONS['BACK']),
    ]
    reply_keyboard.add(*buttons)
    bot.send_message(message.from_user.id, text, reply_markup=reply_keyboard)


@bot.message_handler(content_types=['text'])
def text_message(message):
    switcher = {
        USER_STEP['ENTER_FIRST_NAME']: enter_first_name,
        USER_STEP['DEFAULT']: get_products,
        USER_STEP['GET_PRODUCT']: get_product,
        USER_STEP['ENTER_QTY']: enter_qty_for_cart,
    }
    print(TgUser.objects.get(user_id=message.from_user.id).step)
    func = switcher.get(TgUser.objects.get(user_id=message.from_user.id).step, lambda: start_message(message))
    func(message, bot)
