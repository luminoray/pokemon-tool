import pokemontool
import json
from bs4 import BeautifulSoup

browser = pokemontool.get_smogon_dex_json('moves')

move_dict = {}
runs = 0
y = 0
while True:
    body = browser.find_element_by_tag_name('body')
    visible_rows = browser.find_elements_by_class_name('MoveRow')
    for row in visible_rows:
        soup = BeautifulSoup(row.get_attribute('innerHTML'), 'html.parser')
        link = soup.find('div', 'MoveRow-name').a['href']
        item_id = link.strip('/').rsplit('/', 1)[-1]
        move_dict.update({
            item_id: {
                'url': link
            }
        })
    browser.execute_script('window.scrollBy(0, window.innerHeight + 1)')
    new_y = browser.execute_script('return window.pageYOffset;')
    if y == new_y:
        break
    else:
        y = new_y

print(json.dumps(move_dict))
