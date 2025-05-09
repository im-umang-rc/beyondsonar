from flask import Flask, jsonify, send_file, abort, request
import json
from dotenv import load_dotenv
import os
from rag.rag_client import RagClient
from prompt import prompt, latext_format, prompt_issue_fix, prompt_issue_identify, prompt_issue_reason
from model import GenerativeModel
from modules import fetch_hotspots, fetch_source_code, get_reports, format_reports

app = Flask(__name__)

@app.route("/report", methods=["GET"])
def start():

	project = request.args.get('project_key')

	hotspots = fetch_hotspots(project)

	security_analyst = GenerativeModel(
		model=os.environ.get("LLM_MODEL"),
		system_messages=prompt(),
	)

	issues = []
	for hotspot in hotspots:
		source_code = fetch_source_code(project, hotspot['component']['path'], hotspot['line'])

		input = {
			'rule': {
				'name': hotspot['rule']['name'],
				'riskDescription': hotspot['rule']['riskDescription'],
				'vulnerabilityDescription': hotspot['rule']['vulnerabilityDescription']
			}
		}

		#first iteration of prompting
		issue_identify = prompt_issue_identify(json.dumps(input), source_code)
		issue_identify_res = security_analyst._reasoning(user_prompt=issue_identify)

	    #try catch needed if issue is not in the json
		try:
			issue = issue_identify_res["issue"]
		except Exception as e:
			print(e)

		rag = RagClient(collection_name="owasp_db")
		context_docs = rag.get_context(query=issue, semantic_limit=100, ranked_limit=5)

		# combine the context with the hotspots to form the input to the LLM
		context = "--------------".join([doc['heading_stack']+"\n"+doc['content'] for doc in context_docs])

		#second iteration of prompting
		issue_reason = prompt_issue_reason(previous_response=json.dumps(issue_identify_res), source_code=source_code, context = context)

		issue_reason_res = security_analyst._reasoning(user_prompt=issue_reason)

		issue_fix = prompt_issue_fix(previous_response="-------------".join([json.dumps(issue_identify_res), json.dumps(issue_reason_res)]), source_code = source_code, context = context)

		issue_fix_res = security_analyst._reasoning(user_prompt = issue_fix)

		print(issue_identify_res,issue_reason_res, issue_fix_res, sep ="---------------------")

		issue_reason_res['reason']
		issue_fix_res
		issues.append({
			'issue': issue_identify_res['issue'],
			'reason':issue_reason_res['reason'],
			'resolution': issue_fix_res
		})

	dev_report, manager_report = format_reports(issues)
	zip_buffer = get_reports(dev_report, manager_report)
	return send_file(
		zip_buffer,
		as_attachment=True,
		download_name='reports.zip',
		mimetype='application/zip'
	)