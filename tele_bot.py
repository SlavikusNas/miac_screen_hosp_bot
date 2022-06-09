import telebot
import configparser
from pathlib import Path


class Telebot_send:

    config = configparser.ConfigParser()
    config.read('config.ini')
    config = config['TELEBOT']
    bot = telebot.TeleBot(config['token'])
    chat = int(config['chat'])

    def __init__(self, file_name: str):
        self.path_file = Path().cwd().joinpath('result_html').joinpath(file_name)
        self.send_message()

    def send_message(self):
        with open(self.path_file, 'rb') as file:
            self.bot.send_photo(chat_id=self.chat, photo=file)


if __name__ == '__main__':
    main = Telebot_send(file_name='stamp_time_html_small.html222.png')
