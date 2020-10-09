from __future__ import absolute_import, print_function

import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import pytest
from elasticsearch import Elasticsearch
from flask import Flask, make_response
from flask_login import LoginManager, login_user
from flask_principal import RoleNeed, Principal, Permission
from flask_taxonomies.proxies import current_flask_taxonomies
from flask_taxonomies.term_identification import TermIdentification
from invenio_access import InvenioAccess
from invenio_accounts import InvenioAccounts
from invenio_accounts.models import User
from invenio_base.signals import app_loaded
from invenio_celery import InvenioCelery
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidstore import InvenioPIDStore
from invenio_pidstore.providers.recordid import RecordIdProvider
from invenio_records import InvenioRecords
from invenio_records_rest import InvenioRecordsREST
from invenio_records_rest.schemas.fields import SanitizedUnicode
from invenio_records_rest.utils import PIDConverter
from invenio_records_rest.views import create_blueprint_from_app
from invenio_search import InvenioSearch
from marshmallow import Schema
from oarepo_mapping_includes.ext import OARepoMappingIncludesExt
from oarepo_records_draft.ext import RecordsDraft
from oarepo_references import OARepoReferences
from oarepo_taxonomies.cli import init_db
from oarepo_taxonomies.ext import OarepoTaxonomies
from sqlalchemy_utils import database_exists, create_database, drop_database

from nr_nresults.ext import NRNresults
from tests.helpers import set_identity


@pytest.yield_fixture(scope="module")
def app():
    instance_path = tempfile.mkdtemp()
    app = Flask('testapp', instance_path=instance_path)

    app.config.update(
        JSONSCHEMAS_HOST="nusl.cz",
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SERVER_NAME='127.0.0.1:5000',
        INVENIO_INSTANCE_PATH=instance_path,
        DEBUG=True,
        # in tests, api is not on /api but directly in the root
        PIDSTORE_RECID_FIELD='pid',
        FLASK_TAXONOMIES_URL_PREFIX='/2.0/taxonomies/',
        # RECORDS_REST_ENDPOINTS=RECORDS_REST_ENDPOINTS,
        CELERY_BROKER_URL='amqp://guest:guest@localhost:5672//',
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_RESULT_BACKEND='cache',
        CELERY_CACHE_BACKEND='memory',
        CELERY_TASK_EAGER_PROPAGATES=True,
        SUPPORTED_LANGUAGES=["cs", "en"],
        ELASTICSEARCH_DEFAULT_LANGUAGE_TEMPLATE={
            "type": "text",
            "fields": {
                "keywords": {
                    "type": "keyword"
                }
            }
        }
    )

    app.secret_key = 'changeme'
    print(os.environ.get("INVENIO_INSTANCE_PATH"))

    InvenioDB(app)
    OarepoTaxonomies(app)
    OARepoReferences(app)
    InvenioAccounts(app)
    InvenioAccess(app)
    Principal(app)
    InvenioJSONSchemas(app)
    InvenioSearch(app)
    InvenioIndexer(app)
    OARepoMappingIncludesExt(app)
    InvenioRecords(app)
    InvenioRecordsREST(app)
    InvenioCelery(app)
    NRNresults(app)
    InvenioPIDStore(app)
    # Invenio Records Draft initialization
    RecordsDraft(app)
    app.url_map.converters['pid'] = PIDConverter

    # Celery
    print(app.config["CELERY_BROKER_URL"])

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def basic_user_loader(user_id):
        user_obj = User.query.get(int(user_id))
        return user_obj

    app.register_blueprint(create_blueprint_from_app(app))

    @app.route('/test/login/<int:id>', methods=['GET', 'POST'])
    def test_login(id):
        print("test: logging user with id", id)
        response = make_response()
        user = User.query.get(id)
        login_user(user)
        set_identity(user)
        return response

    # app.extensions['invenio-search'].mappings["test"] = mapping
    # app.extensions["invenio-jsonschemas"].schemas["test"] = schema

    app_loaded.send(app, app=app)

    with app.app_context():
        # app.register_blueprint(taxonomies_blueprint)
        print(app.url_map)
        yield app

    shutil.rmtree(instance_path)


