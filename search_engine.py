import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
CX = os.getenv("GOOGLE_CX")

class SearchEngine:
    def __init__(self, api_key=API_KEY, cx=CX):
        self.api_key = api_key
        self.cx = cx

    async def search(self, query: str):
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": 5
        }

        response = requests.get(url, params=params)
        data = response.json()

        results = []
        if "items" in data:
            for item in data["items"]:
                results.append({
                    "title": item["title"],
                    "link": item["link"],
                    "snippet": item["snippet"]
                })

        return results
