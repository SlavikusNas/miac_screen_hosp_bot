import pandas as pd
import imgkit
import platform
import configparser
from PIL import Image
from pathlib import Path


class Table_to_HTML:
    """ Формирование таблицы HTML по госпитализации и изображения таблице"""

    # Шаблоны таблиц для заполнения
    path_html_stamp = Path.cwd().joinpath('stamp_html')
    stamp_html_big = path_html_stamp.joinpath('stamp_html.html')
    stamp_html_small = path_html_stamp.joinpath('stamp_html_small.html')
    path_html_result = Path.cwd().joinpath('result_html')
    # Названия файлов формируются без типа файла, т.к. будут сохраняться в виде таблицы и виде изображения
    result_html_big = path_html_result.joinpath('stamp_html')
    result_html_small = path_html_result.joinpath('stamp_html_small')

    def __init__(self, week_table: pd.DataFrame, on_hour=None):
        self.period_week_ago = None
        self.period_week_last = None
        self.df = week_table

        # Если создается таблица с указанием времени, то сохраняем файл отдельным именем
        if on_hour:
            self.result_html_big = self.path_html_result.joinpath('stamp_html_time')
            self.result_html_small = self.path_html_result.joinpath('stamp_html_small_time')
        self.main()

    def main(self):
        """ Порядок выполнения методов """
        self.format_table()
        self.put_week_table_to_html()

    def format_table(self):
        """ Переводим таблицу в вид для HTML """
        # Периоды прошлой и предыдущей недели для названия столбцов дат
        self.period_week_ago = f"({self.df['week_ago'].min().strftime('%d.%m')} - " \
                               f"{self.df['week_ago'].max().strftime('%d.%m')})"
        self.period_week_last = f"({self.df['week_last'].min().strftime('%d.%m')} - " \
                                f"{self.df['week_last'].max().strftime('%d.%m')})"

        # Создаем два списка из названия дня недели и времени на которое произведена выгрузка
        # Если подгружено на время 24 часа - то есть за сутки, то полностью убираем время, оставляем только день,
        # удаляя '(24:00)'
        # Если подгружено на определенное время, то оставляем информацию
        for week in ['week_ago', 'week_last']:
            week_ago_week_day = []
            for day, time in zip(self.df[f'{week}_week_day'], self.df[f'{week}_time']):
                if time <= 24:
                    week_ago_week_day += [f'{day} ({int(time)}:00)']
                # else:
                #     week_ago_week_day += [np.NaN]
            column = f'{week}_week_day_time'
            self.df[column] = week_ago_week_day + ['Всего за неделю']
            self.df[column] = self.df[column].apply(lambda x: x.replace(r' (24:00)', '') if type(x) is str else x)

        # Фиксируем порядок столбцов
        cols = ['week_ago_week_day_time', 'covid_y', 'smp_y', 'himself_y', 'getout_y', 'move_y', 'dyn_y', 'dyn_all_y',
                'week_last_week_day_time', 'covid_x', 'smp_x', 'himself_x', 'getout_x', 'move_x', 'dyn_x', 'dyn_all_x']
        self.df = self.df[cols].fillna('')

        # Переводим все численные показатели в целое число, если оно не является строкой
        for col in self.df.columns:
            self.df[col] = self.df[col].apply(lambda x: int(x) if type(x) is not str else x)

    def put_week_table_to_html(self):
        """ Загрузка данных фрейма в html таблицу путем замены значений """
        # Открываем шаблон большой и сокращенной таблицы
        with open(self.stamp_html_big, encoding='utf-8') as file:
            html_big = file.read()
        with open(self.stamp_html_small, encoding='utf-8') as file:
            html_small = file.read()

        # Заменяем названия столбца с датой
        html_big = html_big.replace('>date_x<', f'>{self.period_week_ago}<')
        html_big = html_big.replace('>date_y<', f'>{self.period_week_ago}<')
        html_small = html_small.replace('>date_x<', f'>{self.period_week_last}<')
        html_small = html_small.replace('>date_y<', f'>{self.period_week_last}<')

        # По циклу заменяем значения в столбцах даты
        number = 1
        date_list = self.df['week_ago_week_day_time'].to_list() + self.df['week_last_week_day_time'].to_list()
        for param in date_list:
            html_big = html_big.replace(f'>dt{number}<', f'>{param}<')
            html_small = html_small.replace(f'>dt{number}<', f'>{param}<')
            number += 1

        # По циклу заменяем значения в столбцах с показателями
        cols_param = self.df.columns.to_list()
        cols_param.remove('week_ago_week_day_time')
        cols_param.remove('week_last_week_day_time')
        number = 1
        for col in cols_param:
            for param in self.df[col].to_list():
                html_big = html_big.replace(f'>n{number}<', f'>{param}<')
                html_small = html_small.replace(f'>n{number}<', f'>{param}<')
                number += 1

        # Сохраняем новый html файл
        with open(f'{self.result_html_big}.html', 'w', encoding='utf-8') as file:
            file.write(html_big)
        with open(f'{self.result_html_small}.html', 'w', encoding='utf-8') as file:
            file.write(html_small)

        # Сохраняем изображение html таблицы
        if platform.system() == 'Windows':
            config = imgkit.config(wkhtmltoimage=r"C:\Program Files\wkhtmltopdf\bin/wkhtmltoimage.exe")
        elif platform.system() == 'Linux':
            config = imgkit.config(wkhtmltoimage=r"/usr/local/bin/wkhtmltoimage")
        else:
            config = None

        imgkit.from_file(f'{self.result_html_big}.html', f'{self.result_html_big}.png', config=config)
        imgkit.from_file(f'{self.result_html_small}.html', f'{self.result_html_small}.png', config=config)

        # Обрезаем изображение
        # !!! Параметры стоит редактировать индивидуально, т.к. каждая операционная система и каждый дистрибутив
        # !!! Создает изображение в разных размерах и требуются разные размеры обрезания
        conf = configparser.ConfigParser()
        conf.read('config.ini')
        conf = conf['CUT_IMAGE']
        crop_param_big = (int(conf['x1_small']), int(conf['y1_small']), int(conf['x2_small']), int(conf['y2_small']))
        crop_param_small = (int(conf['x1_small']), int(conf['y1_small']), int(conf['x2_small']), int(conf['y2_small']))

        with Image.open(f'{self.result_html_big}.png') as img:
            img = img.crop(crop_param_big)
            img.save(f'{self.result_html_big}.png')
        with Image.open(f'{self.result_html_small}.png') as img:
            img = img.crop(crop_param_small)
            img.save(f'{self.result_html_small}.png')
        print(1)


if __name__ == '__main__':
    df = pd.read_csv('stamp_for_Table_to_HTML.csv')
    df['week_ago'] = pd.to_datetime(df['week_ago'], format='%Y-%m-%d', errors='coerce')
    df['week_last'] = pd.to_datetime(df['week_last'], format='%Y-%m-%d', errors='coerce')
    main = Table_to_HTML(week_table=df)
