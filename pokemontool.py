import os
import urllib.request
import datetime
import json
import re
from bs4 import BeautifulSoup
from selenium import webdriver

SERVER_URL = 'http://www.smogon.com'
DATE_FORMAT = '%Y-%m'
AUTO_DOWNLOAD = True
PHANTOMJS_PATH = './phantomjs/phantomjs'
DEX_SECTION_ROWS = {
    'moves': 'MoveRow',
    'abilities': 'AbilityRow'
}


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
    def __init__(self, name=None, msg=None):
        if msg is None:
            if name is None:
                msg = 'Pokemon not found.'
            else:
                msg = 'Pokemon "' + name + '" not found.'
        super(PokemonError, self).__init__(msg)


class MoveError(PokeCoachError):
    '''Exception caused when the requested move doesn't exist.'''
    def __init__(self, name=None, msg=None):
        if msg is None:
            if name is None:
                msg = 'Move not found.'
            else:
                msg = 'Move "' + name + '" not found.'
        super(MoveError, self).__init__(msg)


def _check_smogon_release(date):
    server_release = SERVER_URL + '/stats/' + date + '/'
    try:
        urllib.request.urlopen(server_release)
    except urllib.request.HTTPError as e:
        raise SmogonError from e


def _name_to_key(name):
    name_key = re.sub('[^0-9a-z]+', '', name.lower())
    return name_key


def pokemon_usage_dict(date='default', meta='gen7ou', rank=1500):
    json_filename = 'stats/' + date + '/chaos/' + meta + '-' + str(rank) + '.json'
    server_source_path = SERVER_URL + '/' + json_filename
    if date == 'default':
        autodate = datetime.date.today()
        while True:
            date = autodate.strftime(DATE_FORMAT)
            print('Trying date: ' + date)
            json_filename = 'stats/' + date + '/chaos/' + meta + '-' + str(rank) + '.json'
            print('Checking local files... ', end='')
            if not os.path.isfile(json_filename):
                print('Not found.')
                try:
                    if AUTO_DOWNLOAD:
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
        if AUTO_DOWNLOAD:
            print('Downloading: ' + server_source_path)
            os.makedirs(os.path.dirname(json_filename), exist_ok=True)
            try:
                urllib.request.urlretrieve(server_source_path, json_filename)
            except urllib.request.HTTPError as e:
                raise SmogonError from e
    try:
        f = open(json_filename, 'r')
    except FileNotFoundError:
        raise
    json_data = f.read()
    data = json.loads(json_data)
    return data


def pokemon(name, date='default', meta='gen7ou', rank=1500):
    smogon_json = pokemon_usage_dict(date, meta, rank)
    pokemon_data = {'data': {}}
    try:
        pokemon_data.update({
            'data': smogon_json['data'][name],
            'Count': sum(smogon_json['data'][name]['Abilities'].values())
        })
    except KeyError as e:
        raise PokemonError(name) from e
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


def moves_dict(version='sm'):
    data = None
    json_filename = 'dex/' + version + '/moves.json'
    server_source_path = SERVER_URL + '/dex/' + version + '/moves/'

    if not os.path.isfile(json_filename):
        if AUTO_DOWNLOAD:
            print('Scraping: ' + server_source_path)
            os.makedirs(os.path.dirname(json_filename), exist_ok=True)
            data = scrape('moves', version)
            if not bool(data):
                raise SmogonError
            f = open(json_filename, 'w')
            f.write(json.dumps(data))
            f.close()
    if data is None:
        try:
            f = open(json_filename, 'r')
        except FileNotFoundError:
            raise
        json_data = f.read()
        data = json.loads(json_data)
    return data


def move(name, version='sm'):
    moves = moves_dict(version)
    name_key = _name_to_key(name)
    if name_key in moves:
        return moves[name_key]
    raise MoveError(name_key)


def _dex_browser(section, version='sm'):
    browser = webdriver.PhantomJS(PHANTOMJS_PATH)
    browser.get(SERVER_URL + '/dex/' + version + '/' + section + '/')
    browser.set_window_size(1280, 720)
    return browser


def _read_moves(soup):
    move_link = soup.find('div', 'MoveRow-name').a['href']
    move_name = soup.find('div', 'MoveRow-name').string
    move_id = _name_to_key(move_name)
    type_link = soup.find('div', 'MoveRow-type').a['href']
    type_id = type_link.strip('/').rsplit('/', 1)[-1]
    type_name = soup.find('div', 'MoveRow-type').string
    move_damage = soup.find('div', 'MoveRow-damage').div['class'][1]
    move_power = soup.find('div', 'MoveRow-power').span.string
    if not move_power.isnumeric():
        move_power = None
    move_accuracy = soup.find('div', 'MoveRow-accuracy').span.string.strip('%')
    if not move_accuracy.isnumeric():
        move_accuracy = None
    move_pp = soup.find('div', 'MoveRow-pp').span.string
    move_description = soup.find('div', 'MoveRow-description').string

    return {
        move_id: {
            'id': move_id,
            'url': move_link,
            'name': move_name,
            'type': {
                'id': type_id,
                'url': type_link,
                'name': type_name
            },
            'damage': move_damage,
            'power': move_power,
            'accuracy': move_accuracy,
            'pp': move_pp,
            'description': move_description
        }
    }


def _read_abilities(soup):
    ability_link = soup.find('div', 'AbilityRow-name').a['href']
    ability_id = ability_link.strip('/').rsplit('/', 1)[-1]
    ability_name = soup.find('div', 'AbilityRow-name').string
    ability_description = soup.find('div', 'AbilityRow-description').string

    return {
        ability_id: {
            'id': ability_id,
            'url': ability_link,
            'name': ability_name,
            'description': ability_description
        }
    }


def scrape(section, version='sm'):
    browser = _dex_browser(section, version=version)

    try:
        soup_read = globals()['_read_' + section]
    except KeyError as e:
        raise NotImplementedError('No scraper implemented for this section.') from e
    data = {}
    y_scroll = 0
    while True:
        visible_rows = browser.find_elements_by_class_name(DEX_SECTION_ROWS[section])
        for row in visible_rows:
            soup = BeautifulSoup(row.get_attribute('innerHTML'), 'html.parser')
            data.update(soup_read(soup))
        browser.execute_script('window.scrollBy(0, window.innerHeight + 1)')
        new_y = browser.execute_script('return window.pageYOffset;')
        if y_scroll == new_y:
            break
        else:
            y_scroll = new_y
    return data
