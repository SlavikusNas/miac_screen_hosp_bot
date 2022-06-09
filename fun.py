import pandas as pd
import requests
import configparser


def report_bi(report_name):
    """ ВЫГРУЗКА BI отчета """
    config = configparser.ConfigParser()
    config.read('config.ini')
    config = config['LOGING']

    logs = {
        "asGuest": "false",
        "isLoginBinding": "False",
        "login": config['login'],
        "password": config['password']
    }

    url_log = 'http://bi.mz.mosreg.ru/login/?ReturnUrl'
    url_post = f'http://bi.mz.mosreg.ru/api/{report_name}/PostList?typeId={report_name}&key=create'

    ses = requests.Session()
    ses.post(url_log, logs, timeout=10, stream=True)
    get_report = ses.post(url_post, stream=True, timeout=10)

    report = pd.json_normalize(get_report.json()['data'])
    return report