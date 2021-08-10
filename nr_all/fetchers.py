#
# Copyright (c) 2019 UCT Prague.
#
# fetchers.py is part of CIS KROKD repository
# (see https://cis-git.vscht.cz/cis/cis-repo-invenio/cis-krokd-repository).
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
import functools

from invenio_pidstore.fetchers import FetchedPID
from nr_events.record import EventBaseRecord
from nr_generic.fetchers import nr_id_generic_fetcher
from nr_events.fetchers import nr_events_id_fetcher
from nr_generic.record import CommonBaseRecord
from nr_nresults.record import NResultBaseRecord
from nr_theses.fetchers import nr_theses_id_fetcher
from nr_nresults.fetchers import nr_nresults_id_fetcher
from nr_theses.record import ThesisBaseRecord
from nr_datasets.record import DatasetBaseRecord
from nr_datasets.fetchers import nr_datasets_id_fetcher


@functools.lru_cache(maxsize=1)
def prepare_schemas():
    CommonBaseRecord._prepare_schemas()
    EventBaseRecord._prepare_schemas()
    ThesisBaseRecord._prepare_schemas()
    NResultBaseRecord._prepare_schemas()
    DatasetBaseRecord._prepare_schemas()


def nr_all_id_fetcher(record_uuid, data):
    """Fetch an object restoration PID.

        :param record_uuid: Record UUID.
        :param data: Record content.
        :returns: A :class:`invenio_pidstore.fetchers.FetchedPID` that contains
            data['did'] as pid_value.
        """
    if '$schema' not in data:
        raise ValueError('Return _schema in search results')

    schema = data['$schema']

    prepare_schemas()

    if schema == CommonBaseRecord.PREFERRED_SCHEMA:
        fetched_pid = nr_id_generic_fetcher(record_uuid, data)
    elif schema == EventBaseRecord.PREFERRED_SCHEMA:
        fetched_pid = nr_events_id_fetcher(record_uuid, data)
    elif schema == ThesisBaseRecord.PREFERRED_SCHEMA:
        fetched_pid = nr_theses_id_fetcher(record_uuid, data)
    elif schema == NResultBaseRecord.PREFERRED_SCHEMA:
        fetched_pid = nr_nresults_id_fetcher(record_uuid, data)
    elif schema == DatasetBaseRecord.PREFERRED_SCHEMA:
        fetched_pid = nr_datasets_id_fetcher(record_uuid, data)
    else:
        raise ValueError(f'Unknown conversion of schema "{schema}" to pid type')

    if data.get('oarepo:draft'):
        return FetchedPID(
            provider=fetched_pid.provider,
            pid_type="d" + fetched_pid.pid_type,
            pid_value=fetched_pid.pid_value,
        )
    else:
        return fetched_pid
