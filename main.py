import json
import logging
import os
from collections import OrderedDict
from flask import Flask, redirect, request
from flask_restplus import Resource, Api, fields
from flask_cors import CORS
from pymongo import ReplaceOne
from db.config import configure_mongo, MONGO_DB

app = Flask(__name__)
api = Api(app)
cors = CORS(app, resources={r'/api/*': {'origins': 'http://kod-kreyol.ue.r.appspot.com'}})

configure_mongo(app)

logger = logging.getLogger('werkzeug')

with open('1957-bible.json', 'r') as bib:
    bib_json = json.load(bib)[0]

with open('1957-fullaudio-bible-full-name.json', 'r') as bib:
    bib_mp3_json = json.load(bib)[0]


@api.route('/api/liv')
class Liv(Resource):
    def get(self):
        return list(bib_json.keys())


@api.route('/api/<liv>/chapit')
@api.doc(params={'liv': 'Non liv la'})
class Chapit(Resource):
    def get(self, liv):
        return list(bib_json.get(liv, {}).keys())


@api.route('/api/<liv>/<chapit>/vese')
@api.doc(params={'liv': 'Non liv la', 'chapit': 'Nimewo chapit la'})
class Vese(Resource):
    def get(self, liv, chapit):
        vese = bib_json.get(liv, {}).get(chapit, {})
        vese['0'] = f'{liv} chapit {int(chapit)}.'
        vese = OrderedDict(sorted(vese.items(), key=lambda item: float(item[0])))
        nimewo_tit = iter(range(len(vese)))
        return {
            f'Tit {next(nimewo_tit) + 1}' if '.5' in vese
            else 'Chapit' if vese == '0'
            else f'Vese {vese}': teks for vese, teks in vese.items()}


@api.route('/api/<liv>/<chapit>/odyo.mp3')
@api.doc(params={'liv': 'Non liv la', 'chapit': 'Nimewo chapit la'})
class Odyo(Resource):
    def get(self, liv, chapit):
        return redirect(bib_mp3_json.get(liv, {}).get(chapit, {}).get('mp3', ''))


wave_fields = api.model('Wave', {
    'userId': fields.String,
    'startTime': fields.Float,
    'endTime': fields.Float,
    'marked': fields.Boolean,
    'accepted': fields.Boolean,
    'rejected': fields.Boolean,
})

wave_list_fields = api.model('WaveList', {
    'waves': fields.List(fields.Nested(wave_fields))
})


@api.route('/api/<liv>/<chapit>/<idantifikasyon>/anrejistre')
@api.doc(params={'liv': 'Non liv la', 'chapit': 'Nimewo chapit la', 'uid': 'Idantifikasyon itilizate a'})
class Anrejistre(Resource):
    @api.marshal_with(wave_fields)
    def get(self, liv, chapit, idantifikasyon):
        query = {'liv': liv, 'chapit': chapit, 'idantifikasyon': idantifikasyon}
        wavves = list(MONGO_DB.db.odyo_bib_kreyol.find(query))
        return [wave['wave'] for wave in wavves]

    @api.doc(body=wave_list_fields)
    def post(self, liv, chapit, idantifikasyon):
        waves = request.json['waves']
        logger.info(liv)
        logger.info(chapit)
        logger.info(waves)
        vese_yo = [
            ReplaceOne(
                {'liv': liv, 'chapit': chapit, 'vese': index, 'idantifikasyon': idantifikasyon},
                {'liv': liv, 'chapit': chapit, 'vese': index, 'idantifikasyon': idantifikasyon, 'wave': wave},
                upsert=True
            ) for index, wave in enumerate(waves)
        ]
        MONGO_DB.db.odyo_bib_kreyol.bulk_write(vese_yo, ordered=False)


enfo_itilizate = api.model('Kont', {
  "uid": fields.String,
  "name": fields.String,
  "granted_scopes": fields.String,
  "id": fields.String,
  "verified_email": fields.Boolean,
  "given_name": fields.String,
  "locale": fields.String,
  "family_name": fields.String,
  "email": fields.String,
  "picture": fields.String,
})


@api.route('/api/antre')
class Antre(Resource):
    @api.doc(body=enfo_itilizate)
    def post(self):
        enfo = request.json
        enfo['admin'] = request.json['uid'] == os.environ.get("ADMIN_UID", default='')
        MONGO_DB.db.itilizate.update_one({'uid': enfo['uid']}, {'$set': enfo}, upsert=True)
        result = MONGO_DB.db.itilizate.find_one({'uid': enfo['uid']})

        return {
            'token': request.json['uid'],
            'admin': enfo['admin'],
            'latestFeature': result.get('latestFeature', 0)
        }


@api.route('/api/itilizate/<adminUid>')
@api.doc(params={'adminUid': 'Idantifikasyon pou administrate a'})
class Itilizate(Resource):
    @api.marshal_with(enfo_itilizate)
    def get(self, adminUid):
        if adminUid != os.environ.get("ADMIN_UID", default=''):
            return []
        return list(MONGO_DB.db.itilizate.find())


dat_fonksyon = api.model('Dat', {
  "date": fields.Integer,
})


@api.route('/api/kont/<token>')
@api.doc(params={'token': 'Idantifikasyon pou itilizate a'})
class Kont(Resource):
    @api.doc(body=dat_fonksyon)
    def post(self, token):
        dat = request.json
        MONGO_DB.db.itilizate.update_one({'uid': token}, {'$set': {'latestFeature': dat['date']}})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", default=8080))
    app.run(host='0.0.0.0', port=port)

