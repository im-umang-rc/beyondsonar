# Steps to Run

## Software Requirements

1. **Docker**: You need to have docker desktop running on either your laptop/ desktop or on the cloud provider where you plan to host this.

2. **PDFLatex**: You need a linux system to run this to get the pdf reports. If you are running debian or it's variants you can try `sudo apt-get install texlive-latex-base texlive-fonts-recommended texlive-latex-extra` to install the necessary packages for latex

3. **Python**: You need to install Python 3 for the app to run. After that run create a virtual environment (recommended). Then run `pip install requirements.txt` to install the required packages for the application to work.

## Setup

1. Run `docker compose up` in this directory

2. Access SonarQube at localhost:9000 or cloud hostname: 9000

3. Checkout Apache commons IO for the project. `git checkout https://github.com/apache/commons-io.git`. Optionally you can use any other project of your choice.

4. Follow the steps and setup a local repository manually in SonarQube. Run the command presented in SonarQube to have the reports uploaded to SonarQube.

5. Run `python rag.rag_client.py` to update the knowledgebase of RAG

6. Create a `.env` file and add the following entries. Replace localhost with the actual URL depending on Cloud hosting:

    i. QDRANT_URI="http://localhost:6333"

    ii. SONAR_AUTH_URI="http://34.132.13.181:9000/api/authentication/login"

    iii. SONAR_USER="\<admin username\>"

    iv. SONAR_PASSWORD="\<admin password\>"

    v. SONAR_HOTSPOT_SEARCH_URI="http://34.132.13.181:9000/api/hotspots/search?projectKey="

    vi. SONAR_HOTSPOT_DETAILS_URI="http://34.132.13.181:9000/api/hotspots/show?hotspot="

    vii. LLM_MODEL="llama3.1:latest"

## Running the Application

1. Run `flask --app app run` to run the flask based app.

2. Navigate to `localhost:5000/report?project_key=commons-io`, replace commons-io with the project key of step 2. This should run the LLM and you will be able to download the reports as a zip in about a minute.
