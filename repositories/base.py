from supabase import Client
from typing import TypeVar, Generic, Type, List, Optional, Any
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class BaseRepository(Generic[T]):
    def __init__(self, client: Client, table_name: str, model: Type[T]):
        self.client = client
        self.table_name = table_name
        self.model = model

    def get_by_id(self, id: str) -> Optional[T]:
        response = self.client.table(self.table_name).select("*").eq("id", id).execute()
        if response.data:
            return self.model.model_validate(response.data[0])
        return None

    def get_all(self, **kwargs) -> List[T]:
        query = self.client.table(self.table_name).select("*")
        for k, v in kwargs.items():
            query = query.eq(k, v)
        response = query.execute()
        return [self.model.model_validate(item) for item in response.data]

    def create(self, data: dict) -> T:
        response = self.client.table(self.table_name).insert(data).execute()
        return self.model.model_validate(response.data[0])

    def update(self, id: str, data: dict) -> T:
        response = self.client.table(self.table_name).update(data).eq("id", id).execute()
        return self.model.model_validate(response.data[0])

    def delete(self, id: str) -> bool:
        self.client.table(self.table_name).delete().eq("id", id).execute()
        return True
