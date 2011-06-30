# -*- coding: utf-8 -*-
### required - do no delete
def user(): return dict( form = auth() )

#@auth.requires_login()
#def download(): return response.download( request, db )





def call():
    session.forget()
    return service()
### end requires




@auth.requires_login()
def index():
	'''
		Felhasználó által létrehozott ticketek listája
	'''
	import datetime
	filelists = db( auth.accessible_query( 'read', db.controlldata ) &
								( db.controlldata.is_active == True ) ).select( db.controlldata.ALL,
																															db.auth_user.ALL,
																															left = db.auth_user.on( db.controlldata.modified_by == db.auth_user.id ),
																															 orderby = db.controlldata.title )
	flist = []

	for f in filelists:
		if f.controlldata.uploadvaliddate >= request.now.date():
			#
			# még lehet feltölteni
			# ####################
			ul = A( '[%s]' % T( 'Link' ), _href = URL( f = 'upload', args = f.controlldata.uuid ),
								_title = T( 'Valid before and on %(date)s', dict( date = f.controlldata.uploadvaliddate ) ) )
			ue = A( '[%s]' % T( 'Email' ), _href = T( '''mailto:?Subject=%s upload link&Body=You could upload files at http://%s%s''' ,
																							 ( str( f.controlldata.title ),
																								request.env.http_host,
																								URL( f = 'upload', args = f.controlldata.uuid ) ) ),
								_title = T( 'Valid before and on %(date)s', dict( date = f.controlldata.uploadvaliddate ) ) )
		else:
			ul = XML( SPAN( XML( '[<s>%s</s>]' % T( 'Link' ) ), _title = T( 'Overdue at %(date)s', dict( date = f.controlldata.uploadvaliddate ) ) ) )
			ue = XML( SPAN( XML( '[<s>%s</s>]' % T( 'Email' ) ), _title = T( 'Overdue at %(date)s', dict( date = f.controlldata.uploadvaliddate ) ) ) )

		if f.controlldata.downloadvaliddate >= request.now.date():
			#
			# még le lehet tölteni
			# ####################
			dl = A( '[%s]' % T( 'Link' ), _href = URL( f = 'download', vars = dict( q = f.controlldata.dluuid ) ),
								_title = T( 'Valid before and on %(date)s', dict( date = f.controlldata.downloadvaliddate ) ) )
			de = A( '[%s]' % T( 'Email' ), _href = T( 'mailto:?Subject=%s download link&Body=http://%s%s' ,
																							 ( str( f.controlldata.title ),
																								 request.env.http_host,
																								 URL( f = 'download', vars = dict( q = f.controlldata.dluuid ) ) ) ),
								_title = T( 'Valid before and on %(date)s', dict( date = f.controlldata.downloadvaliddate ) ) )
		else:
			dl = XML( SPAN( XML( '[<s>%s</s>]' % T( 'Link' ) ), _title = T( 'Overdue at %(date)s', dict( date = f.controlldata.downloadvaliddate ) ) ) )
			de = XML( SPAN( XML( '[<s>%s</s>]' % T( 'Email' ) ), _title = T( 'Overdue at %(date)s', dict( date = f.controlldata.downloadvaliddate ) ) ) )
		piece = db( db.filestore.controlldata_id == f.controlldata.id ).count()
		ctitle = T( '%(title)s (%(piece)s/%(max)s files)', dict( title = f.controlldata.title,
																								piece = piece,
																								max = f.controlldata.filenumber ) )
		flist.append( TR( 
									TD( A( ctitle, _href = URL( f = 'add', args = f.controlldata.id ), _title = ctitle ), _class = 'description' ) ,
									TD( ul, ue , _class = 'link' ),
									TD( dl, de , _class = 'link' ),
									TD( SPAN( f.auth_user.email, _title = f.auth_user.email ) , BR(), f.controlldata.modified_on ), _class = 'modified' ) )
	if len( flist ) > 0:
		filelist = TABLE( THEAD( TR( 
													TH( db.controlldata.title.label, _class = 'description' ),
													TH( T( 'Upload' ), _class = 'link' ),
													TH( T( 'Download' ), _class = 'link' ),
													TH( T( db.controlldata.modified_by.label ) ,
														BR(),
														T( db.controlldata.modified_on.label ), _class = 'modified' ) ) ),
													 TBODY( *flist ), _class = 'customtable' )
	else:
		filelist = T( 'There is no active upload set.' )
	inactivefilelists = db( auth.accessible_query( 'read', db.controlldata ) &
								( db.controlldata.is_active == False ) ).select( db.controlldata.ALL,
																															db.auth_user.ALL,
																															left = db.auth_user.on( db.controlldata.modified_by == db.auth_user.id ),
																															orderby = db.controlldata.title )
	flist = []
	for f in inactivefilelists:
		flist.append( TR( 
									TD( A( f.controlldata.title, _href = URL( f = 'add', args = f.controlldata.id ), _title = f.controlldata.title ), _class = 'description' ) ,
									TD( SPAN( f.auth_user.email, _title = f.auth_user.email ), _class = 'modified' ),
									TD( f.controlldata.modified_on ), _class = 'modified' ) )
	if len( flist ) > 0:
		inactivefilelists = TABLE( THEAD( TR( 
													TH( db.controlldata.title.label ),
													TH( db.controlldata.modified_by.label, _class = 'modified' ),
													TH( db.controlldata.modified_on.label, _class = 'modified' ) ) ),
													 TBODY( *flist ), _class = 'customtable' )
	else:
		inactivefilelists = None
	return dict( filelist = filelist, inactivefilelists = inactivefilelists )