@pytest.fixture(scope="module")
def db(app):
    """Create database for the tests."""
    dir_path = os.path.dirname(__file__)
    parent_path = str(Path(dir_path).parent)
    db_path = os.environ.get('SQLALCHEMY_DATABASE_URI', f'sqlite:////{parent_path}/database.db')
    os.environ["INVENIO_SQLALCHEMY_DATABASE_URI"] = db_path
    app.config.update(
        SQLALCHEMY_DATABASE_URI=db_path
    )
    if database_exists(str(db_.engine.url)):
        drop_database(db_.engine.url)
    if not database_exists(str(db_.engine.url)):
        create_database(db_.engine.url)
    db_.create_all()
    subprocess.run(["invenio", "taxonomies", "init"])
    runner = app.test_cli_runner()
    result = runner.invoke(init_db)
    if result.exit_code:
        print(result.output, file=sys.stderr)
    assert result.exit_code == 0
    yield db_

    # Explicitly close DB connection
    db_.session.close()
    db_.drop_all()


@pytest.fixture()
def es():
    return Elasticsearch()


@pytest.yield_fixture
def es_index(es):
    index_name = "test_index"
    if not es.indices.exists(index=index_name):
        yield es.indices.create(index_name)

    if es.indices.exists(index=index_name):
        es.indices.delete(index_name)


@pytest.fixture
def client(app, db):
    from flask_taxonomies.models import Base
    Base.metadata.create_all(db.engine)
    return app.test_client()


@pytest.fixture
def permission_client(app, db):
    app.config.update(
        FLASK_TAXONOMIES_PERMISSION_FACTORIES={
            'taxonomy_create': [Permission(RoleNeed('admin'))],
            'taxonomy_update': [Permission(RoleNeed('admin'))],
            'taxonomy_delete': [Permission(RoleNeed('admin'))],

            'taxonomy_term_create': [Permission(RoleNeed('admin'))],
            'taxonomy_term_update': [Permission(RoleNeed('admin'))],
            'taxonomy_term_delete': [Permission(RoleNeed('admin'))],
            'taxonomy_term_move': [Permission(RoleNeed('admin'))],
        }
    )
    from flask_taxonomies.models import Base
    Base.metadata.create_all(db.engine)
    return app.test_client()


@pytest.fixture
def tax_url(app):
    url = app.config['FLASK_TAXONOMIES_URL_PREFIX']
    if not url.endswith('/'):
        url += '/'
    return url


@pytest.fixture(scope="module")
def taxonomy(app, db):
    taxonomy = current_flask_taxonomies.create_taxonomy("test_taxonomy", extra_data={
        "title":
            {
                "cs": "test_taxonomy",
                "en": "test_taxonomy"
            }
    })
    db.session.commit()
    return taxonomy


