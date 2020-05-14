import pymongo
from mongodb_migrations.base import BaseMigration
from pymongo import IndexModel


class Migration(BaseMigration):
    def upgrade(self):
        self.db.create_collection('itilizate')
        self.db.itilizate.create_indexes([IndexModel(
            [
                ('uid', pymongo.ASCENDING),
            ], unique=True)])

    def downgrade(self):
        self.db['itilizate'].drop()
