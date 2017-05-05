import os
import urllib.request
import datetime
import json
import smogonscraper
import re

import constants


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
    server_release = constants.SERVER_URL + '/stats/' + date + '/'
    try:
        urllib.request.urlopen(server_release)
    except urllib.request.HTTPError as e:
        raise SmogonError from e


def _name_to_key(name):
    keyified = re.sub('[^0-9a-z_\-]+', '', name.lower().replace(' ', '_'))
    return keyified


def pokemon_dict(date='default', meta='gen7ou', rank=1500):
    json_filename = 'stats/' + date + '/chaos/' + meta + '-' + str(rank) + '.json'
    server_source_path = constants.SERVER_URL + '/' + json_filename
    if date == 'default':
        autodate = datetime.date.today()
        while True:
            date = autodate.strftime(constants.DATE_FORMAT)
            print('Trying date: ' + date)
            json_filename = 'stats/' + date + '/chaos/' + meta + '-' + str(rank) + '.json'
            print('Checking local files... ', end='')
            if not os.path.isfile(json_filename):
                print('Not found.')
                try:
                    if constants.AUTO_DOWNLOAD:
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
        if constants.AUTO_DOWNLOAD:
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
    data = f.read()
    json_data = json.loads(data)
    return json_data


def pokemon(name, date='default', meta='gen7ou', rank=1500):
    smogon_json = pokemon_dict(date, meta, rank)
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
    json_filename = 'dex/' + version + '/moves.json'
    server_source_path = constants.SERVER_URL + '/dex/' + version + '/moves/'

    if not os.path.isfile(json_filename):
        if constants.AUTO_DOWNLOAD:
            print('Scraping: ' + server_source_path)
            os.makedirs(os.path.dirname(json_filename), exist_ok=True)
            move_dict = smogonscraper.scrape_moves(version)
            if not bool(move_dict):
                raise SmogonError
            f = open(json_filename, 'w')
            f.write(json.dumps(move_dict))
            f.close()
    try:
        f = open(json_filename, 'r')
    except FileNotFoundError:
        raise
    data = f.read()
    json_data = json.loads(data)
    return json_data


def move(name, version='sm'):
    moves = moves_dict(version)
    try:
        move_data = moves[_name_to_key(name)]
    except KeyError as e:
        raise MoveError(name=name) from e
    return move_data