@pytest.fixture(scope="module")
def taxonomy_tree(app, db, taxonomy):
    # accessRights
    id1 = TermIdentification(taxonomy=taxonomy, slug="c_abf2")
    term1 = current_flask_taxonomies.create_term(id1, extra_data={
        "title": {
            "cs": "otevřený přístup",
            "en": "open access"
        },
        "relatedURI": {
            "coar": "http://purl.org/coar/access_right/c_abf2",
            "vocabs": "https://vocabs.acdh.oeaw.ac.at/archeaccessrestrictions/public",
            "eprint": "http://purl.org/eprint/accessRights/OpenAccess"
        }
    })

    # resource type
    id2 = TermIdentification(taxonomy=taxonomy, slug="bakalarske_prace")
    term2 = current_flask_taxonomies.create_term(id2, extra_data={
        "title": {
            "cs": "Bakalářské práce",
            "en": "Bachelor’s theses"
        }
    })

    # institution
    id3 = TermIdentification(taxonomy=taxonomy, slug="61384984")
    term3 = current_flask_taxonomies.create_term(id3, extra_data={
        "title": {
            "cs": "Akademie múzických umění v Praze",
            "en": "Academy of Performing Arts in Prague"
        },
        "type": "veřejná VŠ",
        "aliases": ["AMU"],
        "related": {
            "rid": "51000"
        },
        "address": "Malostranské náměstí 259/12, 118 00 Praha 1",
        "ico": "61384984",
        "url": "https://www.amu.cz",
        "provider": True,
    })

    # language
    id4 = TermIdentification(taxonomy=taxonomy, slug="cze")
    term4 = current_flask_taxonomies.create_term(id4, extra_data={
        "title": {
            "cs": "čeština",
            "en": "Czech"
        }
    })

    # contributor
    id5 = TermIdentification(taxonomy=taxonomy, slug="supervisor")
    term5 = current_flask_taxonomies.create_term(id5, extra_data={
        "title": {
            "cs": "supervizor",
            "en": "supervisor"
        },
        "dataCiteCode": "Supervisor"
    })

    # funder
    id6 = TermIdentification(taxonomy=taxonomy, slug="ntk")
    term6 = current_flask_taxonomies.create_term(id6, extra_data={
        "title": {
            "cs": "Národní technická knihovna",
            "en": "National library of technology"
        },
        "funderISVaVaICode": "123456789"
    })

    # country
    id7 = TermIdentification(taxonomy=taxonomy, slug="cz")
    term7 = current_flask_taxonomies.create_term(id7, extra_data={
        "title": {
            "cs": "Česko",
            "en": "Czechia"
        },
        "code": {
            "number": "203",
            "alpha2": "CZ",
            "alpha3": "CZE"
        }
    })

    # relationship
    id8 = TermIdentification(taxonomy=taxonomy, slug="isversionof")
    term8 = current_flask_taxonomies.create_term(id8, extra_data={
        "title": {
            "cs": "jeVerzí",
            "en": "isVersionOf"
        }
    })

    # rights
    id9 = TermIdentification(taxonomy=taxonomy, slug="copyright")
    term9 = current_flask_taxonomies.create_term(id9, extra_data={
        "title": {
            "cs": "Dílo je chráněno podle autorského zákona č. 121/2000 Sb.",
            "en": "This work is protected under the Copyright Act No. 121/2000 Coll."
        }
    })

    # series
    id9 = TermIdentification(taxonomy=taxonomy, slug="maj")
    term9 = current_flask_taxonomies.create_term(id9, extra_data={
        "name": "maj",
        "volume": "1"
    })

    # subject
    id10 = TermIdentification(taxonomy=taxonomy, slug="psh3001")
    term10 = current_flask_taxonomies.create_term(id10, extra_data={
        "title": {
            "cs": "Reynoldsovo číslo",
            "en": "Reynolds number"
        },
        "reletedURI": ["http://psh.techlib.cz/skos/PSH3001"],
        "DateRevised": "2007-01-26T16:14:37"
    })

    id11 = TermIdentification(taxonomy=taxonomy, slug="psh3000")
    term11 = current_flask_taxonomies.create_term(id11, extra_data={
        "title": {
            "cs": "turbulentní proudění",
            "en": "turbulent flow"
        },
        "reletedURI": ["http://psh.techlib.cz/skos/PSH3000"],
        "DateRevised": "2007-01-26T16:14:37"
    })

    id12 = TermIdentification(taxonomy=taxonomy, slug="D010420")
    term12 = current_flask_taxonomies.create_term(id12, extra_data={
        "title": {
            "cs": "pentany",
            "en": "Pentanes"
        },
        "reletedURI": ["http://www.medvik.cz/link/D010420", "http://id.nlm.nih.gov/mesh/D010420"],
        "DateRevised": "2007-01-26T16:14:37",
        "DateCreated": "2007-01-26T16:14:37",
        "DateDateEstablished": "2007-01-26T16:14:37",
    })

    # studyField
    id13 = TermIdentification(taxonomy=taxonomy, slug="O_herectvi-alternativniho-divadla")
    term13 = current_flask_taxonomies.create_term(id13, extra_data={
        "title": {
            "cs": "Herectví alternativního divadla",
        },
        "AKVO": "8203R082"
    })

    # conference
    id14 = TermIdentification(taxonomy=taxonomy, slug="cze_conference")
    term14 = current_flask_taxonomies.create_term(id14, extra_data={
        "title": {
            "cs": "Česká konference",
        },
    })

    # certifying authority
    id15 = TermIdentification(taxonomy=taxonomy, slug="mdcr")
    term15 = current_flask_taxonomies.create_term(id15, extra_data={
        "title": {
            "cs": "Ministerstvo dopravy",
            "en": "Ministry of transport"
        },
    })

    # N_resultUsage
    id16 = TermIdentification(taxonomy=taxonomy, slug="C")
    term16 = current_flask_taxonomies.create_term(id16, extra_data={
        "title": {
            "cs": "Výsledek je užíván bez omezení okruhu uživatelů",
        },
    })

    # N_resultUsage
    id17 = TermIdentification(taxonomy=taxonomy, slug="A")
    term17 = current_flask_taxonomies.create_term(id17, extra_data={
        "title": {
            "cs": "certifikovaná metodika (NmetC)",
        },
    })

    db.session.commit()


