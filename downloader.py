import json
import requests
import argparse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from progress.bar import IncrementalBar

# CLI Setup
parser = argparse.ArgumentParser(description='Download Bible texts from supported websites.')
parser.add_argument('source', choices=['bible.com', 'biblia.pt'], help='Website to download from')
parser.add_argument('book_code', help='Book code (integer for bible.com, string for biblia.pt)')
args = parser.parse_args()

# Validate book_code for bible.com
if args.source == 'bible.com':
    try:
        book_code = int(args.book_code)
    except ValueError:
        parser.error("book_code must be an integer for bible.com")
else:
    book_code = args.book_code  # biblia.pt uses string codes

# Fetch book metadata for bible.com
if args.source == 'bible.com':
    url = f"https://www.bible.com/api/bible/version/{book_code}"
    # print("Book URL:", url)
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch book metadata: {response.text}")
    
    version_data = response.json()
    books = version_data["books"]
else:
    with open('books.json', 'r') as file:
        books = json.load(file)

# Function to fetch and parse a chapter
def fetch_chapter(source, book_code, book_alias, chapter):
    verses = {}
    try:
        if source == 'bible.com':
            url = f"https://events.bible.com/api/bible/chapter/3.1?id={book_code}&reference={book_alias}.{chapter}"
            #print(f"Fetching {book_code} {chapter} from {url}")
            response = requests.get(url)
            html_content = response.json()["content"]
            soup = BeautifulSoup(html_content, 'html.parser')
            
            verse_counter = 1
            for el in soup.select('.verse'):
                content = ''.join([c.text for c in el.select('.content')]).strip()
                if content:
                    verses[verse_counter] = content
                    verse_counter += 1
        
        elif source == 'biblia.pt':
            url = f"https://www.biblia.pt/biblia/{book_code}/{book_alias}.{chapter}"
            #print(f"Fetching {book_alias} {chapter} from {url}")
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            verse_spans = soup.find_all('span', attrs={'data-verse-org-id': True})
            for span in verse_spans:
                verse_id = span['data-verse-org-id']
                parts = verse_id.split('.')
                
                if len(parts) == 3 and parts[0] == book_alias and parts[1] == str(chapter):
                    try:
                        verse_num = int(parts[2])
                        verse_text = span.get_text(strip=True)
                        
                        if verse_num in verses:
                            verses[verse_num] += " " + verse_text
                        else:
                            verses[verse_num] = verse_text
                    except ValueError:
                        continue
        
    except Exception as e:
        print(f"\nError fetching {book_alias} {chapter}: {str(e)}")
        return None
    
    return {"number": chapter, "verses": [{"number": num, "text": text} for num, text in sorted(verses.items())]}

# Main processing
data = []
for book in books:
    if args.source == 'bible.com':
        book_alias = book['usfm'].upper()  # Use USFM and convert to uppercase
        book_name = book['human']  # Use human-readable name for JSON filename
    else:
        book_alias = book['aliases'][0]
        book_name = book['book']
    
    chapters = range(1, len(book['chapters']) + 1) if args.source == 'bible.com' else range(1, book['chapters'] + 1)
    
    bar = IncrementalBar(f"Processing {book_name}", max=len(chapters))
    book_chapters = []

    # Parallel chapter fetching
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(fetch_chapter, args.source, book_code, book_alias, chapter): chapter
            for chapter in chapters
        }

        for future in as_completed(futures):
            result = future.result()
            if result:
                book_chapters.append(result)
                bar.next()

    bar.finish()
    data.append({
        "book": book_alias,
        "name": book_name,
        "chapters": sorted(book_chapters, key=lambda c: c['number'])
    })

# Save output
output_filename = f"{book_name}.json"
with open(output_filename, 'w', encoding='utf-8') as outfile:
    json.dump(data, outfile, ensure_ascii=False, indent=2)

print(f"Saved output to {output_filename}")
