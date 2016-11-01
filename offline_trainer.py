import os
import sys
import time

from sklearn import cluster
import numpy as np
from psycopg2.pool import ThreadedConnectionPool


def get_centroids(X):
# TODO another method could be used, as this does not ensure the amount of clusters
# TODO Birch for example (but then you would get more centroids
    ms = cluster.MeanShift(bandwidth=4)
    ms.fit(X)
    labels, counts = np.unique(ms.labels_, return_counts=True)
    fraud = labels[np.argmin(counts)]
    return zip(*ms.cluster_centers_.T.tolist(), [bool(l == fraud) for l in labels])


def get_data(conn, n=3000):
    query = """
    WITH win AS (
    SELECT
      x,
      y,
      ROW_NUMBER() OVER (ORDER BY ts desc) n
    FROM
      accelerator.live_data
    )
    SELECT
      x,
      y
    FROM
      win
    WHERE n < (%s)
    """
    c = conn.cursor()
    c.execute(query, (n,))
    data = c.fetchall()
    c.close()
    return data


def write_centroids_to_db(conn, n=3000):
    data = get_data(conn, n=3000)
    centroids = get_centroids(data)
    query = """DELETE FROM accelerator.model"""
    c = conn.cursor()
    c.execute(query)
    query = """INSERT INTO accelerator.model VALUES (%s, %s, %s)"""
    c.executemany(query, centroids)
    c.close()


def main(n=3000):
    dsn = os.environ['POSTGRES_DSN']
    pool = ThreadedConnectionPool(1, 2, dsn=dsn)
    conn = pool.getconn()
    conn.autocommit = True
    write_centroids_to_db(conn, n)
    pool.putconn(conn)


if __name__ == "__main__":
    if len(sys.argv[1]) > 1:
# TODO build in some safety here
        n = sys.argv[1]
    else:
        n = 3000
    main(n)

