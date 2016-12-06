'''SQL server database interface.
'''

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

    def leaderboard(self, ngames):
        with self._connection.cursor() as cursor:
            # 1. Find all the valid bots
            cursor.execute('''
            SELECT bots.id, bots.name, bots.upload_version,
                   bots.disqualified, bots.disabled
            FROM bots
            WHERE bots.id IN (
                SELECT MAX(bots.id) FROM bots GROUP BY bots.name
            )
            ''')
            bots = {id: dict(name=name,
                             version=upload_version,
                             disqualified=disqualified,
                             disabled=disabled,
                             played=0,
                             won=0,
                             drawn=0)
                    for id, name, upload_version, disqualified, disabled
                    in cursor}

            # 2. Count the number of wins over the last 'ngames' games.
            #
            # Inefficient here... should do the aggregation inside SQL,
            # but that's tricky!
            cursor.execute('''
            SELECT bot_a, bot_b, winner
            FROM games
            ORDER BY id DESC
            ''')
            for a, b, winner in cursor:
                if a in bots and bots[a]['played'] < ngames:
                    bots[a]['played'] += 1
                    bots[a]['won'] += (winner == a)
                    bots[a]['drawn'] += winner is None
                if b in bots and bots[b]['played'] < ngames:
                    bots[b]['played'] += 1
                    bots[b]['won'] += (winner == b)
                    bots[b]['drawn'] += winner is None

            # 3. Sort by descending number-of-wins
            return sorted(
                (dict(id=id, **v) for id, v in bots.items()),
                key=lambda x: (x['disqualified'], -x['won']))

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

    def history(self, n):
        with self._connection.cursor() as cursor:
            cursor.execute('''
            SELECT TOP(%d) g.id, g.map, a.name, b.name, w.name
            FROM games g
            INNER JOIN bots a ON a.id = g.bot_a
            INNER JOIN bots b ON b.id = g.bot_b
            LEFT JOIN bots w ON w.id = g.winner
            ORDER BY g.id DESC
            ''', (n,))
            return [dict(id=id,
                         map=map,
                         a=a, b=b,
                         winner=winner)
                    for id, map, a, b, winner in cursor]

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
