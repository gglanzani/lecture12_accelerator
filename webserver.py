import os
from datetime import datetime

from flask import Flask
from flask_restful import Api, Resource, reqparse
from werkzeug.contrib.cache import SimpleCache
import psycopg2
from psycopg2.pool import ThreadedConnectionPool

app = Flask(__name__)
api = Api(app)

# dsn = os.environ['POSTGRES_DSN']
dsn = 'host=127.0.0.1 dbname=postgres user=accelerator'
pool = ThreadedConnectionPool(1, 5, dsn=dsn)

parser = reqparse.RequestParser()
parser.add_argument('x')
parser.add_argument('y')

cache = SimpleCache(default_timeout=600)


def distance(p0, p1):
    """This is actually the distance squared"""
    x0, y0 = p0
    x1, y1 = p1
    return (x0 - x1) ** 2 + (y0 - y1) ** 2


def load_model():
    model = cache.get('model')
    if model is None:
        connection = pool.getconn()
        c = connection.cursor()
        c.execute("""
        SELECT x, y, fraud 
        FROM accelerator.model
        ORDER BY fraud
        """)
        centroids = c.fetchall()
        (x_n, y_n, _), (x_f, y_f, __) = centroids
        model = {'normal': (x_n, y_n), 'fraud': (x_f, y_f)}
        cache.set('model', model)
    return model


class Classify(Resource):
    def post(self):
        args = parser.parse_args()
        point = (float(args['x']), float(args['y']))
        is_fraud = self.is_fraud(point)
        self.write_to_db(point)
        return {"is_fraud": is_fraud}

    def is_fraud(self, point):
        model = load_model()
        if distance(point, model['normal']) > distance(point, model['fraud']):
            return True

    def write_to_db(self, point):
# TODO perfect candidate to make it happen async
        c = self.get_cursor()
        c.execute("""INSERT INTO accelerator.live_data VALUES (%s, %s, %s)""", 
                  (point[0], point[1], datetime.now()))
        c.close()
        self.close_connection()

    def get_cursor(self):
# TODO the following two could be added to the Classify resource (add_resource)
        connection = pool.getconn()
        connection.autocommit = True
        self.connection = connection
        c = connection.cursor()
        return c

    def close_connection(self):
        if self.connection:
            pool.putconn(self.connection)


api.add_resource(Classify, '/classify/')

if __name__ == '__main__':
    app.run(debug=True, port=5005)
