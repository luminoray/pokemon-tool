import pokemontool
import constants
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('move', help='ID of the move')

args = parser.parse_args()

move_id = args.move

move = pokemontool.move(move_id, 'sm')
print('')
print('===================')
print(' * ' + move['name'] + ' -- ' + constants.SERVER_URL + move['url'])
print('===================')
print('Type: ' + move['type']['name'] + ' -- ' + constants.SERVER_URL + move['type']['url'])
print('Damage: ' + move['damage'])
print('Power: ' + str(move['power']))
print('Accuracy: ' + str(move['accuracy']))
print('Desc: ' + move['description'])
print('')
