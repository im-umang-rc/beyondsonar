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

app = Flask(__name__)

with open('config.json') as config_file:
    config_data = json.load(config_file)
    app.config.update(config_data)

@app.route("/start", methods=["GET"])
def start():
	loginUrl = app.config['sonar_url'] + app.config['sonar_login']
	loginRes = requests.post(loginUrl, 
						  {"login" : app.config['username'] ,
		  "password" : app.config['password']})

	project_key = request.args.get('project_key')
	searchUrl = app.config['sonar_url'] + app.config['sonar_hotspot_api'] + project_key
	res = requests.get(searchUrl, cookies=loginRes.cookies)


	hotspots = json.loads(res.text)['hotspots']
	input= []
	for hotspot in hotspots:
		hostspotsUrl = app.config['sonar_url'] + app.config['sonar_hotspot_details'] + hotspot['key']
		hotspotData = requests.get(hostspotsUrl, cookies=loginRes.cookies)
		# print(hotspotData.text)
		input.append(json.loads(hotspotData.text)['rule']['name'] + "," + json.loads(hotspotData.text)['message'])

	print(input)

	rag = RagClient(collection_name="owasp_db")
	context_docs = rag.get_context(query="".join(input), semantic_limit=100, ranked_limit=5)

	context = " \n".join([doc['heading_stack']+"\n"+doc['content'] for doc in context_docs])

	print(context)

	# return "Success"

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
	#print(dev_output_json, manager_output_json, sep ="\n\n")

	print(dev_output_json)

	# return "Success"

	dev_latex, manager_latex = latext_format()

	# Generate final report
	dev_report = security_analyst.generate_report(dev_output_json, dev_latex)
	manager_report = security_analyst.generate_report(manager_output_json, manager_latex)

	write_pdf(dev_report, "dev")
	write_pdf(manager_report, "mgr")

	return "Success"


def write_pdf(input, type):
	with open(f"output/{type}.tex", "w") as f:
		f.write(input)

		# subprocess.run(["pdflatex", f"{type}.tex"], cwd=temp_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
