from invenio_records_rest.utils import deny_all, check_elasticsearch
from invenio_search import RecordsSearch

RECORDS_REST_ENDPOINTS = {
    # readonly url for both endpoints, does not have item route
    # as it is accessed from the endpoints above
    'all': dict(
        pid_type='nrall',
        pid_minter='nr_all_id_minter',
        pid_fetcher='nr_all_id_fetcher',
        default_endpoint_prefix=True,
        search_class=RecordsSearch,
        search_index='nr-all',
        search_serializers={
            'application/json': 'oarepo_validate:json_search',
        },
        list_route='/all/',
        default_media_type='application/json',
        max_result_window=1000000,

        # not used really
        item_route='/all/not-used-but-must-be-present',
        create_permission_factory_imp=deny_all,
        delete_permission_factory_imp=deny_all,
        update_permission_factory_imp=deny_all,
        read_permission_factory_imp=check_elasticsearch,
        record_serializers={
            'application/json': 'oarepo_validate:json_response',
        },
        # search_factory_imp='restoration.objects.search:objects_search_factory'
        # default search_factory_imp: invenio_records_rest.query.default_search_factory
    )
}

# TODO: dodělat facety a filtry pro souhrnný index

RECORDS_REST_FACETS = {}

RECORDS_REST_FILTERS = {}