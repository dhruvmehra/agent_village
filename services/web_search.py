import requests
from bs4 import BeautifulSoup
from utils.logger import setup_logger
import time
import random
from nltk.tokenize import sent_tokenize
import nltk
import ssl
import certifi

logger = setup_logger(__name__)

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    try:
        nltk.download('punkt', quiet=True)
    except Exception as e:
        logger.warning(f"Failed to download NLTK data: {str(e)}")
        logger.warning("NLTK tokenization might not work properly.")

def search_web(query, num_results=5, max_retries=3):
    search_url = f"https://www.google.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            search_results = []
            for g in soup.find_all('div', class_='g')[:num_results]:
                anchor = g.find('a')
                if anchor:
                    link = anchor['href']
                    title = g.find('h3').text if g.find('h3') else "No title"
                    snippet = g.find('div', class_='VwiC3b').text if g.find('div', class_='VwiC3b') else "No snippet"
                    search_results.append({"title": title, "link": link, "snippet": snippet})
            
            return search_results
        except Exception as e:
            logger.error(f"Error during web search (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2)  # Wait before retrying
    
    return []

def fetch_webpage_content(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            sentences = sent_tokenize(text)
            return ' '.join(sentences[:50])  # Return first 50 sentences
        except Exception as e:
            logger.error(f"Error fetching webpage content (attempt {attempt + 1}): {str(e)}")
        
        if attempt < max_retries - 1:
            time.sleep(2)  # Wait before retrying
    
    return "Unable to fetch webpage content after multiple attempts."

def get_random_article(interests):
    query = random.choice(interests)
    search_results = search_web(query)
    if search_results:
        article = random.choice(search_results)
        content = fetch_webpage_content(article['link'])
        return {
            "title": article['title'],
            "content": content,
            "url": article['link']
        }
    return None