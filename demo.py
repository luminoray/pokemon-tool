from collections import OrderedDict
import pokemontool
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('pokemon', help='Name of the pokemon')
parser.add_argument('category', help='Category of data to get')

args = parser.parse_args()

pokemon = args.pokemon
category = args.category

usage_data = pokemontool.pokemon(pokemon)
category_data = OrderedDict(sorted(usage_data['data_percent'][category].items(), key=lambda t: t[1], reverse=True))
print('')
print('===================')
print(pokemon)
print('===================')
for (item, usage) in category_data.items():
    if usage > 0.01:
        print(item + ' ' + str(round(usage*100, 2)) + '%')
