from . import config


class NRAll:
    def __init__(self, app=None, db=None):
        self.init_app(app, db)

    def init_app(self, app, db):
        self.init_config(app, db)

    def init_config(self, app, db):
        app.config.setdefault('RECORDS_REST_ENDPOINTS', {}).update(
            config.RECORDS_REST_ENDPOINTS
        )
        # TODO: dodělat facety a filtry pro souhrný index
        # app.config.setdefault('RECORDS_REST_FACETS', {}).update(
        #     config.RECORDS_REST_FACETS
        # )
