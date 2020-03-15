from .models import TgUser, Cart
from .const import USER_STEP, BUTTONS
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from product.models import Product, Category


def enter_first_name(message, bot):
    TgUser.objects.filter(user_id=message.from_user.id).update(first_name=message.text, step=USER_STEP['DEFAULT'])
    text = 'Nima buyurtma beramiz ?'
    category_qs = Category.objects.all().values_list('name', flat=True)
    reply_markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    buttons = [KeyboardButton(text=text) for text in category_qs]
    buttons.append(KeyboardButton(text=BUTTONS['CART']))
    reply_markup.add(*buttons)

    bot.send_message(message.from_user.id, text, reply_markup=reply_markup)


def get_products(message, bot):
    try:
        category = Category.objects.get(name=message.text)
        products = Product.objects.filter(category=category).values_list('name', flat=True)
        if products:
            reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

            buttons = [KeyboardButton(text=category.name[:1] + text) for text in products]
            buttons.append(KeyboardButton(text=BUTTONS['BACK']))
            reply_keyboard.add(*buttons)
            TgUser.objects.filter(user_id=message.from_user.id).update(step=USER_STEP['GET_PRODUCT'])
            bot.send_message(message.from_user.id, category.name, reply_markup=reply_keyboard)
        else:
            text = 'Kechirasiz ushbu menyuda maxsulotlar yo\'q'
            bot.send_message(message.from_user.id, text)

    except Category.DoesNotExist:
        pass


def get_product(message, bot):
    try:
        product = Product.objects.get(name=message.text[1:])
        user = TgUser.objects.get(user_id=message.from_user.id)
        user.step = USER_STEP['ENTER_QTY']
        Cart.objects.create(product=product, user=user, status=False)
        user.save()

        text = f'{product.name}\n\n'
        text += f'{product.caption}\n\n'
        text += f'Narxi: {product.price}'

        reply_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
        buttons = [KeyboardButton(text=i) for i in range(1, 10)]
        navigators = [
            KeyboardButton(text=BUTTONS['CART']),
            KeyboardButton(text=BUTTONS['BACK'])
        ]
        reply_keyboard.add(*buttons, *navigators)
        bot.send_photo(chat_id=message.from_user.id, photo=product.photo, caption=text, reply_markup=reply_keyboard)
    except Exception as e:
        print(e)


def enter_qty_for_cart(message, bot):
    user = TgUser.objects.get(user_id=message.from_user.id)
    user.step = USER_STEP['DEFAULT']

    last_cart = Cart.objects.filter(user__user_id=message.from_user.id, status=False, qty=0).last()
    last_cart.qty = str(message.text)
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

    bot.send_message(message.from_user.id, text_1, reply_markup=reply_markup)
