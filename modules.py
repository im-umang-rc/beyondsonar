from pathlib import Path
from dotenv import load_dotenv
import os
import requests
import json
import subprocess
import zipfile
from io import BytesIO

def fetch_hotspots(project):
    cookies = __get_cookies()
    hotspots = __find_hotspots(project, cookies)

    hotspot_details = []
    for hotspot in hotspots:
        details = __get_hotspot_details(hotspot=hotspot['key'], cookies=cookies)
        hotspot_details.append(details)
    return hotspot_details

def fetch_source_code(project, path, line):
    full_path = os.path.join(Path.cwd().parent, project, path)
    with open(full_path, 'r') as f:
        lines = f.readlines()
    snippet = lines[line - 1]
    return snippet

def __get_env(key):
    return os.environ.get(key)

def __get_cookies():
    authBody = {
        "login": __get_env('SONAR_USER'),
        "password": __get_env('SONAR_PASSWORD')
    }
    authResponse = requests.post(__get_env('SONAR_AUTH_URI'), authBody)
    return authResponse.cookies

def __find_hotspots(project, cookies):
    hotspots = requests.get(__get_env('SONAR_HOTSPOT_SEARCH_URI') + project, cookies=cookies)
    return json.loads(hotspots.text)['hotspots']

def __get_hotspot_details(hotspot, cookies):
    hotspot_details = requests.get(__get_env('SONAR_HOTSPOT_DETAILS_URI') + hotspot, cookies=cookies)
    return json.loads(hotspot_details.text) 

def get_reports(dev_report, manager_report):
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
    return zip_buffer

def format_reports(issues):
    count = len(issues)
    
    triage_section = """
        \\subsubsection*{{ {issue} }}
        \\begin{{itemize}}
            {items}
        \\end{{itemize}}
    """

    bug_section = """
        \\item {fix}
        \\\\
        \\textit{{ {reason} }}
    """

    body = []
    assessments = []
    consequences = []
    for issue in issues:
        bugs=[]
        for fix in issue['resolution']['fixes']:
            bugs.append(bug_section.format(fix=fix['fix'], reason=fix['reason']))
        body.append(triage_section.format(issue=issue['issue'], items=" \\\\".join(bugs)))
        assessments.append(issue['reason'])
        consequences.append(issue['resolution']['consequences'])

    assessment = " \\\\ ".join(assessments)
    consequence = " \\\\ ".join(consequences)
    dev_body=" \\\\ ".join(body)

    p2_section = ""

    manager_report = f"""
		\\documentclass{{article}}
        \\usepackage[margin=1in]{{geometry}}
        \\usepackage{{enumitem}}
        \\title{{Manager Report}}
        \\begin{{document}}

        \\maketitle

        \\section*{{Bug Report}}
        \\begin{{itemize}}
        \\item Security issues: {count}
        \\end{{itemize}}

        \\section*{{Assessment}}
        {assessment}

        \\section*{{Consequences}}
        {consequence}

        \\end{{document}}
    """

    developer_report = f"""
        \\documentclass{{article}}
        \\usepackage[margin=1in]{{geometry}}
        \\usepackage{{enumitem}}
        \\title{{Developer Report}}
        \\begin{{document}}

        \\maketitle

        \\section*{{Bug Report}}
        \\begin{{itemize}}
        \\item Security issues: {count}
        \\end{{itemize}}

        \\section*{{Triaging}}

        \\subsection*{{P1}}
        {dev_body}

        \\subsection*{{P2}}
        {p2_section}

        \\subsection*{{Assessment}}
        {assessment}

        \\end{{document}}
    """


    return developer_report, manager_report