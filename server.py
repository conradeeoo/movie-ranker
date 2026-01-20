from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import time
from difflib import SequenceMatcher
import os

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

def title_similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

@app.route('/api/get-movie', methods=['POST'])
def get_movie():
    try:
        data = request.json
        name = data['name']
        year = data['year']
        
        search_url = f"https://www.imdb.com/find/?q={name}+{year}&s=tt&ttype=ft"
        r = requests.get(search_url, headers=headers)
        
        if r.status_code != 200:
            return jsonify({'poster': None, 'director': None, 'actors': []})
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        all_links = soup.find_all('a', href=lambda x: x and '/title/tt' in x)
        if not all_links:
            return jsonify({'poster': None, 'director': None, 'actors': []})
        
        best_match = None
        best_score = 0
        
        for link in all_links[:5]:
            parent = link.find_parent()
            if parent:
                link_text = link.get_text(strip=True)
                if link_text:
                    similarity = title_similarity(name, link_text)
                    if similarity > best_score and similarity > 0.6:
                        best_score = similarity
                        best_match = link
        
        if not best_match:
            best_match = all_links[0]
        
        movie_url = "https://www.imdb.com" + best_match['href'].split('?')[0]
        
        time.sleep(0.5)
        r = requests.get(movie_url, headers=headers)
        
        if r.status_code != 200:
            return jsonify({'poster': None, 'director': None, 'actors': []})
        
        soup = BeautifulSoup(r.text, 'html.parser')
        
        poster = None
        img = soup.find('img', {'class': 'ipc-image'})
        if img and img.get('src'):
            poster = img['src']
        
        director = None
        actors = []
        
        all_people_links = soup.find_all('a', href=lambda x: x and '/name/nm' in x)
        if all_people_links:
            director = all_people_links[0].text.strip()
            actors = [link.text.strip() for link in all_people_links[1:4] if link.text.strip()]
        
        print(f"✅ {name} ({year}) - Match: {best_score:.2f} - Poster: {bool(poster)} - Director: {director}")
        
        return jsonify({
            'poster': poster,
            'director': director,
            'actors': [],
            'filtered': False
        })
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({'poster': None, 'director': None, 'actors': []})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3001))
    print(f"🚀 Backend running on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
