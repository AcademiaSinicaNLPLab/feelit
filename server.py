from flask import Flask, render_template, url_for, make_response, Response, jsonify, request
import sys, json, os
import fetch_mongo
import confusion_matrix as matrix
app = Flask(__name__)

cache_folder_name = 'feelit-data'
cache_folder_root = os.path.join(os.getcwd(), cache_folder_name)

@app.route('/')
def hello():
	return render_template( 'index.html' )

@app.route("/browse")
@app.route("/browse/")
def list_emotions():
	emotions = fetch_mongo.get_emotion_list()
	return render_template( 'emotions.html', emotions=emotions )

@app.route("/browse/<emotion>/")
def list_docIDs(emotion):
	return render_template( 'docids.html', emotion=emotion )

@app.route('/browse/<emotion>/<int:ldocID>/')
def list_sents(emotion, ldocID):
	sp_pairs = fetch_mongo.get_sp_pairs(emotion, ldocID)
	docscore_categories = fetch_mongo.get_docscore_categories()
	return render_template( 'sents.html', emotion=emotion, ldocID=ldocID, sp_pairs=sp_pairs, docscore_categories=docscore_categories )

@app.route('/chart')
@app.route('/chart/')
def plot():
	return render_template( 'chart.html' )


@app.route('/matrix')
@app.route('/matrix/')
def show_matrix(setting_id='537b00e33681df445d93d57e', svm_param='c9r2t1'):

	if not request.args:
		data = {}
		## list availabel matrix
		# matrix.list_all()

	elif request.args['setting_id'] and request.args['svm_param']:
		cache_fn   = '.'.join([setting_id, svm_param, 'json'])
		cache_path = os.path.join(cache_folder_root, cache_fn)

		## found in cache
		if os.path.exists(cache_path):
			data = json.load(open(cache_path, 'r'))
			print >> sys.stderr, '[cache] load', cache_fn
		## cannot find in cache
		else:
			matrix.setting_id = setting_id
			matrix.svm_param = svm_param
			## set default search path
			# matrix.external_search = external_search
			# matrix.internal_search = internal_search

			print >> sys.stderr, '[call] [server.py] matrix.load_data()'
			matrix.load_data()

			print >> sys.stderr, '[call] [server.py] matrix.generate()'
			data = matrix.generate()

			if data:
				## cache it
				json.dump(data, open(cache_path, 'w'))
				print >> sys.stderr, '[cache] dump', cache_fn
	else:
		data = {}

	return render_template( 'matrix.html', matrix=data, order=list( enumerate(sorted(data.keys())) ) )

## -------------------- APIs -------------------- ##

@app.route('/api/pat_distribution/<pat>')
@app.route('/api/pat_distribution/<pat>/')
def showplot(pat):
	print >> sys.stderr, '[info] get pattern "'+pat+'"'
	pat_data = fetch_mongo.get_pat_dist(pat)
	print >> sys.stderr, '[info] data length:', len(pat_data)

	if type(pat_data) == list and len(pat_data) == 0:
		return Response(status=204)
	elif type(pat_data) == list and len(pat_data) > 0:
		return Response(json.dumps(pat_data), mimetype="application/json", status=200)
	else:
		return Response(status=500)

@app.route('/api/pat_sentences/<pat>')

@app.route('/api/pat_sentences/<pat>/<emo>/')
def showsents(pat, emo=None):
	return fetch_mongo.get_sents_by_pat(pat, emo)

@app.route('/api/docscore/<udocID>/<docscore_category>')
def showdocscore():
	return fetch_mongo.get_docscores(udocID, docscore_category)


# @app.route('/api/matrix/')
# def get_matrix():
# 	matrix.path_to_answer = 'data/0.out'
# 	matrix.path_to_gold = 'data/gold.txt'

# 	matrix.load_data()
# 	M = matrix.generate()

# 	return Response(json.dumps(M), mimetype="application/json", status=200)

if __name__ == "__main__":
	import getopt, sys

	_port = 5000
	app.debug = False

	try:
		opts, args = getopt.getopt(sys.argv[1:],'p:d',['port=', 'debug'])
	except getopt.GetoptError:
		exit(2)

	for opt, arg in opts:
		if opt in ('-p', '--port'): _port = int(arg.strip())
		elif opt in ('-d','--debug'): app.debug = True

	app.run(host='0.0.0.0', port=_port)
