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

with open('spider.bible_id.json', 'r') as bib:
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
        vese = OrderedDict(sorted(vese.items(), key=lambda item: int(item[0].split('-')[0])))
        return {f'Vese {vese}' if 'antèt' in vese else 'Tit': teks for vese, teks in vese.items()}


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
        wavves = list(MONGO_DB.db.odyo_bib_kreyol.find(
            {'liv': liv, 'chapit': chapit, 'idantifikasyon': idantifikasyon}
        ))
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
    'uid': fields.String,
})


@api.route('/api/antre')
class Antre(Resource):
    @api.doc(body=enfo_itilizate)
    def post(self):
        assert request.json['uid'] == os.environ.get("ADMIN_UID", default='')
        return {'token': request.json['uid']}


if __name__ == '__main__':
    port = int(os.environ.get("PORT", default=8080))
    app.run(host='0.0.0.0', port=port)
