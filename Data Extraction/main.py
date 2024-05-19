import asyncio
import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
import os

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()
    
async def extract_article_info(url, session, id_generator, stop_words, article_class):
    try:
        html = await fetch_url(session, url)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract article title
        article_title_tag = soup.find('h1', class_='entry-title')
        article_title = article_title_tag.get_text().strip() if article_title_tag else "No title found"
        
        # Search the entire HTML document for the article class
        article_container = soup.find(class_=article_class)
        
        if article_container:
            # Extract only the text content within the container
            article_text = article_container.get_text(separator='\n').strip()
            
            # Remove stop words
            article_words = article_text.split()
            article_words = [word for word in article_words if word.lower() not in stop_words]
            article_text = ' '.join(article_words)
            
            # Remove extra spaces
            article_text = ' '.join(article_text.split())
            
            return article_title, article_text
        else:
            print("Article container not found")
            return "Error", ""
    except Exception as e:
        print(f"Error extracting information from {url}: {e}")
        return "Error", ""

class SequentialIDGenerator:
    def __init__(self, prefix='blackassign', start=1, digits=4):
        self.prefix = prefix
        self.counter = start
        self.digits = digits

    def generate_id(self):
        id_format = '{{prefix}}{{number:0{digits}d}}'.format(digits=self.digits)
        generated_id = id_format.format(prefix=self.prefix, number=self.counter)
        self.counter += 1
        return generated_id

async def main(input_excel, output_directory, stop_words_directory, article_class):
    df = pd.read_excel(input_excel)
    urls = df['URL'].tolist()
    id_generator = SequentialIDGenerator()

    stop_words = set()
    for filename in os.listdir(stop_words_directory):
        with open(os.path.join(stop_words_directory, filename), 'r', encoding='latin-1') as file:
            stop_words.update(file.read().split())
    
    # print("Stop Words:", stop_words)  # Debug
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            task = asyncio.create_task(extract_article_info(url, session, id_generator, stop_words, article_class))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)

    for i, (article_title, article_text) in enumerate(results):
        filename = id_generator.generate_id() + ".txt"
        filepath = os.path.join(output_directory, filename)
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(f"Article Title: {article_title}\n\n")
            file.write(f"Article Text:\n{article_text}")
        print(f"Content extracted from {urls[i]} and saved to {filepath}")

# Example usage
input_excel = "input.xlsx"
output_directory = "output"
stop_words_directory = "../StopWords"
article_class = "td-post-content tagdiv-type"

# Create and run the event loop manually
loop = asyncio.get_event_loop()
loop.run_until_complete(main(input_excel, output_directory, stop_words_directory, article_class))
