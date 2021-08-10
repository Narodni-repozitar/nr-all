import uuid

from nr_nresults.record import PublishedNResultRecord
from nr_theses.record import PublishedThesisRecord
from nr_datasets.record import PublishedDatasetRecord
from nr_all.fetchers import nr_all_id_fetcher


def test_nr_all_id_fetcher(app, db, base_json, taxonomy_tree, nresult_data, theses_data,
                                events_data, datasets_data, default_location):
    id_field = "control_number"
    nresult_data["control_number"] = "1"
    theses_data["control_number"] = "2"
    events_data["control_number"] = "3"
    datasets_data['id'] = '4'
    uuid_nresult = uuid.uuid4()
    uuid_theses = uuid.uuid4()
    uuid_datasets = uuid.uuid4()
    uuid_events = uuid.uuid4()
    nresult_record = PublishedNResultRecord.create(data=nresult_data, id_=uuid_nresult)
    theses_record = PublishedThesisRecord.create(data=theses_data, id_=uuid_theses)
    datasets_record = PublishedDatasetRecord.create(data=datasets_data, id_=uuid_datasets)
    # TODO: fix this after migrating to build schemas from datamodels
    # events_record = PublishedEventRecord.create(data=events_data, id_=uuid_events)
    fetched_nresult = nr_all_id_fetcher(uuid_nresult, nresult_data)
    fetched_theses = nr_all_id_fetcher(uuid_theses, theses_data)
    fetched_datasets = nr_all_id_fetcher(uuid_datasets, datasets_data)
    # fetched_events = nr_all_id_fetcher(uuid_theses, events_data)
    assert fetched_nresult.pid_type == "nrnrs"
    assert str(fetched_nresult.pid_value) == str(nresult_data[id_field])
    assert fetched_theses.pid_type == "nrthe"
    assert str(fetched_theses.pid_value) == str(theses_data[id_field])
    assert fetched_datasets.pid_type == 'datst'
    assert str(fetched_datasets.pid_value) == str(datasets_data['id'])
    # assert fetched_events.pid_type == "nrevt"
    # assert str(fetched_events.pid_value) == str(events_data[id_field])


def test_entry_points(app):
    assert 'nr_all' in app.extensions['invenio-pidstore'].fetchers.keys()
