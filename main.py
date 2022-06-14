import report_bi_hosp
import tele_bot
from create_html_table import Table_to_HTML
from datetime import date, timedelta, datetime, time


class HOSP_WEEK_TABLE:

    def __init__(self, date_now: date, time_now: int, send_telegram: bool = False):
        self.date_now = date_now  # Дата - на которую формируется отчет
        self.time_now = time_now  # Время на которое формируется отчет
        self.send_telegram = send_telegram
        self.week_time_table = None  # Таблица по госпитализации с временем
        self.week_table = None  # Таблица по госпитализации без
        self.main()

    def main(self):
        self.get_table()  # Формируем таблицы
        self.format_table_to_html()  # Преобразуем таблицы в HTML, сохраняем изображение таблиц
        if self.send_telegram:
            self.telegram_chat_send()  # Отправляем данные в телеграмм чат

    def get_table(self):
        """ Выгружаем таблицы """
        report = report_bi_hosp.BI_Report_Hospital_on_hour(date_now=self.date_now, time_now=self.time_now)
        self.week_table, self.week_time_table = report.create_table()

    def format_table_to_html(self):
        """ Формируем HTML файлы с таблицей """
        Table_to_HTML(self.week_table.copy())
        Table_to_HTML(self.week_time_table.copy(), on_hour=True)

    def telegram_chat_send(self):
        tb = tele_bot.Telebot_send
        if self.time_now <= 7:
            tb('stamp_html.png')
            tb('stamp_html_small.png')
        else:
            tb('stamp_html_time.png')
            tb('stamp_html_small_time.png')


if __name__ == '__main__':
    tm_now = time(datetime.now().hour, 0).hour
    # Если время 7 или менее часов - отправляется скриншот за предыдущие сутки
    if tm_now <= 7:
        dt_now = date.today() - timedelta(days=1)
    # Если время более 7 часов - отправляется скриншот на текущие сутки
    else:
        dt_now = date.today()
    main = HOSP_WEEK_TABLE(date_now=dt_now, time_now=tm_now, send_telegram=True)
