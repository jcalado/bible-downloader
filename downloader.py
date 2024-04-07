from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import json
import re
import requests
import argparse
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser(description='Download bible.com texts and generate JSONs.')
parser.add_argument('book_code', metavar='Book Code', type=int,
                    help='book code for the bible version')
args = parser.parse_args()

chrome_options = Options()
chrome_options.add_argument("--incognito")
chrome_options.add_argument("--window-size=1280x720")

driver = webdriver.Chrome(options=chrome_options)

books = ["GEN", "EXO", "LEV", "NUM", "DEU", "JOS", "JDG", "RUT", "1SA", "2SA",
"1KI", "2KI", "1CH", "2CH", "EZR", "NEH", "EST", "JOB", "PSA", "PRO", "ECC",
"SNG", "ISA", "JER", "LAM", "EZK", "DAN", "HOS", "JOL", "AMO", "OBA", "JON",
"MIC", "NAM", "HAB", "ZEP", "HAG", "ZEC", "MAL", "MAT", "MRK", "LUK", "JHN",
"ACT", "ROM", "1CO", "2CO", "GAL", "EPH", "PHP", "COL", "1TH", "2TH", "1TI",
"2TI", "TIT", "PHM", "HEB", "JAS", "1PE", "2PE", "1JN", "2JN", "3JN", "JUD",
"REV"]
data = []
book_code = args.book_code

books_url = f"https://www.bible.com/json/bible/books/{book_code}"
driver.get(books_url)
books_el = driver.find_element(By.TAG_NAME, 'pre')


books_json = json.loads(books_el.text)

for book in books_json["items"]:
    print(book)

    chapters_url = f"https://www.bible.com/json/bible/books/{book_code}/{book['usfm']}/chapters"
    driver.close()
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(chapters_url)

    chapters_el = driver.find_element(By.TAG_NAME, 'pre')
    #print(chapters.text)

    y = json.loads(chapters_el.text)

    chapters_total = y['items'][-1:][0]['human']
    chapters = list(range(1, int(chapters_total) + 1))

    book_chapters = []

    for chapter in chapters:
        # https://events.bible.com/api/bible/chapter/3.1?id={book_code}&reference=GEN.1
        url = f"https://events.bible.com/api/bible/chapter/3.1?id={book_code}&reference={book['usfm']}.{chapter}"
        driver.get(url)

        x = driver.find_element(By.CSS_SELECTOR, 'pre').text
        chapter_text = json.loads(x)
        html_content = chapter_text["content"]



        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find elements following this CSS selector: .verse > span.content
        els = soup.select('.verse')

        verse = 1
        verses = []

        for el in els:
            
            # Search element for .content selectors
            content = el.select('.content')

            # Join all the text from all the elements
            content = ''.join([c.text for c in content]).strip()
            
            if content == '':
                continue
            else:
                print(verse)
                print(content)

                verses.append({
                    "number": verse,
                    "text": content
                })
                verse += 1

        book_chapters.append({ "number": chapter, "verses": verses })
    

    data.append({"book":book['usfm'], "name": book['human'], "chapters": book_chapters})

with open('data.json', 'a+', encoding='utf8') as outfile:
    json.dump(data, outfile, ensure_ascii=False)

driver.quit()
