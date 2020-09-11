from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk


class Elastic(object):
    def __init__(self, app=None, db=None, *args, **kwargs):
        if app:
            self.object = (
                Elasticsearch([app.config["ELASTICSEARCH_URL"]])
                if app.config["ELASTICSEARCH_URL"]
                else None
            )

        self.object = None
        self.db = db

    def init_app(self, app, db):
        self.object = (
            Elasticsearch([app.config["ELASTICSEARCH_URL"]])
            if app.config["ELASTICSEARCH_URL"]
            else None
        )
        self.db = db
        self.bulk_queue = []

    def add_to_bulk_queue(self, index, model_object, operation):
        if operation == 'delete':
            entry = {
                "_op_type": operation,
                "_index": index,
                "_type": index,
                "_id": model_object.id
            }
        elif operation == 'index':
            entry = {
                "_op_type": operation,
                "_index": index,
                "_type": index,
                "_id": model_object.id,
                "_source": self._create_payload(model_object)
            }
        else:
            return
        
        self.bulk_queue.append(entry)

    def clear_bulk_queue(self):
        self.bulk_queue = []
        
    def perform_bulk(self):
        bulk(self.object, self.bulk_queue)
        self.clear_bulk_queue()

    def _create_payload(self, model_object):
        payload = dict()
        for field in model_object.__searchable__:
            if isinstance(field, str):
                payload[field] = getattr(model_object, field)
            if isinstance(field, tuple):
                subfields = field[1]
                field = field[0]
                if not isinstance(getattr(model_object, field), list):
                    if len(subfields) == 1:
                        payload[field] = getattr(
                            getattr(model_object, field), subfields[0]
                        )
                    else:
                        payload[field] = dict()
                        for subfield in subfields:
                            payload[field][subfield] = getattr(
                                getattr(model_object, field), subfield
                            )
                else:
                    payload[field] = list()
                    for sub_model_object in getattr(model_object, field):
                        subfield_group = dict()
                        for subfield in subfields:
                            subfield_group[subfield] = getattr(
                                sub_model_object, subfield
                            )
                        payload[field].append(subfield_group)
        return payload

    def add_to_index(self, index, model_object):
        if not self.object:
            return
        # payload = dict()
        # for field in model.__searchable__:
        #     if "." in field:
        #         [field, subfield] = field.split(".")
        #         field_attr = getattr(model, field)
        #         if isinstance(field_attr, self.db.Model):
        #             payload[field] = getattr(field_attr, subfield)
        #         elif isinstance(field_attr, list):
        #             payload[field] = list()
        #             for i in field_attr:
        #                 if isinstance(i, self.db.Model):
        #                     subfield_attr = getattr(i, subfield)
        #                     payload[field].append(subfield_attr)

        #     else:
        #         payload[field] = getattr(model, field)
        payload = self._create_payload(model_object)
        self.object.index(index=index, doc_type=index, id=model_object.id, body=payload)

    def remove_from_index(self, index, model_object):
        if not self.object:
            return
        self.object.delete(index=index, doc_type=index, id=model_object.id)

    def query_index(self, index, query, page, per_page):
        if not self.object:
            return [], 0
        search = self.object.search(
            index=index,
            body={
                "query": {"multi_match": {"query": query, "fields": ["*"]}},
                "from": (page - 1) * per_page,
                "size": per_page,
            },
        )
        # ids = [int(hit['_id']) for hit in search['hits']['hits']]
        return search
