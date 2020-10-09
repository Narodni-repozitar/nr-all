import uuid

import pytest

from nr_all.minters import nr_all_id_minter


def test_nr_all_id_minter(app, db, base_json, taxonomy_tree):
    data = base_json
    del data["control_number"]
    record_uuid = uuid.uuid4()
    with pytest.raises(Exception, match="Should not be used as nr-all is readonly"):
        nr_all_id_minter(record_uuid=record_uuid, data=data)


def test_entry_points(app):
    assert 'nr_all' in app.extensions['invenio-pidstore'].minters.keys()