@auth.requires_login()
def add():
	'''
		Feltöltési ticket előállítása, és kezelése
	'''
	db.controlldata.tonotify.default = auth.user.email
	form = crud.update( db.controlldata,
										 request.args( 0 ),
										 onaccept = controllaccept,
										 ondelete = controlldelete )
	return dict( form = form )

@auth.requires_login()
def fstore():
	'''
		Feltöltött fájlok kezelése
	'''
	if not request.args( 0 ):
		#
		# az oldal nem parameterrel lett meghivva
		# ########################################
		raise HTTP( 400, T( "Wrong page call" ) )
	filelist = None
	q = ( ( db.filestore.id == request.args( 0 ) ) &
		( db.filestore.controlldata_id == db.controlldata.id ) &
		auth.accessible_query( 'update', db.controlldata ) )
	if db( q ).count() > 0:
		crud.settings.auth = None
		db.filestore.created_by.default = auth.user_id
		db.filestore.modified_by.default = auth.user_id
		db.filestore.modified_by.update = auth.user_id

		form = crud.update( db.filestore, request.args( 0 ),
											onvalidation = filestorevalidation,
											onaccept = fstoreaccept,
											next = 'fstore/[id]' )
		flist = []
		for row in db( db.downloaddata.filestore_id == request.args( 0 ) ).select( db.downloaddata.ALL,
																																						db.auth_user.ALL,
																																						left = db.auth_user.on( db.downloaddata.client_name == db.auth_user.id ),
																																						orderby = db.downloaddata.dl_timestamp ):
			flist.append( TR( 
										TD( row.downloaddata.dl_timestamp ),
										TD( row.auth_user.email ),
										TD( row.downloaddata.client_ip )
										)
			)
		if len( flist ) > 0:
			filelist = TABLE( THEAD( 
													TR( 
														TH( db.downloaddata.dl_timestamp.label ),
														TH( db.downloaddata.client_name.label ),
														TH( db.downloaddata.client_ip.label ),
														)
													),
												TBODY( *flist )
										)
	else:
		form = T( 'Not authorized record' )
	return dict( form = form, filelist = filelist )

@auth.requires_login()
def dl():
	'''
		Az eredeti download funkció
	'''
	try:
		db.downloaddata.client_name.default = auth.user_id
	except:
		#
		# ha nincs user_id, nem toltjuk ki
		# #################################
		pass
	fsid = db( db.filestore.content == request.args( 0 ) ).select( db.filestore.id ).first().id
	db.downloaddata.insert( filestore_id = fsid )

	return response.download( request, db )