def get_pid():
    """Generates a new PID for a record."""
    record_uuid = uuid.uuid4()
    provider = RecordIdProvider.create(
        object_type='rec',
        object_uuid=record_uuid,
    )
    return record_uuid, provider.pid.pid_value


@pytest.fixture()
def base_json():
    return {
        "accessRights": [{
            "is_ancestor": False,
            "links": {
                "self": "http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/c-abf2"
            }
        }],

        "control_number": "411100",
        "creator": [
            {
                "name": "Daniel Kopecký"
            }
        ],
        "dateIssued": "2010-07-01",
        "keywords": [
            {"cs": "1", "en": "1"},
            {"cs": "2", "en": "2"},
            {"cs": "3", "en": "3"},
        ],
        "language": [
            {
                "is_ancestor": False,
                "links": {
                    "self": "http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/cze"
                }
            }
        ],
        "provider": [
            {
                "is_ancestor": False,
                "links": {
                    "self": "http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/61384984"
                }
            }
        ],
        "resourceType": [
            {
                "is_ancestor": False,
                "links": {
                    "self": "http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/bakalarske-prace"
                }
            }
        ],
        "title": [{
            "cs": "Testovací záznam",
            "en": "Test record"
        }]
    }


@pytest.fixture()
def base_json_dereferenced():
    return {
        'accessRights': [{
            'is_ancestor': False,
            'links': {
                'self': 'http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/c-abf2'
            },
            'relatedURI': {
                'coar': 'http://purl.org/coar/access_right/c_abf2',
                'eprint': 'http://purl.org/eprint/accessRights/OpenAccess',
                'vocabs':
                    'https://vocabs.acdh.oeaw.ac.at/archeaccessrestrictions/public'
            },
            'title': {'cs': 'otevřený přístup', 'en': 'open access'}
        }],
        'control_number': '411100',
        'creator': [{'name': 'Daniel Kopecký'}],
        'dateIssued': '2010-07-01',
        "keywords": [
            {"cs": "1", "en": "1"},
            {"cs": "2", "en": "2"},
            {"cs": "3", "en": "3"},
        ],
        'language': [{
            'is_ancestor': False,
            'links': {
                'self': 'http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/cze'
            },
            'title': {'cs': 'čeština', 'en': 'Czech'}
        }],
        'provider': [{
            'address': 'Malostranské náměstí 259/12, 118 00 Praha 1',
            'aliases': ['AMU'],
            'ico': '61384984',
            'is_ancestor': False,
            'links': {
                'self': 'http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/61384984'
            },
            'provider': True,
            'related': {'rid': '51000'},
            'title': {
                'cs': 'Akademie múzických umění v Praze',
                'en': 'Academy of Performing Arts in Prague'
            },
            'type': 'veřejná VŠ',
            'url': 'https://www.amu.cz'
        }],
        'entities': [{
            'address': 'Malostranské náměstí 259/12, 118 00 Praha 1',
            'aliases': ['AMU'],
            'ico': '61384984',
            'is_ancestor': False,
            'links': {
                'self': 'http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/61384984'
            },
            'provider': True,
            'related': {'rid': '51000'},
            'title': {
                'cs': 'Akademie múzických umění v Praze',
                'en': 'Academy of Performing Arts in Prague'
            },
            'type': 'veřejná VŠ',
            'url': 'https://www.amu.cz'
        }],
        'resourceType': [{
            'is_ancestor': False,
            'links': {
                'self': 'http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/bakalarske-prace'
            },
            'title': {
                'cs': 'Bakalářské práce',
                'en': 'Bachelor’s theses'
            }
        }],
        'title': [{'cs': 'Testovací záznam', 'en': 'Test record'}]
    }


