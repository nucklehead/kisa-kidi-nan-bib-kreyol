import pymongo
from mongodb_migrations.base import BaseMigration
from pymongo import IndexModel


class Migration(BaseMigration):
    def upgrade(self):
        self.db.odyo_bib_kreyol.drop_index('liv_1_chapit_1_vese_1')
        self.db.odyo_bib_kreyol.create_indexes([IndexModel(
            [
                ('liv', pymongo.ASCENDING),
                ('chapit', pymongo.ASCENDING),
                ('vese', pymongo.ASCENDING),
                ('idantifikasyon', pymongo.ASCENDING),
            ], unique=True)])

    def downgrade(self):
        self.db.odyo_bib_kreyol.drop_indexes('liv_1_chapit_1_vese_1_idantifikasyon_1')
        self.db.odyo_bib_kreyol.create_indexes([IndexModel(
            [
                ('liv', pymongo.ASCENDING),
                ('chapit', pymongo.ASCENDING),
                ('vese', pymongo.ASCENDING),
            ], unique=True)])