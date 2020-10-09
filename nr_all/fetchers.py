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
from invenio_pidstore.fetchers import FetchedPID
from nr_common.fetchers import nr_id_fetcher
from nr_events.fetchers import nr_events_id_fetcher
from nr_theses.fetchers import nr_theses_id_fetcher
from nr_nresults.fetchers import nr_nresults_id_fetcher


def nr_all_id_fetcher(record_uuid, data):
    """Fetch an object restoration PID.

        :param record_uuid: Record UUID.
        :param data: Record content.
        :returns: A :class:`invenio_pidstore.fetchers.FetchedPID` that contains
            data['did'] as pid_value.
        """
    if "defended" in data:
        fetched_pid = nr_theses_id_fetcher(record_uuid, data)
    elif "events" in data:
        fetched_pid = nr_events_id_fetcher(record_uuid, data)
    elif "N_type" in data:
        fetched_pid = nr_nresults_id_fetcher(record_uuid, data)
    else:
        fetched_pid = nr_id_fetcher(record_uuid, data)
    if 'oarepo:validity' in data:
        return FetchedPID(
            provider=fetched_pid.provider,
            pid_type="d" + fetched_pid.pid_type,
            pid_value=fetched_pid.pid_value,
        )
    else:
        return fetched_pid