@pytest.fixture()
def base_nresult():
    return {
        "N_certifyingAuthority": [{
            "links": {
                "self": "http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/mdcr"
            }
        }],
        "N_dateCertified": "2020-03-19",
        "N_economicalParameters": "Výsledky diagnostiky staveb jsou podkladem pro návrh vhodného "
                                  "způsobu opatření či zásahu (údržba/ oprava/ rekonstrukce). "
                                  "Pokud jsou tyto podklady v dostatečném rozsahu a kvalitě vede "
                                  "to k optimalizaci nákladů a zvyšování životnosti staveb. K "
                                  "tomuto účelu může nemalou měrou přispět uplatnění kombinace "
                                  "nedestruktivních diagnostických metod jako je rázové zařízení "
                                  "FWD a georadar. V kap. 2.5 jsou uvedeny konkrétní příklady "
                                  "kombinace rázového zařízení FWD a georadaru při diagnostickém "
                                  "průzkumu vozovky s demonstrováním přínosu jejich použití.",
        "N_technicalParameters": "Metodika uvádí jak postupovat při použití kombinace dvou "
                                 "nedestruktivních diagnostických zařízení – rázového zařízení "
                                 "FWD (pro hodnocení únosnosti vozovek) a georadaru (pro "
                                 "zjišťování tlouštěk konstrukčních vrstev, k identifikaci "
                                 "nehomogenit, skrytých vad a poruch) při diagnostickém průzkumu "
                                 "vozovek pozemních komunikací. Upozorňuje na přínosy, "
                                 "které plynou ze zpracování dat naměřených oběma zařízeními a "
                                 "jejich využití při tvorbě homogenních sekcí, které slouží jako "
                                 "podklad pro plánování údržby, oprav a rekonstrukcí vozovek. "
                                 "Cílem metodiky je uvést: - zásady pro uplatnění kombinace "
                                 "rázového zařízení FWD a georadaru, - postup při použití "
                                 "kombinace těchto dvou nedestruktivních diagnostických metod, "
                                 "- upřesnění postupu při tvorbě homogenních sekcí, - konkrétní "
                                 "příklady, při kterých je kombinace těchto zařízení využívána.",
        "N_internalID": "N-2020-FWD-GPR",
        "N_referenceNumber": "1/2020-710-VV/1",
        "N_resultUsage": [{
            "links": {
                "self": "http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/c"
            }
        }],
        "N_type": [{
            "links": {
                "self": "http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/a"
            }
        }]
    }


