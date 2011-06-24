from gluon.storage import Storage
settings = Storage()

settings.migrate = True
settings.title = T( 'Temporary storage' )
settings.subtitle = 'powered by web2py'
settings.author = 'Szimszon'
settings.author_email = 'szimszon@oregpreshaz.eu'
settings.keywords = 'f\xc3\xa1jl,felt\xc3\xb6lt\xc3\xa9s,upload,file'
settings.description = ''
settings.layout_theme = 'Whitelight'
#settings.database_uri = 'postgres://username:pw@dbhost/dbname'
settings.database_uri = 'sqlite://storage.sqlite'
settings.security_key = 'sha512:6f98a5d1-4f39-4ff4-3a6b-e09d79f9fa3d'
settings.email_server = 'localhost'
settings.email_sender = 'noreply@localhost'
settings.email_login = ''
settings.login_method = 'local'
settings.login_config = ''
settings.plugins = []
settings.default_max_number_of_uploadable_files = 1
settings.default_valid_download_days = 7
settings.default_valid_upload_days = 7
settings.verzion_number='110624'
