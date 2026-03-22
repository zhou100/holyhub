from typing import List, Dict
from holyhub.database import Database


class LocationServices:
    def __init__(self, database: Database):
        self.database = database

    def search_churches(self, city: str, state: str) -> List[Dict]:
        query = """
            SELECT church_id AS id, name, address, city, state,
                   denomination, service_times
            FROM Churches
            WHERE city = ? AND state = ?
        """
        try:
            return self.database.execute_query(query, (city, state))
        except Exception as e:
            return []