@pytest.fixture()
def base_nresult_dereferenced():
    return {
        'N_certifyingAuthority': [{
            'is_ancestor': False,
            'links': {
                'self':
                    'http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/mdcr'
            },
            'title': {
                'cs': 'Ministerstvo dopravy',
                'en': 'Ministry of transport'
            }
        }],
        'N_dateCertified': "2020-03-19",
        'N_economicalParameters': 'Výsledky diagnostiky staveb jsou podkladem pro '
                                  'návrh vhodného způsobu opatření či zásahu (údržba/ '
                                  'oprava/ rekonstrukce). Pokud jsou tyto podklady v '
                                  'dostatečném rozsahu a kvalitě vede to k '
                                  'optimalizaci nákladů a zvyšování životnosti '
                                  'staveb. K tomuto účelu může nemalou měrou přispět '
                                  'uplatnění kombinace nedestruktivních '
                                  'diagnostických metod jako je rázové zařízení FWD a '
                                  'georadar. V kap. 2.5 jsou uvedeny konkrétní '
                                  'příklady kombinace rázového zařízení FWD a '
                                  'georadaru při diagnostickém průzkumu vozovky s '
                                  'demonstrováním přínosu jejich použití.',
        'N_internalID': 'N-2020-FWD-GPR',
        'N_referenceNumber': '1/2020-710-VV/1',
        'N_resultUsage': [{
            'is_ancestor': False,
            'links': {
                'self': 'http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/c'
            },
            'title': {
                'cs': 'Výsledek je užíván bez omezení okruhu '
                      'uživatelů'
            }
        }],
        'N_technicalParameters': 'Metodika uvádí jak postupovat při použití kombinace '
                                 'dvou nedestruktivních diagnostických zařízení – '
                                 'rázového zařízení FWD (pro hodnocení únosnosti '
                                 'vozovek) a georadaru (pro zjišťování tlouštěk '
                                 'konstrukčních vrstev, k identifikaci nehomogenit, '
                                 'skrytých vad a poruch) při diagnostickém průzkumu '
                                 'vozovek pozemních komunikací. Upozorňuje na '
                                 'přínosy, které plynou ze zpracování dat naměřených '
                                 'oběma zařízeními a jejich využití při tvorbě '
                                 'homogenních sekcí, které slouží jako podklad pro '
                                 'plánování údržby, oprav a rekonstrukcí vozovek. '
                                 'Cílem metodiky je uvést: - zásady pro uplatnění '
                                 'kombinace rázového zařízení FWD a georadaru, - '
                                 'postup při použití kombinace těchto dvou '
                                 'nedestruktivních diagnostických metod, - upřesnění '
                                 'postupu při tvorbě homogenních sekcí, - konkrétní '
                                 'příklady, při kterých je kombinace těchto zařízení '
                                 'využívána.',
        'N_type': [{
            'is_ancestor': False,
            'links': {'self': 'http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/a'},
            'title': {'cs': 'certifikovaná metodika (NmetC)'}
        }]
    }


@pytest.fixture()
def base_event():
    return {
        "nameOriginal":
            "Česká konference 2020",
        "nameAlternate": [
            "Konference Česka 2020", "Conference of Czechia 2020"
        ],
        "nameUnified": [{
            "links": {
                "self": "http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/cze-conference"
            }
        }],
        "date": "2019-12-23/2019-12-24",
        "location": {
            "place": "Prague",
            "country": [{
                "links": {
                    "self": "http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/cz"
                }
            }]
        }
    }


@pytest.fixture()
def base_theses():
    return {
        "dateDefended": "2010-07-01",
        "defended": True,
        "degreeGrantor": [{
            "links": {
                "self": "http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/61384984"
            }
        }],
        "studyField": [
            {
                "is_ancestor": False,
                "links": {
                    "self": "http://127.0.0.1:5000/2.0/taxonomies/test_taxonomy/o-herectvi"
                            "-alternativniho-divadla"
                }
            }
        ]
    }


@pytest.fixture()
def nresult_data(base_json, base_nresult):
    return {**base_json, **base_nresult}


@pytest.fixture()
def theses_data(base_json, base_theses):
    return {**base_json, **base_theses}


@pytest.fixture()
def events_data(base_json, base_event):
    base_json["events"] = [base_event]
    return base_json
