#!/bin/bash

# update localisation

find ./tri_photo_date -name '*.py' -exec xgettext -o messages.pot {} +

msgmerge --update tri_photo_date/locales/fr/LC_MESSAGES/base.po messages.pot
msgmerge --update tri_photo_date/locales/en/LC_MESSAGES/base.po messages.pot

cd tri_photo_date/locales/fr/LC_MESSAGES/
msgfmt base.po base.mo

cd tri_photo_date/locales/en/LC_MESSAGES/
vim base.po
msgfmt base.po base.mo
