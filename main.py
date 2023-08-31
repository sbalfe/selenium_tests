import re
import time

from selenium import webdriver
from selenium.common import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver import ActionChains
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import os
from dotenv import load_dotenv
import spotipy
from spotipy import SpotifyOAuth

sp_dc = 'AQC0R74gtFxOKmGCWEV8MQOskHjMxCww_eKy56lJweqRTuOE9AsawTHTOFxZKqT0QGIkwl8TyT5D8xejJk3PglOBQXyhkN7QNoiClkmr4dqUhfWAvV6FzL3aUI6nc8kLYtQ9xqAXj9a1cGdG1L5Ogy-QmX3lhjA'
sp_key = 'bdbf51e7-cae0-4c32-9e46-8ae48c3e9612'

def authenticate():
    print("auth")
    load_dotenv("/home/shriller44/dev/python/misc/web_scraping_tests/.env")

    client_id = str(os.environ.get("SPOTIPY_CLIENT_ID"))
    client_secret = str(os.environ.get("SPOTIPY_CLIENT_SECRET"))
    scope = os.environ.get("SCOPE")
    redirect_uri = os.environ.get("REDIRECT_URI")

    return spotipy.Spotify(auth_manager=SpotifyOAuth(client_id,
                                                     client_secret,
                                                     redirect_uri=redirect_uri,
                                                     scope=scope))


def generate_options():
    options = Options()
    # options.headless = True
    options.log.level = "TRACE"
    options.binary_location = "/usr/bin/firefox"
    return options


def setup_driver():
    options = generate_options()
    service = Service('/usr/bin/geckodriver')

    driver = webdriver.Firefox(service=service, options=options)
    return driver


def add_cookies(driver):

    cookies = [
        {
            "name": "sp_dc",
            "value": sp_dc
        },
        {
            "name": "sp_key",
            "value": sp_key
        },
    ]

    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.refresh()


def discovered_on_playlist_ids(driver):
    driver.get('https://open.spotify.com/artist/1KXSj6uiC8Wtl2wCckVmAD/discovered-on')
    source = driver.page_source
    pattern = r'/playlist/(\w+)'
    matches = re.findall(pattern, source)
    print("Discover on playlist ids: ")
    for match in matches:
        print(match)
    print("thats all folks")


# Scroll down the page

def scroll_down(driver, track_list):
    # Find the element that represents the scrollable area
    scrollable_element = driver.find_element(By.XPATH, "/html/body/div[4]/div/div[2]/div[4]/div[1]/div[2]/div[4]/div/div")

    # Perform the scroll action using actions
    actions = ActionChains(driver)
    actions.move_to_element(scrollable_element)
    actions.click_and_hold().move_by_offset(0, 100).release().perform()

    # Wait for a short moment to let content load
    time.sleep(3)
    source = driver.page_source
    pattern = r'/track/(\w+)'
    matches = re.findall(pattern, source)
    print(f'found {len(matches)} tracks:')

    for match in matches:
        track_list.add(match)


def init():
    driver = setup_driver()
    add_cookies(driver)
    driver.refresh()
    time.sleep(2)
    return driver

def scope_to(driver):

    current_element = 1


    while True:
        for i in range(1,40):
            try:
                target = driver.find_element(By.XPATH,f'/html/body/div[4]/div/div[2]/div[4]/div[1]/div[2]/div[2]/div/div/div[2]/main/div[1]/section/div[2]/div[3]/div[1]/div[2]/div[2]/div[{i}]/div')

                previous_element = current_element
                current_element = int(target.text.split('\n')[0])

                if current_element < previous_element:
                    continue

                print(f'moving to: {current_element}')
                driver.execute_script("arguments[0].scrollIntoView();", target)
                time.sleep(0.5)
            except NoSuchElementException:
                print("target not found")
            except StaleElementReferenceException:
                print("stale exception")


def print_all_rows(driver, song_tag, elements):

    items = driver.find_elements(By.XPATH, f'//div[contains(@class, "{song_tag}")]')
    for item in items:
        elements.append(item)

    driver.execute_script("arguments[0].scrollIntoView();", items[-1])
    print_all_rows(driver)


def main():
    sp = authenticate()
    driver = init()



    discovered_on_playlist_ids(driver)






    time.sleep(5000)
    target = driver.find_element(By.XPATH,
                                 f'/html/body/div[4]/div/div[2]/div[4]/div[1]/div[2]/div[2]/div/div/div[2]/main/div[1]/section/div[2]/div[3]/div[1]/div[2]/div[2]/div[1]/div')

    song_tag = target.get_attribute("class").split(' ')[0]

    elements = []
    #print_all_rows(driver, song_tag, elements)
    #scope_to(driver)

    time.sleep(100)

    # Scroll down a few times
    for _ in range(9999):  # Scroll down 5 times, adjust as needed
        before_length = len(tracks)
        scroll_down(driver, tracks)
        after_length = len(tracks)
        if after_length == before_length:
            break

    print("Creating playlist with found tracks")
    pl = sp.user_playlist_create(sp.me()['id'], 'test_delete', public=False)

    track_uris = [sp.track(track_id)['uri'] for track_id in tracks]
    print(f'found {len((track_uris))} tracks')

    batch_size = 100
    for i in range(0, len(track_uris), batch_size):
        sp.playlist_add_items(pl['id'], track_uris[i:i + batch_size])

    print("waiting to exit...")
    time.sleep(5000)


if __name__ == '__main__':
    main()