def download():
	'''
		Bejelentkezés nélküli letöltési lehetőség ticket alapján
	'''
	if not request.vars.q:
		#
		# az oldal nem parameterrel lett meghivva
		# ########################################
		redirect( URL( f = 'dl', args = request.args ) )


	q = ( ( db.controlldata.dluuid == request.vars.q ) &
		( db.controlldata.is_active == True ) &
		( db.controlldata.downloadvaliddate >= request.now ) )


	if db( q ).count() == 0:
		#
		# nincs a parameternek megfelelo feltoltesi hely
		# ############################################### 
		raise HTTP( 400, T( "Wrong page call" ) )
	controlldata = db( q ).select( db.controlldata.id,
																db.controlldata.title ).first()
	controlldata_id = controlldata.id

	if request.args( 0 ):
		try:
			db.downloaddata.client_name.default = auth.user_id
		except:
			#
			# ha nincs user_id, nem toltjuk ki
			# #################################
			pass
		fsid = db( db.filestore.content == request.args( 0 ) ).select( db.filestore.id ).first().id
		db.downloaddata.insert( filestore_id = fsid )
		return response.download( request, db )

	filelist = T( 'There is no file for this identifier!' )

	flist = []
	for f in db( db.filestore.controlldata_id == controlldata_id ).select( db.filestore.ALL,
																																			db.auth_user.ALL,
																																			left = db.auth_user.on( db.filestore.modified_by == db.auth_user.id ),
																																			 orderby = ( db.filestore.description, db.filestore.filename ) ):
		if auth.user_id:
			fmodify = TD( A( IMG( _src = URL( c = 'static', f = 'toll.png' ), alt = T( 'Modify' ) ), _href = URL( f = 'fstore', args = f.filestore.id ) ), _title = T( 'Modify' ) )
		else:
			fmodify = TD()
		flist.append( TR( 
									TD( XML( '%s' % A( f.filestore.description, _href = URL( args = f.filestore.content,
																							vars = request.vars ), _title = f.filestore.description ) ), BR(),
											XML( '[%s]' % A( f.filestore.md5sum, _href = URL( args = f.filestore.content,
																							vars = request.vars ), _title = f.filestore.md5sum ) ), _class = 'description' ) ,
									TD( XML( '%s' % A( f.filestore.filename , _href = URL( args = f.filestore.content,
																							vars = request.vars ) , _title = f.filestore.filename ) ) ),
									TD( f.filestore.modified_ip , BR(), f.filestore.modified_on , _class = 'modified' ),
									fmodify
									)
								)
	if len( flist ) > 0:
		filelist = TABLE( 
									THEAD( 
											TR( 
												TH( '%s' % db.filestore.description.label, BR(),
																		db.filestore.md5sum.label, _class = 'description' ),
												TH( db.filestore.filename.label, _class = 'filename' ),
												TH( db.filestore.modified_ip.label, BR(), db.filestore.modified_on.label, _class = 'modified' ),
												TH()
												)
											),
									TBODY( 
											*flist
											)
									)


	return dict( filelist = filelist, controlldata_title = controlldata.title )

