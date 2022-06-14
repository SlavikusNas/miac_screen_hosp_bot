import pandas as pd
import requests
import json
import numpy as np
from fun import report_bi
from datetime import date, datetime, timedelta, time


class BI_Report_Hospital_on_hour:
    """ Количество госпитализированных человек сводная таблица """

    REPORT_NAME = r'hosp_covid_dis_covid_hours_for'
    DATE_NOW = date.today()
    TIME_NOW = time(datetime.now().hour, 0).hour

    def __init__(self, date_now: date = None, time_now: time = None):

        self.week_ago_dt_max = None
        self.week_ago_dt_min = None
        self.week_now_dt_max = None
        self.week_now_dt_min = None
        self.week_with_time = None
        self.week = None
        self.report_bi = None

        if time_now:
            self.TIME_NOW = time_now

        if date_now:
            self.DATE_NOW = date_now
        self.period_week()  # Добавляем даты определяющие периоды недели

    def period_week(self):
        """ Определение периода по которому будет формироваться таблица """
        # weekday = self.date_now.weekday()
        weekday = self.DATE_NOW.isoweekday()
        # Периоды последней недели
        self.week_now_dt_min = self.DATE_NOW - timedelta(weekday - 1)
        self.week_now_dt_max = self.week_now_dt_min + timedelta(6)
        # Периоды предыдущей недели
        self.week_ago_dt_min = self.week_now_dt_min - timedelta(7)
        self.week_ago_dt_max = self.week_ago_dt_min + timedelta(6)

    def get_report(self):
        """ Выгрузка отчета """
        try:
            self.report_bi = report_bi(self.REPORT_NAME)
        except Exception as er:
            print(er)
            print('Ошибка выгрузки отчета. Для продолжения будет загружена последня сохраненная версия отчета!')
            self.report_bi = pd.read_csv('report_bi.csv')

        # Форматирование
        self.report_bi['date'] = pd.to_datetime(self.report_bi['date'], format='%Y-%m-%d')
        self.report_bi['time'] = pd.to_datetime(self.report_bi['time_t'], format='%H:%M', errors='coerce').dt.hour
        self.report_bi['time'] = np.where(self.report_bi['time_t'] == 'сутки', 24, self.report_bi['time'])

    def create_stamp_week_table(self):
        """
        Формирование шаблона таблицы с заданными периодами,
        данный метода формирует пустую таблицу с периодами, к которой будут подтягиваться данные по госпитализации

        функция возвращает две таблицы - stamp, stamp_time
        """
        self.period_week()  # Формирование дат периодов
        dates_last_week = pd.date_range(self.week_now_dt_min, self.week_now_dt_max).to_list()
        dates_ago_week = pd.date_range(self.week_ago_dt_min, self.week_ago_dt_max).to_list()

        # Таблица с периодами за отчетные сутки
        stamp = pd.DataFrame()
        stamp['week_ago'], stamp['week_last'] = dates_ago_week, dates_last_week
        # В местах где будет добавляться информация за день указываем 23
        stamp['week_ago_time'], stamp['week_last_time'] = 24, 24
        # Добавляем номер дня неделим
        stamp['week_ago_week_day'] = stamp['week_ago'].dt.weekday
        stamp['week_last_week_day'] = stamp['week_last'].dt.weekday

        # Таблица с периодами на текущую дату с указанием времени
        stamp_time = stamp.copy()
        # Добавляем время на текущий день, предыдущие день и аналогичный день предыдущей недели
        # now_week_day = self.DATE_NOW.weekday()  # Номер текущего дня недели начиная с 0
        week_date_for_time = [
            (self.DATE_NOW.strftime('%Y-%m-%d')),
            (self.DATE_NOW - timedelta(days=1)).strftime('%Y-%m-%d'),
            (self.DATE_NOW - timedelta(days=7)).strftime('%Y-%m-%d')
        ]
        stamp_time['week_last_time'] = \
            np.where(stamp['week_last'].isin(week_date_for_time), self.TIME_NOW, stamp_time['week_last_time'])
        stamp_time['week_ago_time'] = \
            np.where(stamp['week_ago'].isin(week_date_for_time), self.TIME_NOW, stamp_time['week_ago_time'])
        return stamp, stamp_time

    def create_table(self):
        if self.report_bi is None:
            self.get_report()
        # Выгружаем шаблоны таблиц
        cols_data = ['covid', 'smp', 'himself', 'getout', 'move', 'dyn', 'dyn_all']
        stamp, stamp_time = self.create_stamp_week_table()

        # К шаблонам добавляем информацию из отчета
        def upgrade_table(df: pd.DataFrame):
            # К таблице по очереди добавляется текущая неделя, затем предыдущая неделя
            for cols in [['week_last', 'week_last_time'], ['week_ago', 'week_ago_time']]:
                df = df.merge(self.report_bi, left_on=cols, right_on=['date', 'time'], how='left')
            return df

        stamp, stamp_time = upgrade_table(stamp), upgrade_table(stamp_time)

        week_day = {0: "ПН", 1: "ВТ", 2: "СР", 3: "ЧТ", 4: "ПТ", 5: "СБ", 6: "ВС"}
        for col in ['week_ago_week_day', 'week_last_week_day']:
            stamp[col], stamp_time[col] = stamp[col].replace(week_day), stamp_time[col].replace(week_day)

        # Добавляем итоговую сумму
        # Итоговая сумма в таблице с временем должна быть такая же, как и в таблице за отчетные сутки
        stamp.loc['Total'], stamp_time.loc['Total'] = stamp.sum(numeric_only=True), stamp.sum(numeric_only=True)

        # Настраиваем порядок столбцов
        columns = []
        for week in ['week_ago', 'week_last']:
            columns += [week] + [f'{week}_week_day'] + [f'{week}_time']
            for col in cols_data:
                if week == 'week_ago':
                    x_y = '_y'
                else:
                    x_y = '_x'
                columns += [f'{col}{x_y}']
        stamp, stamp_time = stamp[columns], stamp_time[columns]
        return stamp, stamp_time


if __name__ == '__main__':
    report = BI_Report_Hospital_on_hour()
    report.get_report()
    report.create_table()
