import os

class Config:
    SSL_REDIRECT = False
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mynameishardtoguess'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_USE_TLS = True
    MAIL_PORT = 587
    MAIL_SERVER = 'smtp.gmail.com'
    MAX_CONTENT_LENGTH = 1024 * 5120
    UPLOAD_PATH = 'static/uploads'
    UIMAGE_ADMIN = 'oyewaleadedunmola@gmail.com'
    UIMAGE_MAIL_SENDER = 'oyewaleadedunmola@gmail.com'
    UIMAGE_MAIL_HEADER = '[Uimage]'
    USERS_PER_PAGE = 15
    UIMAGE_POSTS_PER_PAGE = 10 
    UIMAGE_COMMENTS_PER_PAGE = 10
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UIMAGE_SLOW_DB_QUERY_TIME = 0.5
    SQLALCHEMY_RECORD_QUERIES = True

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    PROFILE = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
         'sqlite:///' + os.path.join(os.path.dirname(__file__), 'dev.sqlite')


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
         'sqlite://'


class ProductionConfig(Config):
    DEBUG = True
    uri = os.environ.get('DATABASE_URL')
    SQLALCHEMY_DATABASE_URI = uri.replace('postgres://', 'postgresql://') or \
         'sqlite:///' + os.path.join(os.path.dirname(__file__), 'prod-dev.sqlite')

    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        #email errors to the admin
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_TLS', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.UIMAGE_MAIL_SENDER,
            toaddrs=cls.UIMAGE_ADMIN,
            subject=cls.UIMAGE_MAIL_HEADER + 'Application Error',
            secure=secure, 
            credentials=credentials)

        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)


class HerokuConfig(ProductionConfig):
    SSL_REDIRECT = True if os.environ.get('DYNO') else False
    @classmethod
    def init_app(cls, app):
        ProductionConfig.init_app(app)

        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app)

config = {
    'default': DevelopmentConfig,
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig
}