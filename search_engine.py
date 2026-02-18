import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
CX = os.getenv("GOOGLE_CX")

print("DEBUG: API_KEY =", API_KEY)
print("DEBUG: CX =", CX)

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
        print("DEBUG: Status Code =", response.status_code)
        print("DEBUG: Response Text =", response.text[:500])  # первые 500 символов

        try:
            data = response.json()
        except Exception as e:
            print("ERROR: Failed to parse JSON:", e)
            return []

        results = []
        if "items" in data:
            for item in data["items"]:
                results.append({
                    "title": item["title"],
                    "link": item["link"],
                    "snippet": item["snippet"]
                })
        else:
            print("DEBUG: No items found in data:", data)

        return results
