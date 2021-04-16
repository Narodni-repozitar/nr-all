import json
from copy import deepcopy

from elasticsearch import VERSION as ES_VERSION
from invenio_records_rest.serializers import record_responsify, search_responsify
from oarepo_validate import JSONSerializer

lt_es7 = ES_VERSION[0] < 7


# TODO: přesunout, pravděpodobně do nr-common
class NrJSONSerializer(JSONSerializer):
    def serialize_search(self, pid_fetcher, search_result, links=None, item_links_factory=None,
                         **kwargs):
        """Serialize a search result.

                :param pid_fetcher: Persistent identifier fetcher.
                :param search_result: Elasticsearch search result.
                :param links: Dictionary of links to add to response.
                """
        search_result = self.post_process_search_result(search_result)
        total = search_result['hits']['total'] if lt_es7 else \
            search_result['hits']['total']['value']
        return json.dumps(dict(
            hits=dict(
                hits=[self.transform_search_hit(
                    pid_fetcher(hit['_id'], hit['_source']),
                    hit,
                    links_factory=item_links_factory,
                    **kwargs
                ) for hit in search_result['hits']['hits']],
                total=total,
            ),
            links=links or {},
            aggregations=search_result.get('aggregations', dict()),
        ), **self._format_args())

    @staticmethod
    def post_process_search_result(search_result):
        access_rights_container = search_result.get("aggregations", {}).get("nested#accessRights", None)
        if access_rights_container:
            access_rights = access_rights_container.get("sterms#inner_facet", None)
            if access_rights:
                buckets = access_rights.get("buckets", [])
                open_access: int = 0
                close_access: int = 0
                for bucket in buckets:
                    if bucket["key"] == "open access":
                        open_access += bucket["doc_count"]
                    else:
                        close_access += bucket["doc_count"]
                new_buckets = [
                    {"key": 1, "key_as_string": "true", "doc_count": open_access},
                    {"key": 0, "key_as_string": "false", "doc_count": close_access}
                ]
                new_buckets = [bucket for bucket in new_buckets if bucket["doc_count"] > 0]
                is_open_access = deepcopy(access_rights)
                is_open_access["buckets"] = new_buckets
                access_rights_container["sterms#inner_facet"] = is_open_access
        return search_result


json_serializer = NrJSONSerializer(replace_refs=False)

json_response = record_responsify(json_serializer, 'application/json')
json_search = search_responsify(json_serializer, 'application/json')
