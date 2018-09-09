from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram.utils.helpers import mention_markdown
from telegram.error import BadRequest, Unauthorized

import json
import logging
import languages
from time import sleep

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
data_file = open('./database.json')
database = json.load(data_file)

updater = Updater(token='TOKEN')
dispatcher = updater.dispatcher


def start(bot, update, args):
    language = save(update)
    if not args:
        bot.send_message(chat_id=update.message.chat_id, text=languages.start["{}".format(language)])
    else:
        real_id = args[0][5:len(args[0])]
        keyboard = [[InlineKeyboardButton(languages.english["{}".format(language)],
                                          callback_data='en{}'.format(real_id)),
                     InlineKeyboardButton(languages.german["{}".format(language)],
                                          callback_data='de{}'.format(real_id))],
                    [InlineKeyboardButton(languages.uzbek["{}".format(language)],
                                          callback_data='uz{}'.format(update.message.chat_id))]
                    ]
        languages_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(text=languages.setting["{}".format(language)], reply_markup=languages_markup)


def helps(bot, update):
    language = save(update)
    if update.effective_chat.type == "private":
        bot.send_message(chat_id=update.message.chat_id, text=languages.helps["{}".format(language)])


def lang(bot, update):
    language = save(update)
    keyboard = [[InlineKeyboardButton(languages.english["{}".format(language)],
                                      callback_data='en{}'.format(update.message.chat_id)),
                 InlineKeyboardButton(languages.german["{}".format(language)],
                                      callback_data='de{}'.format(update.message.chat_id))],
                [InlineKeyboardButton(languages.uzbek["{}".format(language)],
                                      callback_data='uz{}'.format(update.message.chat_id))]
                ]
    starting = [[InlineKeyboardButton("Start",
                                      "https://t.me/DeleteVoiceMessagesBot?start=start{}".format(update.message.chat_id)
                                      )]
                ]
    languages_markup = InlineKeyboardMarkup(keyboard)
    start_markup = InlineKeyboardMarkup(starting)
    found = False
    if update.effective_chat.type != "private":
        admins = bot.getChatAdministrators(update.message.chat_id)
        for ids in admins:
            if ids['user']["id"] == update.message.from_user.id:
                found = True
                try:
                    bot.send_message(chat_id=update.message.from_user.id, text=languages.setting["{}".format(language)],
                                     reply_markup=languages_markup)
                except Unauthorized:
                    update.message.reply_text(text=languages.starts["{}".format(language)], reply_markup=start_markup)
        if not found:
            update.message.reply_text(languages.admin["{}".format(language)])
    else:
        update.message.reply_text(text=languages.setting["{}".format(language)], reply_markup=languages_markup,
                                  parse_mode='MARKDOWN')


def buttons(bot, update):
    language = save(update)
    query = update.callback_query
    real_id = query.data[2:len(query.data)]
    if real_id.startswith("-100"):
        for ids in database["groups"]:
            if ids[0] == int(real_id):
                ids[1] = query.data[0:2]
                with open('./database.json', 'w') as outfile:
                    json.dump(database, outfile, indent=4, sort_keys=True)
                break
    else:
        for ids in database["users"]:
            if ids[0] == int(real_id):
                ids[1] = query.data[0:2]
                with open('./database.json', 'w') as outfile:
                    json.dump(database, outfile, indent=4, sort_keys=True)
                break
    bot.edit_message_text(text=languages.selected["{}".format(language)].format(query.data[0:2]),
                          chat_id=query.message.chat_id,
                          message_id=query.message.message_id, parse_mode='MARKDOWN')


def voice(bot, update):
    x = 5
    language = save(update)
    try:
        update.message.delete()
        user = mention_markdown(update.message.from_user.id, update.message.from_user.first_name)
        message = bot.send_message(chat_id=update.message.chat_id,
                                   text=languages.delete["{}".format(language)].format(user, x), parse_mode='markdown')
        while True:
            x -= 1
            message.edit_text(text=languages.delete["{}".format(language)].format(user, x), parse_mode='markdown')
            if x is 0:
                message.delete()
                stats("groups", update.message.chat_id)
                break
            sleep(1)
    except BadRequest:
        if update.effective_chat.type == "private":
            update.message.reply_text(languages.private["{}".format(language)])
            stats("users", update.message.chat_id)
        else:
            update.message.reply_text(languages.fail["{}".format(language)])


def commands(bot, update):
    language = save(update)
    if update.effective_chat.type == "private":
        update.message.reply_text(languages.commands_p["{}".format(language)])
    else:
        update.message.reply_text(languages.commands_g["{}".format(language)])


def statistic(bot, update):
    language = save(update)
    group = 0
    if update.effective_chat.type == "private":
        for ids in database["users"]:
            if ids[0] == update.message.chat_id:
                update.message.reply_text(languages.private_stats["{}".format(language)].format(ids[2]))
                break
    else:
        user = mention_markdown(update.message.from_user.id, update.message.from_user.first_name)
        for ids in database["groups"]:
            if ids[0] == update.message.chat_id:
                group = ids[2]
                break
        for chats in database["users"]:
            if chats[0] == update.message.from_user.id:
                update.message.reply_text(languages.group_stats["{}".format(language)].format(group, user, chats[2]),
                                          parse_mode="markdown")
                break


def add(bot, update):
    language = save(update)
    for ids in update.message.new_chat_members:
        if ids["id"] == 686965201:
            bot.send_message(chat_id=update.message.chat_id, text=languages.joined["{}".format(language)])
            break


def stats(chat, real_id):
    for ids in database[chat]:
        if ids[0] == real_id:
            ids[2] += 1
            break
    with open('./database.json', 'w') as outfile:
        json.dump(database, outfile, indent=4, sort_keys=True)


def save(update):
    skip = False
    try:
        if update.effective_chat.type == "private":
            chat = "users"
            real_id = update.message.chat_id
        else:
            chat = "groups"
            real_id = update.message.chat_id
    except AttributeError:
        chat = "users"
        real_id = update.callback_query.from_user.id
    for ids in database[chat]:
        if ids[0] == real_id:
            skip = True
            language = ids[1]
            return language
    if not skip:
        database[chat].append([real_id, "en", 0])
        with open('./database.json', 'w') as outfile:
            json.dump(database, outfile, indent=4, sort_keys=True)
            language = "en"
            return language


start_handler = CommandHandler('start', start, pass_args=True)
dispatcher.add_handler(start_handler)
lang_handler = CommandHandler('lang', lang)
dispatcher.add_handler(lang_handler)
helps_handler = CommandHandler('help', helps)
dispatcher.add_handler(helps_handler)
commands_handler = CommandHandler('commands', commands)
dispatcher.add_handler(commands_handler)
statistic_handler = CommandHandler('stats', statistic)
dispatcher.add_handler(statistic_handler)
language_handler = CallbackQueryHandler(buttons)
dispatcher.add_handler(language_handler)
voice_handler = MessageHandler(Filters.voice, voice)
dispatcher.add_handler(voice_handler)
added_handler = MessageHandler(Filters.status_update.new_chat_members, add)
dispatcher.add_handler(added_handler)
updater.start_polling()
