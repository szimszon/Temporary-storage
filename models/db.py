# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
#########################################################################

if request.env.web2py_runtime_gae:            # if running on Google App Engine
    db = DAL( 'google:datastore' )              # connect to Google BigTable
                                              # optional DAL('gae://namespace')
    session.connect( request, response, db = db ) # and store sessions and tickets there
    ### or use the following lines to store sessions in Memcache
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db = MEMDB(Client()))
else:                                         # else use a normal relational database
    db = DAL( settings.database_uri )       # if not, use SQLite or other DB
## if no need for session
# session.forget()

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import *
mail = Mail()                                  # mailer
auth = Auth( globals(), db )                      # authentication/authorization
crud = Crud( globals(), db )                      # for CRUD helpers using auth
service = Service( globals() )                   # for json, xml, jsonrpc, xmlrpc, amfrpc
plugins = PluginManager()

mail.settings.server = 'logging' or 'smtp.gmail.com:587'  # your SMTP server
mail.settings.sender = 'you@gmail.com'         # your email
#mail.settings.login = 'username:password'      # your credentials or None

auth.settings.hmac_key = settings.security_key   # before define_tables()

########################################
db.define_table( 'auth_user',
    Field( 'id', 'id',
          represent = lambda id:SPAN( id, ' ', A( 'view', _href = URL( 'auth_user_read', args = id ) ) ) ),
    Field( 'username', type = 'string',
          label = T( 'Username' ) ),
    Field( 'first_name', type = 'string',
          label = T( 'First Name' ) ),
    Field( 'last_name', type = 'string',
          label = T( 'Last Name' ) ),
    Field( 'email', type = 'string',
          label = T( 'Email' ) ),
    Field( 'password', type = 'password',
          readable = False,
          label = T( 'Password' ) ),
    Field( 'created_on', 'datetime', default = request.now,
          label = T( 'Created On' ), writable = False, readable = False ),
    Field( 'modified_on', 'datetime', default = request.now,
          label = T( 'Modified On' ), writable = False, readable = False,
          update = request.now ),
    Field( 'registration_key', default = '',
          writable = False, readable = False ),
    Field( 'reset_password_key', default = '',
          writable = False, readable = False ),
    Field( 'registration_id', default = '',
          writable = False, readable = False ),
    format = '%(username)s',
    migrate = settings.migrate )


db.auth_user.first_name.requires = IS_NOT_EMPTY( error_message = auth.messages.is_empty )
db.auth_user.last_name.requires = IS_NOT_EMPTY( error_message = auth.messages.is_empty )
db.auth_user.password.requires = CRYPT( key = auth.settings.hmac_key )
db.auth_user.username.requires = IS_NOT_IN_DB( db, db.auth_user.username )
db.auth_user.registration_id.requires = IS_NOT_IN_DB( db, db.auth_user.registration_id )
db.auth_user.email.requires = ( IS_EMAIL( error_message = auth.messages.invalid_email ),
                               IS_NOT_IN_DB( db, db.auth_user.email ) )
auth.define_tables( migrate = settings.migrate )                           # creates all needed tables
auth.settings.mailer = mail                    # for user email verification
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.messages.verify_email = 'Click on the link http://' + request.env.http_host + URL( 'default', 'user', args = ['verify_email'] ) + '/%(key)s to verify your email'
auth.settings.reset_password_requires_verification = True
auth.messages.reset_password = 'Click on the link http://' + request.env.http_host + URL( 'default', 'user', args = ['reset_password'] ) + '/%(key)s to reset your password'


#########################################################################
## If you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, uncomment and customize following
# from gluon.contrib.login_methods.rpx_account import RPXAccount
# auth.settings.actions_disabled=['register','change_password','request_reset_password']
# auth.settings.login_form = RPXAccount(request, api_key='...',domain='...',
#    url = "http://localhost:8000/%s/default/user/login" % request.application)
## other login methods are in gluon/contrib/login_methods
#########################################################################

crud.settings.auth = auth                      # =auth to enforce authorization on crud

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

mail.settings.server = settings.email_server
mail.settings.sender = settings.email_sender
#mail.settings.login = settings.email_login

import uuid
import datetime

