import os
import urllib.request
import datetime
import json

from bs4 import BeautifulSoup
from selenium import webdriver

server_url = 'http://www.smogon.com/'
date_format = '%Y-%m'
auto_download = True
PHANTOMJS_PATH = './phantomjs/phantomjs'


class PokeCoachError(Exception):
    '''Exception for errors raised by PokeCoach'''
    pass


class SmogonError(PokeCoachError):
    '''Exception caused when data is not found on Smogon'''
    def __init__(self, msg=None):
        if msg is None:
            msg = 'Requested data does not exist in Smogon.'
        super(SmogonError, self).__init__(msg)


class PokemonError(PokeCoachError):
    '''Exception caused when the requested pokemon doesn't exist.'''
    def __init__(self, msg=None):
        if msg is None:
            msg = 'Pokemon not found.'
        super(PokemonError, self).__init__(msg)


def _check_smogon_release(date):
    server_release = server_url + 'stats/' + date + '/'
    try:
        urllib.request.urlopen(server_release)
    except urllib.request.HTTPError as e:
        raise SmogonError from e


def get_smogon_json(date='default', meta='gen7ou', rank=1500):
    json_filename = 'stats/' + date + '/chaos/' + meta + '-' + str(rank) + '.json'
    if date == 'default':
        autodate = datetime.date.today()
        while True:
            date = autodate.strftime(date_format)
            print('Trying date: ' + date)
            json_filename = 'stats/' + date + '/chaos/' + meta + '-' + str(rank) + '.json'
            print('Checking local files... ', end='')
            if not os.path.isfile(json_filename):
                print('Not found.')
                try:
                    if auto_download:
                        print('Checking server... ', end='')
                        _check_smogon_release(date)
                        print('Found!')
                        break
                except SmogonError:
                    print('Not found.')
                finally:
                    new_date = autodate.replace(day=1) - datetime.timedelta(days=1)
                    autodate = new_date
            else:
                print('Found!')
                break

    if not os.path.isfile(json_filename):
        if auto_download:
            print('Downloading: ' + server_url + json_filename)
            os.makedirs(os.path.dirname(json_filename), exist_ok=True)
            try:
                urllib.request.urlretrieve(server_url + json_filename, json_filename)
            except urllib.request.HTTPError as e:
                raise SmogonError from e
    try:
        f = open(json_filename, 'r')
    except FileNotFoundError:
        raise
    data = f.read()
    json_data = json.loads(data)
    return json_data


def get_pokemon_data(pokemon, date='default', meta='gen7ou', rank=1500):
    smogon_json = get_smogon_json(date, meta, rank)
    pokemon_data = {'data': {}}
    try:
        pokemon_data.update({
            'data': smogon_json['data'][pokemon],
            'Count': sum(smogon_json['data'][pokemon]['Abilities'].values())
        })
    except KeyError as e:
        raise PokemonError from e
    pokemon_data['data_percent'] = pokemon_data['data']
    for (category, content) in pokemon_data['data'].items():
        if isinstance(content, dict):
            for (item, usage) in content.items():
                if isinstance(usage, float):
                    percent_usage = usage / pokemon_data['Count']
                    pokemon_data['data_percent'][category].update({
                        item: percent_usage
                    })
    return pokemon_data


def get_smogon_dex_json(section):
    browser = webdriver.PhantomJS(PHANTOMJS_PATH)
    browser.get(server_url + 'dex/sm/' + section + '/')
    browser.set_window_size(1280, 720)
    return browser
