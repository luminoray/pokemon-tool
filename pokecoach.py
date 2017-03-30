import os
import urllib.request
import json

server_url = 'http://www.smogon.com/'


def get_smogon_json(date, meta='gen7ou', rank=1500):
    json_filename = 'stats/'+date+'/chaos/'+meta+'-'+str(rank)+'.json'
    os.makedirs(os.path.dirname(json_filename), exist_ok=True)

    if not os.path.isfile(json_filename):
        print('Downloading: ' + server_url + json_filename)
        urllib.request.urlretrieve(server_url + json_filename, json_filename)
    f = open(json_filename, 'r')
    data = f.read()
    json_data = json.loads(data)
    return json_data


def get_pokemon_data(pokemon, date, meta='gen7ou', rank=1500):
    smogon_json = get_smogon_json(date, meta, rank)
    pokemon_data = {'data': {}}
    pokemon_data.update({
        'data': smogon_json['data'][pokemon],
        'Count': sum(smogon_json['data'][pokemon]['Abilities'].values())
    })
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
