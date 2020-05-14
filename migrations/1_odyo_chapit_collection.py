import pymongo
from mongodb_migrations.base import BaseMigration
from pymongo import IndexModel


class Migration(BaseMigration):
    def upgrade(self):
        self.db.create_collection('odyo_bib_kreyol')
        self.db.odyo_bib_kreyol.create_indexes([IndexModel(
            [
                ('liv', pymongo.ASCENDING),
                ('chapit', pymongo.ASCENDING),
                ('vese', pymongo.ASCENDING)
            ], unique=True)])

    def downgrade(self):
        self.db['odyo_bib_kreyol'].drop()
