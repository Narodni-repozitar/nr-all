from invenio_records_rest.utils import deny_all, check_elasticsearch
from invenio_search import RecordsSearch
from nr_common.config import FACETS, CURATOR_FACETS, FILTERS, CURATOR_FILTERS
from oarepo_records_draft import DRAFT_IMPORTANT_FACETS, DRAFT_IMPORTANT_FILTERS
from oarepo_ui.facets import translate_facets

from nr_all.record import AllNrRecord, all_index_name

RECORDS_REST_ENDPOINTS = {
    # readonly url for both endpoints, does not have item route
    # as it is accessed from the endpoints above
    'all': dict(
        pid_type='nrall',
        pid_minter='nr_all',
        pid_fetcher='nr_all',
        default_endpoint_prefix=True,
        search_class=RecordsSearch,
        record_class=AllNrRecord,
        search_index=all_index_name,
        search_serializers={
            'application/json': 'nr_all.serializers:json_search',
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


RECORDS_REST_FACETS = {
    all_index_name: {
        "aggs": translate_facets({**FACETS, **CURATOR_FACETS, **DRAFT_IMPORTANT_FACETS}, label='{facet_key}',
                                 value='{value_key}'),
        "filters": {**FILTERS, **CURATOR_FILTERS, **DRAFT_IMPORTANT_FILTERS}
    },
}

RECORDS_REST_SORT_OPTIONS = {
    all_index_name: {
        'alphabetical': {
            'title': 'alphabetical',
            'fields': [
                'title.cs.raw'
            ],
            'default_order': 'asc',
            'order': 1
        },
        'best_match': {
            'title': 'Best match',
            'fields': ['_score'],
            'default_order': 'desc',
            'order': 1,
        }
    }
}

RECORDS_REST_DEFAULT_SORT = {
    all_index_name: {
        'query': 'best_match',
        'noquery': 'best_match'
    }
}
