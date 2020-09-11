import redis


class RedisStore:
    def __init__(self, app=None):
        if app:
            self.object = redis.Redis(
                host=app.config["REDIS_HOST"],
                port=app.config["REDIS_PORT"],
                db=0,
                decode_responses=True,
            )
        self.object = None

    def init_app(self, app):
        self.object = redis.Redis(
            host=app.config["REDIS_HOST"],
            port=app.config["REDIS_PORT"],
            db=0,
            decode_responses=True,
        )
