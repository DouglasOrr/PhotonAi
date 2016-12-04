import pymssql


class Session:
    def __init__(self, server, user, password, database):
        self._connection = pymssql.connect(
            server=server, user=user, password=password, database=database,
            tds_version='7.0')

    def upload(self, name, script):
        with self._connection.cursor() as cursor:
            cursor.execute('''
            INSERT INTO bots (name, script, uploaded, upload_version)
            VALUES (%s, %s, GETDATE(),
            1 + (SELECT ISNULL(MAX(upload_version), 0) FROM bots WHERE name=%s)
            )
            ''',
                           (name, script, name))
        self._connection.commit()
