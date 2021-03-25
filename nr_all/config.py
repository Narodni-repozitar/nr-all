from invenio_records_rest.facets import terms_filter, range_filter
from invenio_records_rest.utils import deny_all, check_elasticsearch
from invenio_search import RecordsSearch
from oarepo_multilingual import language_aware_text_term_facet, \
    language_aware_text_terms_filter
from oarepo_records_draft import DRAFT_IMPORTANT_FILTERS, DRAFT_IMPORTANT_FACETS
from oarepo_records_draft.rest import term_facet
from oarepo_ui.facets import translate_facets, date_histogram_facet
from oarepo_ui.filters import group_by_terms_filter

from nr_all.record import AllNrRecord, all_index_name

_ = lambda x: x

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
FILTERS = {
    _('person'): terms_filter('person.keyword'),
    _('accessRights'): group_by_terms_filter('accessRights.title.en.raw', {
        "true": "open access",
        1: "open access",
        True: "open access",
        "1": "open access",
        False: ["embargoed access", "restricted access", "metadata only access"],
        0: ["embargoed access", "restricted access", "metadata only access"],
        "false": ["embargoed access", "restricted access", "metadata only access"],
        "0": ["embargoed access", "restricted access", "metadata only access"],
    }),
    _('resourceType'): language_aware_text_terms_filter('resourceType.title'),
    _('keywords'): language_aware_text_terms_filter('keywords'),
    _('subject'): language_aware_text_terms_filter('subjectAll'),
    _('language'): language_aware_text_terms_filter('language.title'),
    _('date'): range_filter('dateAll.date'),
    **DRAFT_IMPORTANT_FILTERS
}

FACETS = {
    'person': term_facet('person.keyword'),
    'accessRights': term_facet('accessRights.title.en.raw'),
    'resourceType': language_aware_text_term_facet('resourceType.title'),
    'keywords': language_aware_text_term_facet('keywords'),
    'subject': language_aware_text_term_facet('subjectAll'),
    'language': language_aware_text_term_facet('language.title'),
    'date': date_histogram_facet('dateAll.date'),
    **DRAFT_IMPORTANT_FACETS
}

RECORDS_REST_FACETS = {
    all_index_name: {
        "aggs": translate_facets(FACETS, label='{facet_key}',
                                 value='{value_key}'),
        "filters": FILTERS
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
