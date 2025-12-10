from elasticsearch import Elasticsearch
from typing import Optional, Dict, Any
import json

from ..core.config import settings
from ..schemas.book import BookSearchRequest


class SearchService:
    _client: Optional[Elasticsearch] = None

    @classmethod
    def get_client(cls) -> Elasticsearch:
        if cls._client is None:
            cls._client = Elasticsearch(
                [settings.ELASTICSEARCH_URL],
                verify_certs=False
            )
        return cls._client

    @classmethod
    async def create_index(cls):
        client = cls.get_client()

        index_body = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 1,
                "analysis": {
                    "analyzer": {
                        "kazakh_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": ["lowercase", "kazakh_stop", "kazakh_stemmer"]
                        }
                    },
                    "filter": {
                        "kazakh_stop": {
                            "type": "stop",
                            "stopwords": ["және", "бірақ", "немесе", "сондықтан"]
                        },
                        "kazakh_stemmer": {
                            "type": "stemmer",
                            "language": "kazakh"
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    "book_id": {"type": "integer"},
                    "title": {
                        "type": "text",
                        "analyzer": "kazakh_analyzer",
                        "fields": {
                            "keyword": {"type": "keyword"}
                        }
                    },
                    "description": {"type": "text", "analyzer": "kazakh_analyzer"},
                    "isbn": {"type": "keyword"},
                    "authors": {"type": "text", "analyzer": "kazakh_analyzer"},
                    "publish_year": {"type": "integer"},
                    "publisher": {"type": "keyword"},
                    "language": {"type": "keyword"},
                    "category": {"type": "keyword"},
                    "created_at": {"type": "date"}
                }
            }
        }

        if not client.indices.exists(index="books"):
            client.indices.create(index="books", body=index_body)

    @classmethod
    async def index_book(cls, book):
        client = cls.get_client()

        authors = [author.full_name for author in book.authors]
        category = book.category.category_name if book.category else ""

        doc = {
            "book_id": book.book_id,
            "title": book.title,
            "description": book.description or "",
            "isbn": book.isbn or "",
            "authors": authors,
            "publish_year": book.publish_year,
            "publisher": book.publisher or "",
            "language": book.language,
            "category": category,
            "created_at": book.created_at.isoformat() if book.created_at else None
        }

        client.index(index="books", id=book.book_id, body=doc)

    @classmethod
    async def search_books(cls, search_request: BookSearchRequest) -> Optional[Dict[str, Any]]:
        client = cls.get_client()

        if not client.ping():
            return None

        query_body = {
            "query": {
                "bool": {
                    "must": []
                }
            },
            "from": (search_request.page - 1) * search_request.size,
            "size": search_request.size,
            "sort": [
                {"_score": {"order": "desc"}}
            ]
        }

        if search_request.query:
            query_body["query"]["bool"]["must"].append({
                "multi_match": {
                    "query": search_request.query,
                    "fields": ["title^3", "description^2", "authors"],
                    "fuzziness": "AUTO"
                }
            })
        if search_request.author:
            query_body["query"]["bool"]["must"].append({
                "match": {"authors": search_request.author}
            })
        if search_request.category:
            query_body["query"]["bool"]["must"].append({
                "term": {"category": search_request.category}
            })

        if search_request.year_from or search_request.year_to:
            range_filter = {}
            if search_request.year_from:
                range_filter["gte"] = search_request.year_from
            if search_request.year_to:
                range_filter["lte"] = search_request.year_to

            query_body["query"]["bool"]["must"].append({
                "range": {"publish_year": range_filter}
            })
        if search_request.language:
            query_body["query"]["bool"]["must"].append({
                "term": {"language": search_request.language}
            })

        try:
            result = client.search(index="books", body=query_body)
            return result
        except Exception as e:
            print(f"Elasticsearch іздеу қатесі: {e}")
            return None

    @classmethod
    async def update_book_index(cls, book_id: int, update_data: dict):
        client = cls.get_client()

        if client.exists(index="books", id=book_id):
            client.update(index="books", id=book_id, body={"doc": update_data})

    @classmethod
    async def delete_book_from_index(cls, book_id: int):
        client = cls.get_client()

        if client.exists(index="books", id=book_id):
            client.delete(index="books", id=book_id)