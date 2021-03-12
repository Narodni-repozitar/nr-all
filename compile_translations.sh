#!/bin/bash

pybabel extract -o nr_all/translations/messages.pot nr_all
pybabel update -d nr_all/translations -i nr_all/translations/messages.pot -l cs
pybabel update -d nr_all/translations -i nr_all/translations/messages.pot -l en
pybabel compile -d nr_all/translations