from django.db.models import F

from .models import TgUser, Cart
from .const import USER_STEP, BUTTONS
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from product.models import Product, Category


def enter_first_name(message, bot):
    user = TgUser.objects.filter(user_id=message.from_user.id, step=USER_STEP['ENTER_FIRST_NAME']).last()
    user.first_name = message.text
    user.step = USER_STEP['CONFIRM']
    user.save()
    if "/+/" in user.address:
        address = "Location"
    else:
        address = user.address
    text = 'Ism: ' + user.first_name + f'\nManzil: {address}\nTelefon raqami: {user.number}\n\nSavatda: \n'
    cart_qs = Cart.objects.filter(status=True, user__user_id=message.from_user.id).annotate(
        total=F('product__price') * F('qty'))
    total_sum = 0
    for cart in cart_qs:
        total_sum += cart.total
        text += f'{cart.product.name} (x{cart.qty}) {cart.total} so\'m\n'
    text += f'\nBuyurtmaning yakuniy summasi: {total_sum}so\'m'
    text += '\nToshkent shahar ichida yetkazib berish bepul'
    reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    reply_markup.row(KeyboardButton(BUTTONS['CONFIRM']))
    reply_markup.row(KeyboardButton(BUTTONS['CANCEL_BOOK']), KeyboardButton(BUTTONS['BACK_MENU']))
    bot.send_message(message.from_user.id, text, reply_markup=reply_markup)


def get_products(message, bot):
    try:
        category = Category.objects.get(name=message.text)
        products = Product.objects.filter(category=category).values_list('name', flat=True)
        if products:
            reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

            buttons = [KeyboardButton(text) for text in products]
            reply_keyboard.add(*buttons)
            reply_keyboard.row(KeyboardButton(BUTTONS['CREATE_ORDER']))
            reply_keyboard.row(KeyboardButton(text=BUTTONS['BACK_MENU']))
            TgUser.objects.filter(user_id=message.from_user.id).update(step=USER_STEP['GET_PRODUCT'])
            bot.send_message(message.from_user.id, category.name, reply_markup=reply_keyboard)
        else:
            text = 'Kechirasiz ushbu menyuda maxsulotlar yo\'q'
            bot.send_message(message.from_user.id, text)

    except Category.DoesNotExist:
        pass


def get_product(message, bot):  # 2
    try:
        product = Product.objects.get(name=message.text)
        user = TgUser.objects.get(user_id=message.from_user.id)
        user.step = USER_STEP['ENTER_QTY']
        cart, created = Cart.objects.get_or_create(product=product, user=user)
        if not created:
            cart.qty = 0
            cart.status = False
            cart.save()
        user.save()

        text = f'{product.name}\n\n'
        text += f'{product.description}\n\n'
        text += f'Narxi: {product.price}'

        reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        buttons = [KeyboardButton(str(i)) for i in range(1, 10)]
        navigators = [
            KeyboardButton(text=BUTTONS['CART']),
            KeyboardButton(text=BUTTONS['BACK_MENU'])
        ]
        reply_keyboard.add(*buttons, *navigators)
        bot.send_photo(chat_id=message.from_user.id, photo=product.photo, caption=text, reply_markup=reply_keyboard)
    except Exception as e:
        print(e)


def enter_qty_for_cart(message, bot):  # 3
    user = TgUser.objects.filter(user_id=message.from_user.id).get()
    user.step = USER_STEP['DEFAULT']

    last_cart = Cart.objects.filter(user__user_id=message.from_user.id, status=False, qty=0).last()
    last_cart.qty = int(message.text)
    last_cart.status = True
    text = 'Savatga {} (x{}) qo\'shildi'.format(last_cart.product.name, last_cart.qty)
    last_cart.save()
    user.save()
    bot.send_message(message.from_user.id, text)

    text_1 = 'Yana nima qo\'shamiz??'
    category_qs = Category.objects.all().values_list('name', flat=True)
    reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    buttons = [KeyboardButton(text=text) for text in category_qs]
    buttons.append(KeyboardButton(text=BUTTONS['CART']))
    reply_markup.add(*buttons)
    reply_markup.add(KeyboardButton(text=BUTTONS['BACK_MENU']))
    bot.send_message(message.from_user.id, text_1, reply_markup=reply_markup)


def enter_phone_number(message, bot):
    if message.contact:
        phone_num = message.contact.phone_number
    else:
        phone_num = message.text
    if phone_num.isdigit() and len(phone_num) == 12:
        TgUser.objects.filter(user_id=message.from_user.id).update(number=int(phone_num))
        text = 'Joylashgan joyingizni yuboring yoki ' \
               'aniq manzilingizni ko‘rsating (tuman, ko‘cha, uy, xonadon)' \
               ' va botga yuboring'
        reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        reply_keyboard.add(KeyboardButton(
            'Joriy manzil',
            request_location=True))
        reply_keyboard.add(KeyboardButton(BUTTONS['BACK_MENU']))
        bot.send_message(message.from_user.id, text, reply_markup=reply_keyboard)

        user = TgUser.objects.filter(user_id=message.from_user.id).get()
        user.step = USER_STEP['ENTER_ADDRESS']
        user.save()
    else:
        bot.send_message(message.from_user.id, 'Nomeringizni to\'g\'ri kiriting')


def enter_address(message, bot):
    user_id = message.from_user.id
    user = TgUser.objects.filter(user_id=user_id).get()
    user.step = USER_STEP['ENTER_FIRST_NAME']
    if message.location:
        user.address = str(message.location.longitude) + "/+/" + str(message.location.latitude)
    else:
        user.address = message.text
    user.save()
    text = 'O\'z ismingizni botga yuboring'

    reply_markup = ReplyKeyboardMarkup(resize_keyboard=True)

    if user.first_name:
        reply_markup.add(KeyboardButton(user.first_name))

    bot.send_message(user_id, text, reply_markup=reply_markup)
