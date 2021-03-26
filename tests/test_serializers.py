from pprint import pprint

from nr_all.serializers import NrJSONSerializer


def test_result_postprocess():
    search_result = {
        "aggregations": {
            'keywords': {'doc_count_error_upper_bound': 0, 'sum_other_doc_count': 0, 'buckets': []},
            'accessRights': {
                'doc_count_error_upper_bound': 0, 'sum_other_doc_count': 0,
                'buckets': [{'key': 'open access', 'doc_count': 276565},
                            {'key': 'metadata only access', 'doc_count': 36813},
                            {'key': 'restricted access', 'doc_count': 11778}]
            },
            'resourceType': {
                'doc_count_error_upper_bound': 0, 'sum_other_doc_count': 0,
                'buckets': [{'key': 'Theses (etds)', 'doc_count': 282148},
                            {'key': 'Bachelor theses', 'doc_count': 132139},
                            {'key': 'Master theses', 'doc_count': 126654},
                            {'key': 'Conference materials', 'doc_count': 25346},
                            {'key': 'Conference papers', 'doc_count': 24151},
                            {'key': 'Reports', 'doc_count': 15861},
                            {'key': 'Doctoral theses', 'doc_count': 14836},
                            {'key': 'Rigorous theses', 'doc_count': 8269},
                            {'key': 'Project reports', 'doc_count': 7234},
                            {'key': 'Research reports', 'doc_count': 7222},
                            {'key': 'Other specialized materials', 'doc_count': 1836},
                            {'key': 'Studies and analyses', 'doc_count': 1483},
                            {'key': 'Conference proceedings', 'doc_count': 1119},
                            {'key': 'Statistical and status reports', 'doc_count': 785},
                            {'key': 'Methodologies and procedures', 'doc_count': 620},
                            {'key': 'Annual reports', 'doc_count': 477},
                            {'key': 'Methodologies without certification', 'doc_count': 354},
                            {'key': 'Trade literature', 'doc_count': 339},
                            {'key': 'Certified methodologies', 'doc_count': 266},
                            {'key': 'Post-doctoral theses', 'doc_count': 250},
                            {'key': 'Books', 'doc_count': 71},
                            {'key': 'Press releases', 'doc_count': 69},
                            {'key': 'Business trip reports', 'doc_count': 63},
                            {'key': 'Conference programmes', 'doc_count': 41},
                            {'key': 'Conference posters', 'doc_count': 35},
                            {'key': 'Articles', 'doc_count': 27},
                            {'key': 'Exhibition catalogues and guides', 'doc_count': 11},
                            {'key': 'Field reports', 'doc_count': 11},
                            {'key': 'Educational materials', 'doc_count': 3}]
            }
        }
    }
    res = NrJSONSerializer.post_process_search_result(search_result)
    pprint(res)
