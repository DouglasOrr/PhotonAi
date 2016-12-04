import pymssql


class Session:
    def __init__(self, server, user, password, database):
        self._connection = pymssql.connect(
            server=server, user=user, password=password, database=database,
            tds_version='7.0')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

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

    def sample_bots(self, n):
        with self._connection.cursor() as cursor:
            cursor.execute('''
            SELECT id, name, upload_version, script
            FROM bots
            WHERE id IN (
                SELECT TOP %d MAX(bots.id)
                FROM bots
                WHERE bots.disabled = 0
                GROUP BY bots.name
                ORDER BY NEWID()
            )
            ''', (n,))
            return [dict(id=id,
                         name=name,
                         version=upload_version,
                         script=script)
                    for id, name, upload_version, script in cursor]

    def add_game(self, bot_a, bot_b, winner, map, seed):
        with self._connection.cursor() as cursor:
            cursor.execute('''
            INSERT INTO games (bot_a, bot_b, winner, played, map, seed)
            VALUES (%d, %d, %s, GETDATE(), %s, %d)
            ''',
                           (bot_a, bot_b, winner, map, seed))
            cursor.execute('SELECT SCOPE_IDENTITY()')
            id = next(iter(cursor))[0]
        self._connection.commit()
        return id

    def close(self):
        self._connection.close()
