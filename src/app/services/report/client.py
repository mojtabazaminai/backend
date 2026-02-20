from typing import Any, Dict

import httpx

class InferenceClient:
    def __init__(self, base_url: str = "http://property-inference", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout

    async def post(self, path: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}{path}", json=json_body)
            response.raise_for_status()
            return response.json()
