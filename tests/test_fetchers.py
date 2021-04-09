import uuid

from nr_events.record import PublishedEventRecord
from nr_nresults.record import PublishedNResultRecord
from nr_theses.record import PublishedThesisRecord

from nr_all.fetchers import nr_all_id_fetcher


def test_nr_all_id_fetcher(app, db, base_json, taxonomy_tree, nresult_data, theses_data,
                                events_data):
    id_field = "control_number"
    nresult_data["control_number"] = "1"
    theses_data["control_number"] = "2"
    events_data["control_number"] = "3"
    uuid_nresult = uuid.uuid4()
    uuid_theses = uuid.uuid4()
    uuid_events = uuid.uuid4()
    nresult_record = PublishedNResultRecord.create(data=nresult_data, id_=uuid_nresult)
    theses_record = PublishedThesisRecord.create(data=theses_data, id_=uuid_theses)
    events_record = PublishedEventRecord.create(data=events_data, id_=uuid_events)
    fetched_nresult = nr_all_id_fetcher(uuid_nresult, nresult_data)
    fetched_theses = nr_all_id_fetcher(uuid_theses, theses_data)
    fetched_events = nr_all_id_fetcher(uuid_theses, events_data)
    assert fetched_nresult.pid_type == "nrnrs"
    assert str(fetched_nresult.pid_value) == str(nresult_data[id_field])
    assert fetched_theses.pid_type == "nrthe"
    assert str(fetched_theses.pid_value) == str(theses_data[id_field])
    assert fetched_events.pid_type == "nrevt"
    assert str(fetched_events.pid_value) == str(events_data[id_field])


def test_entry_points(app):
    assert 'nr_all' in app.extensions['invenio-pidstore'].fetchers.keys()
