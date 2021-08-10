from elasticsearch_dsl.query import Term, Bool
from nr_common.search import NRRecordsSearch


class AllRecordsSearch(NRRecordsSearch):
    LIST_SOURCE_FIELDS = [
        'control_number', 'oarepo:validity.valid', 'oarepo:draft', 'title',
        'dateIssued', 'creator', 'resourceType', 'contributor', 'keywords',
        'subject', 'abstract', 'state', 'accessRights',
        'language', 'id', '_primary_community', 'communities',
        '_administration.primaryCommunity',
        '_administration.communities',
        '$schema'
    ]


class AllRecordsDraftSearch(AllRecordsSearch):
    class ActualMeta(NRRecordsSearch.ActualMeta):
        @classmethod
        def default_filter_factory(cls, search=None, **kwargs):
            qs = NRRecordsSearch.Meta.default_filter_factory(search=search, **kwargs)
            return Bool(must=[
                qs,
                Term(**{'oarepo:draft': True})
            ])


class AllRecordsPublishedSearch(AllRecordsSearch):
    class ActualMeta(NRRecordsSearch.ActualMeta):
        @classmethod
        def default_filter_factory(cls, search=None, **kwargs):
            qs = NRRecordsSearch.Meta.default_filter_factory(search=search, **kwargs)
            return Bool(must=[
                qs,
                Term(**{'oarepo:draft': False})
            ])
