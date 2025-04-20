from flask import Flask, jsonify, send_file, abort, request
import subprocess
import os
import tempfile
import shutil
import json
import requests
from rag.rag_client import RagClient
from prompt import prompt, latext_format
from model import GenerativeModel
import zipfile
from io import BytesIO

app = Flask(__name__)

with open('config.json') as config_file:
    config_data = json.load(config_file)
    app.config.update(config_data)

@app.route("/report", methods=["GET"])
def start():

	# authenticate with Sonar
	loginUrl = app.config['sonar_url'] + app.config['sonar_login']
	loginRes = requests.post(loginUrl, 
						  {"login" : app.config['username'] ,
		  "password" : app.config['password']})

	# fetch the hotspots
	project_key = request.args.get('project_key')
	searchUrl = app.config['sonar_url'] + app.config['sonar_hotspot_api'] + project_key
	res = requests.get(searchUrl, cookies=loginRes.cookies)

	# fetch the hotspot description
	hotspots = json.loads(res.text)['hotspots']
	input= []
	for hotspot in hotspots:
		hostspotsUrl = app.config['sonar_url'] + app.config['sonar_hotspot_details'] + hotspot['key']
		hotspotData = requests.get(hostspotsUrl, cookies=loginRes.cookies)
		input.append(json.loads(hotspotData.text)['rule']['name'] + "," + json.loads(hotspotData.text)['message'])

	# search the RAG database and fetch the indexed documents that match the search query
	rag = RagClient(collection_name="owasp_db")
	context_docs = rag.get_context(query="".join(input), semantic_limit=100, ranked_limit=5)

	# combine the context with the hotspots to form the input to the LLM
	context = " \n".join([doc['heading_stack']+"\n"+doc['content'] for doc in context_docs])
	system_message, dev_json, manager_json = prompt()

    # Initialize model
	security_analyst = GenerativeModel(
		model="llama3.1:latest",
		system_messages=system_message,
		output_structure=dev_json
	)

    # Perform reasoning
	dev_output_json = security_analyst._reasoning(hotspot, context, dev_json)
	manager_output_json = security_analyst._reasoning(hotspot, context, manager_json)

	print(dev_output_json)

	# convert the json report to .tex format
	dev_latex, manager_latex = latext_format()

	# Generate final report
	dev_report = security_analyst.generate_report(dev_output_json, dev_latex)
	manager_report = security_analyst.generate_report(manager_output_json, manager_latex)

	# convert the .tex file to .pdf
	with open("output/developer_report.tex", "w") as f:
		f.write(dev_report)
	with open("output/manager_report.tex", "w") as f:
		f.write(manager_report)

	try:
		subprocess.run(["pdflatex", "output/developer_report.tex"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		subprocess.run(["pdflatex", "output/manager_report.tex"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	except:
		print('Error converting pdf')

	# archive the files and send back
	zip_buffer = BytesIO()
	with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
		zip_file.write('developer_report.pdf')
		zip_file.write('manager_report.pdf')

	zip_buffer.seek(0)

	return send_file(
		zip_buffer,
		as_attachment=True,
		download_name='reports.zip',
		mimetype='application/zip'
	)