#!/usr/bin/env python

import argparse
from pathlib import Path
import csv
import uuid
import json

ENTRY_TYPE_CONVERTER = {
    'Password': 1,
    'General': 2,
    'Credit Card': 3,
}

def build_bitwarden_item(type, name=None, notes=None):
    return {
        'id': str(uuid.uuid4()),    # not sure that Bitwarden will actually use the uuid you give it
        'organizationId': None,
        'folderId': None,
        'type': type,
        'name': name,
        'notes': notes,
        'favorite': False,
        'collectionIds': None,
    }

def add_login(bitwarden_item, username=None, password=None, totp=None, uris=None):
    bitwarden_item['login'] = {
        'username': username,
        'password': password,
        'totp': totp,
    }
    if uris and len(uris) > 0:
        bitwarden_item['login']['uris'] = uris

def add_secure_note(bitwarden_item, text=None):
    meta_notes = list(filter(lambda x: x is not None, [text, bitwarden_item['notes']]))
    bitwarden_item['notes'] = '\n\n---\n\n'.join(meta_notes)
    bitwarden_item['secureNote'] = { 'type': 0 }

def add_card(bitwarden_item, cardholder_name=None, brand=None, number=None, exp_month=None, exp_year=None, code=None):
    bitwarden_item['card'] = {
        'cardholderName': cardholder_name,
        'brand': brand,    # I doubt this will work in every case, but 'Mastercard' did
        'number': number,
        'expMonth': exp_month,
        'expYear': exp_year,
        'code': code,
    }

def add_identity(bitwarden_item, title=None, first_name=None, middle_name=None, last_name=None, address1=None,
        address2=None, address3=None, city=None, state=None, postal_code=None, country=None, company=None, email=None,
        phone=None, ssn=None, username=None, passport_number=None, license_number=None):
    bitwarden_item['identity'] = {
        "title": title,
        "firstName": first_name,
        "middleName": middle_name,
        "lastName": last_name,
        "address1": address1,
        "address2": address2,
        "address3": address3,
        "city": city,
        "state": state,
        "postalCode": postal_code,
        "country": country,
        "company": company,
        "email": email,
        "phone": phone,
        "ssn": ssn,
        "username": username,
        "passportNumber": passport_number,
        "licenseNumber": license_number,
    }

parser = argparse.ArgumentParser()
parser.add_argument('file', help='location of the Encryptr CSV export file')
args = parser.parse_args()

path = Path(args.file)

if not path.is_file():
    raise ValueError(f'\'{args.file}\' is not a file')

# parse csv
with path.open('r') as export:
    reader = csv.reader(export, delimiter=',', quotechar='"')
    next(reader)    # skip header
    data = list(reader)

# fix formatting
for i, row in enumerate(data):
    for j, cell in enumerate(row):
        data[i][j] = cell.replace('\\n', '\n')    # de-escape linebreaks one level

        if cell == "":    # convert empty to null
            data[i][j] = None

# convert to Bitwarden
bitwarden_import = { 'items': [] }

for entry_type, label, username, password, site_url, notes, text, card_type, name_on_card, card_number, cvv, expiry in data:
    bitwarden_item = build_bitwarden_item(ENTRY_TYPE_CONVERTER[entry_type], name=label, notes=notes)

    if entry_type == 'Password':
        add_login(bitwarden_item, username=username, password=password, totp=None)
    elif entry_type == 'General':
        add_secure_note(bitwarden_item, text=text)
    elif entry_type == 'Credit Card':
        exp_month = expiry.split('/')[0].lstrip('0')
        exp_year = '20' + expiry.split('/')[1]
        add_card(bitwarden_item, cardholder_name=name_on_card, brand=card_type, number=card_number,
            exp_month=exp_month, exp_year=exp_year, code=cvv)

    bitwarden_import['items'].append(bitwarden_item)

# write to disk
with Path('bitwarden.json').open('w') as f:
    json.dump(bitwarden_import, f, indent=2)
