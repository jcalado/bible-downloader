import json
import requests
import argparse
from bs4 import BeautifulSoup
from progress.bar import IncrementalBar

parser = argparse.ArgumentParser(description='Download bible.com texts and generate JSONs.')
parser.add_argument('book_code', metavar='Book Code', type=int,
                    help='book code for the bible version')
args = parser.parse_args()

with open('books.json', 'r') as file:
    books = json.load(file)

data = []
book_code = args.book_code

for book in books:
    book_chapters = []
    chapters = range(1, book['chapters']+1)
    bar = IncrementalBar(f"A processar {book['book']}", max=book['chapters'])

    for chapter in chapters:
        verses = []
        verse = 1
        response = requests.get(f"https://events.bible.com/api/bible/chapter/3.1?id={book_code}&reference={book['aliases'][0]}.{chapter}")
        
        html_content = response.json()["content"]
        soup = BeautifulSoup(html_content, 'html.parser')

        els = soup.select('.verse')
        for el in els:
            
            content = el.select('.content')
            content = ''.join([c.text for c in content]).strip()
            
            if content == '':
                continue
            else:
                verses.append({
                    "number": verse,
                    "text": content
                })
                verse += 1

        book_chapters.append({ "number": chapter, "verses": verses })
        bar.next()
    
    bar.finish()
    data.append({"book":book['aliases'][0], "name": book['book'], "chapters": book_chapters})

with open(f'{book_code}.json', 'a+', encoding='utf8') as outfile:
    json.dump(data, outfile, ensure_ascii=False)