def upload():
	'''
		Bejelentkezés nélkül lehet feltölteni fájlokat egy ticket (uuid) alapján
	'''
	if not request.args( 0 ):
		#
		# az oldal nem parameterrel lett meghivva
		# ########################################
		raise HTTP( 400, T( "Wrong page call" ) )


	q = ( ( db.controlldata.uuid == request.args( 0 ) ) &
		( db.controlldata.is_active == True ) &
		( db.controlldata.uploadvaliddate >= request.now ) )


	if db( q ).count() == 0:
		#
		# nincs a parameternek megfelelo feltoltesi hely
		# ############################################### 
		raise HTTP( 400, T( "Wrong page call" ) )

	controlldata = db( q ).select( db.controlldata.id,
															db.controlldata.title ).first()
	controlldata_id = controlldata.id
	filelist = None
	try:
		maxfilecount = db( db.controlldata.uuid == request.args( 0 ) ).select( db.controlldata.filenumber ).first().filenumber
	except:
		maxfilecount = 0

	filecount = db( db.filestore.controlldata_id == controlldata_id ).count()
	if filecount >= maxfilecount:
		#
		# nincs tobb lehetoseg fajl feltoltesre ezzel az azonositoval
		# ############################################################
		form = T( 'There is no possibility for uploading more files!' )
	else:
		db.filestore.controlldata_id.default = controlldata_id
		crud.settings.auth = None
		db.filestore.filename.readable = False
		db.filestore.md5sum.readable = False
		if auth.user_id:
			db.filestore.created_by.default = auth.user_id
			db.filestore.modified_by.default = auth.user_id
			db.filestore.modified_by.update = auth.user_id

		form = crud.create( db.filestore,
										onvalidation = filestorevalidation,
										onaccept = filestoreaccept )
	filecount = db( db.filestore.controlldata_id == controlldata_id ).count()
	if filecount >= maxfilecount:
		#
		# nincs tobb lehetoseg fajl feltoltesre ezzel az azonositoval
		# ############################################################
		form = T( 'There is no possibility for uploading more files!' )
	flist = []
	for f in db( db.filestore.controlldata_id == controlldata_id ).select( orderby = ( db.filestore.description, db.filestore.filename ) ):
		if auth.user_id:
			fmodify = TD( A( IMG( _src = URL( c = 'static', f = 'toll.png' ), alt = T( 'Modify' ) ) , _href = URL( f = 'fstore', args = f.id ) ), _title = T( 'Modify' ) )
		else:
			fmodify = TD()
		flist.append( TR( 
									TD( SPAN( '%s' % f.description , _title = f.description ),
											BR(),
											SPAN( '[%s]' % f.md5sum, _title = f.md5sum ), _class = 'description' ),
									TD( SPAN( '%s' % f.filename, _title = '%s' % f.filename ), _class = 'filename' ),
									TD( f.modified_ip , BR(), f.modified_on , _class = 'modified' ),
									fmodify
									)
								)
	if len( flist ) > 0:
		filelist = TABLE( 
									THEAD( 
											TR( 
												TH( '%s' % db.filestore.description.label, BR(), db.filestore.md5sum.label, _class = 'description' ),
												TH( db.filestore.filename.label, _class = 'filename' ),
												TH( db.filestore.modified_ip.label, BR(), db.filestore.modified_on.label, _class = 'modified' ),
												TH()
												)
											),
									TBODY( 
											*flist
											)
									, _class = 'customtable' )
	return dict( form = form, filelist = filelist, controlldata_title = controlldata.title )






def error():
    return dict()




def controllaccept( form ):
	'''
	 Ha a controll adat most jött létre, akkor a létrehozó embernek
	 minden jogot megadunk hozzá
	'''
	if not auth.has_permission( 'read', db.controlldata, form.vars.id ):
		for role in ['select', 'read', 'update']:
			auth.add_permission( auth.user_group( auth.user.id ), role, db.controlldata, form.vars.id )



def controlldelete( form ):
	'''
	 Ha a controll adat most törlődött, töröljük a hozzá tartozó dolgokat
	'''
	#
	# a jogokat
	# ##########
	for role in ['select', 'read', 'update']:
		auth.del_permission( auth.user_group( auth.user.id ), role, db.controlldata, form.vars.id )

	#
	# a fájlokat - és bejegyzéseket
	# ##############################
	db( db.filestore.controlldata_id == form.vars.id ).delete()


def filestorevalidation( form ):
	'''
		Műveletvégzések, mielőtt egy fájl feltöltésre kerül
	'''
	#
	# filename beitasa
	# #####################################
	form.vars.filename = form.vars.content.filename
	#form.vars.md5sum = compute_md5( form.vars.content_newfilename )