db.define_table( 'controlldata',
					Field( 'uuid',
							label = T( 'Upload identifier' ),
							length = 64,
							default = lambda:str( uuid.uuid4() ),
							writable = False, ),
					Field( 'dluuid',
							label = T( 'Download identifier' ),
							length = 64,
							default = lambda:str( uuid.uuid4() ),
							writable = False, ),
					Field( 'title', 'string',
							label = T( 'Description' ) ),
					Field( 'tonotify', 'string',
							label = T( 'Notify if file submitted' ),
							comment = T( 'comma separated list' )
							 ),
					Field( 'filenumber', 'integer',
							label = T( 'Max number of uploading files' ),
							default = settings.default_max_number_of_uploadable_files ),
					Field( 'uploadvaliddate', 'date',
							requires = IS_DATE( T( '%Y-%m-%d' ) ),
							default = ( request.now + datetime.timedelta( days = settings.default_valid_upload_days ) ).date(),
							label = T( 'Date until files can be uploaded' ) ),
					Field( 'downloadvaliddate', 'date',
							requires = IS_DATE( T( '%Y-%m-%d' ) ),
							default = ( request.now + datetime.timedelta( days = settings.default_valid_download_days ) ).date(),
							label = T( 'Date until files can be downloaded' ) ),
					auth.signature,
					format = '%(uuid)s',
					migrate = settings.migrate

 )
db.define_table( 'filestore',
					Field( 'controlldata_id', db.controlldata,
							label = T( 'Identifier' ),
							requires = IS_IN_DB( db, db.controlldata.id, '%(uuid)s' ),
							writable = False,
							readable = False ),
					Field( 'description', 'string',
							label = T( 'Description' ) ,
							requires = IS_NOT_EMPTY() ),
					Field( 'filename', 'string',
							label = T( 'Name of the file' ),
							writable = False ),
					Field( 'content', 'upload',
							uploadseparate = True,
							label = T( 'File' ),
							requires = IS_NOT_EMPTY(),
							autodelete = True ),
					Field( 'md5sum', 'string',
							label = T( 'MD5 Sum' ),
							represent = lambda md5sum: '[%s]' % md5sum,
							writable = False ),
					Field( 'created_by', db.auth_user,
							label = T( 'Created by' ),
							requires = IS_EMPTY_OR( IS_IN_DB( db, db.auth_user, '%(email)s' ) ),
							writable = False,
							),
					Field( 'created_ip', 'string',
							label = T( 'Creator\'s IP' ),
							default = request.env.remote_addr,
							writable = False ),
					Field( 'created_on', 'datetime',
							label = T( 'Created on' ),
							default = request.now,
							writable = False ),
					Field( 'modified_by', db.auth_user,
							label = T( 'Modified by' ),
							requires = IS_EMPTY_OR( IS_IN_DB( db, db.auth_user, '%(email)s' ) ),
							writable = False,
							),
					Field( 'modified_ip', 'string',
							label = T( 'Modifier\'s IP' ),
							default = request.env.remote_addr,
							update = request.env.remote_addr,
							writable = False ),
					Field( 'modified_on', 'datetime',
							label = T( 'Modified on' ),
							default = request.now,
							update = request.now,
							writable = False ),
							migrate = settings.migrate
					 )

db.define_table( 'downloaddata',
							Field( 'filestore_id', db.filestore,
									label = T( 'Identifier' ),
									requires = IS_IN_DB( db, db.filestore.id, '%(id)s' ),
									writable = False,
									readable = False,
									),
							Field( 'client_name', db.auth_user,
									label = T( 'Client name' ),
									requires = IS_EMPTY_OR( IS_IN_DB( db, db.auth_user, '%(email)s' ) ),
									writable = False,
									),
							Field( 'client_ip', 'string',
									label = T( 'Client IP' ),
									default = request.env.remote_addr,
									),
							Field( 'dl_timestamp', 'datetime',
									label = T( 'Timestamp' ),
									default = request.now
									),
							)

if db( db.auth_user.id > 0 ).count() > 0:
	#
	# ha van már felhasználó, letiltjuk a regisztrációt
	# ##################################################
	auth.settings.actions_disabled = ['register']
else:
	#
	# ha még nincs felhasználó akkor beállítjuk a jogokat azért
	# ##########################################################
	query = ( db.auth_group.role == 'admin' )
	if ( int( db( query ).count() ) == 0 ):
				gid = auth.add_group( 'admin', 'admin group' )
	else:
			gid = db( query ).select( db.auth_group.id ).first().id
	for group_id in [gid]:
		for tbl in ['controlldata']:
			for role in ['create', 'select']:
				pquery = ( ( db.auth_permission.group_id == group_id ) &
											( db.auth_permission.name == role ) &
											( db.auth_permission.table_name == tbl ) )
				if ( db( pquery ).count() == 0 ):
					auth.add_permission( group_id, role, tbl, 0 )
