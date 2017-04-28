import constants
from bs4 import BeautifulSoup
from selenium import webdriver


def _get_smogon_dex_browser(section, version='sm'):
    browser = webdriver.PhantomJS(constants.PHANTOMJS_PATH)
    browser.get(constants.SERVER_URL + '/dex/' + version + '/' + section + '/')
    browser.set_window_size(1280, 720)
    return browser


def scrape_moves(version='sm'):
    browser = _get_smogon_dex_browser('moves', version=version)

    move_dict = {}
    y = 0
    while True:
        visible_rows = browser.find_elements_by_class_name('MoveRow')
        for row in visible_rows:
            soup = BeautifulSoup(row.get_attribute('innerHTML'), 'html.parser')
            move_link = soup.find('div', 'MoveRow-name').a['href']
            move_id = move_link.strip('/').rsplit('/', 1)[-1]
            move_name = soup.find('div', 'MoveRow-name').string
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

            move_dict.update({
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
            })
        browser.execute_script('window.scrollBy(0, window.innerHeight + 1)')
        new_y = browser.execute_script('return window.pageYOffset;')
        if y == new_y:
            break
        else:
            y = new_y

    return move_dict