def filestoreaccept( form ):
	'''
		Műveletvégzések, ha egy fájl feltöltésre kerül
	'''
	import os
	#
	# email kuldes az ertesitendo embernek
	# #####################################
	filestorerow = db( db.filestore.id == form.vars.id ).select( db.filestore.controlldata_id ).first()

	#
	# Meghatarozzuk, hova lett mentve a fájl
	# #######################################
	fpath = ''
	if db.filestore.content.uploadfolder:
		fpath = self.uploadfolder
	elif db._adapter.folder:
		fpath = os.path.join( db._adapter.folder, '..', 'uploads' )
	else:
		raise RuntimeError, "you must specify a Field(...,uploadfolder=...)"
	if db.filestore.content.uploadseparate:
		fpath = os.path.join( fpath, "%s.%s" % ( 'filestore', 'content' ),
												 form.vars.content_newfilename[
																			len( "%s.%s." % ( 'filestore', 'content' ) ):
																			len( "%s.%s." % ( 'filestore', 'content' ) ) + 2] )
	fpath = os.path.join( fpath, form.vars.content_newfilename )
	#
	# Kiszámítjuk az MD5-öt és beírjuk
	# #################################
	md5sum = compute_md5( fpath )
	db( db.filestore.id == form.vars.id ).update( md5sum = md5sum )
	controlldatarow = db( db.controlldata.id == filestorerow.controlldata_id ).select().first()
	tos = controlldatarow.tonotify.split( ',' )
	if len( tos ) == 0:
		#
		# Nincs megadva címzett akit értesíteni kellene
		# ##############################################
		return True
	subject = T( '[Upload::%(t)s]Uploaded file: %(d)s' , dict( d = str( form.vars.description[:20] ),
																								t = str( controlldatarow.title ) ) )
	body = T( '''
File reveived can be downloaded until %s.
=========================================

Download set %s link:
 http://%s%s

Direct link to the file:
 http://%s%s

/ File details:
| -------------
| %s: %s
| %s: %s
| %s: %s
| %s: %s
| %s: %s
\--------------
	''' , ( 
				str( controlldatarow.downloadvaliddate ),
				str( controlldatarow.title ),
				str( request.env.http_host ),
				str( URL( f = 'download', vars = dict( q = controlldatarow.dluuid ) ) ),
				str( request.env.http_host ),
				str( URL( f = 'download',
							args = form.vars.content,
							vars = dict( q = controlldatarow.dluuid ) ) ),
				str( db.filestore.filename.label ),
				str( form.vars.filename ),
				str( db.filestore.md5sum.label ),
				str( md5sum ),
				str( db.filestore.description.label ),
				str( form.vars.description ),
				str( db.filestore.modified_ip.label ),
				str( request.env.remote_addr ),
				str( db.filestore.modified_on.label ),
				str( request.now ),
				) )
	mail.send( to = tos,
					subject = subject,
					message = body )


def fstoreaccept( form ):
	'''
		Műveletvégzések, ha egy fájl módosításra kerül
	'''
	if form.vars.content_newfilename:
		import os
		#
		# Meghatarozzuk, hova lett mentve a fájl
		# #######################################
		fpath = ''
		if db.filestore.content.uploadfolder:
			fpath = self.uploadfolder
		elif db._adapter.folder:
			fpath = os.path.join( db._adapter.folder, '..', 'uploads' )
		else:
			raise RuntimeError, "you must specify a Field(...,uploadfolder=...)"
		if db.filestore.content.uploadseparate:
			fpath = os.path.join( fpath, "%s.%s" % ( 'filestore', 'content' ),
													 form.vars.content_newfilename[
																				len( "%s.%s." % ( 'filestore', 'content' ) ):
																				len( "%s.%s." % ( 'filestore', 'content' ) ) + 2] )
		fpath = os.path.join( fpath, form.vars.content_newfilename )
		#
		# Kiszámítjuk az MD5-öt és beírjuk
		# #################################
		md5sum = compute_md5( fpath )
		db( db.filestore.id == form.vars.id ).update( md5sum = md5sum )

def compute_md5( filename ):
	'''
		A filename-hez kiszámítjuk az md5 checksum-ot
	'''
	# 
	# http://stackoverflow.com/questions/1131220/get-md5-hash-of-a-files-without-open-it-in-python
	# ###################################################################
	import hashlib
	md5 = hashlib.md5()
	f = open( filename, 'rb' )
	while True:
		data = f.read( 128 * md5.block_size )
		if not data:
			break
		md5.update( data )
	f.close()
	return str( md5.hexdigest() )

