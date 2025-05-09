from model import GenerativeModel
# from vector import retriever
import json

from rag.rag_client import RagClient
# import langchain
# langchain.verbose = False
# langchain.debug = False
# langchain.llm_cache = False

def latext_format():
    dev_report_latex = """
    output a tex document given this template, use the json output to replace the template strings in <>. Only replace the template strings, do not add new latex formatting.:
    \\documentclass{article}
    \\usepackage[margin=1in]{geometry}
    \\usepackage{enumitem}
    \\title{Developer Report}
    \\begin{document}

    \\maketitle

    \\section*{Bug Report}
    \\begin{itemize}
    \\item Security issues: <count>
    \\end{itemize}

    \\section*{Triaging}

    \\subsection*{P1}
    \\begin{itemize}
    \\item <issue and fix>
    \\end{itemize}

    \\subsection*{P2}
    \\begin{itemize}
    \\item <issue and fix>
    \\end{itemize}

    \\end{document}
    """

    manager_report_latex = """
    output a tex document given this template, use the json output to replace the template strings in <>. Only replace the template strings, do not add new latex formatting.:
    \\documentclass{article}
    \\usepackage[margin=1in]{geometry}
    \\usepackage{enumitem}
    \\title{Manager Report}
    \\begin{document}

    \\maketitle

    \\section*{Bug Report}
    \\begin{itemize}
    \\item Security issues: <count>
    \\end{itemize}

    \\section*{Assessment}
    <assessment>

    \\subsection*{}
    \\begin{itemize}
    \\item <issue and consequence>
    \\item Production readiness: <ready or not ready depending on the assessment>
    \\end{itemize}

    \\end{document}
    """

    return dev_report_latex, manager_report_latex

def prompt():

    return  """
    <System Instructions>

        You are a Senior Security Analyst. 
        You are skilled at identifying issues related to security.
        You are skilled at diagnosing security hotspots.
        You are capable of suggesting solutions to fix these hotspots. 
        You are highly capable, thoughtful and precise at your job. 
        Your goal is to deeply understand the security issue at hand from the <Hotspot> section only.
        Think step-by-step through the issues reported in <Hotspot> and use the information provided in <Context>, <Source Code> and <Previous Response> to augment your understanding of the issue and potential fix.
        Rspond only in JSON ALWAYS
        Always prioritize being truthful, nuanced, insightful, and efficient.
        Always follow the above rules.
        Do NOT deviate.


        A hotspot in a code file is defined as below:

        <Hotspot>
            A piece of code which is a security issue as identified by static code analyzer.

            It will at least have the following fields: 

            {
                "rule":{
                    "name" : "A description of what the hotspot is",
                    "riskDescription" : "The description of the risks posed by utilizing the current code in this context",
                    "vulnerabilityDescription" : "Questions to evaluate if the current usage of this piece of code leads to a vulnerability."
                }
            }

        </Hotspot>
        
        <Source Code>
            This will contain the exact block of source code that caused the hotspot to be flagged by the static code analyzer.
        </Source Code>

        <Context>
            Context is the owasp recommendations for steps needed to fix the issues reported in hotspots. You are to only use this to better undestand the hotspot issues at hand and ways to fix them.
        </Context>
        
        <Previous Response>
            This section will contain the reponses you provided to the user seperated by dashes ('---------').
            Use this as additional context to provide meaningful reponses.
        </Previous Response>
            
    </System Instructions>	
    """

def prompt_issue_identify(hotspot: str, source_code: str) -> str:
    return f"""
    <Hotspot>
        {hotspot}
    </Hotspot>

    <Source Code>
        {source_code}
    </Source Code>

    Given this hotspot response from Sonar, identify the core issue of this hotspot. 

    Respond in the following JSON format only:

    {{
        "issue": <description of the issue>,
        "reason": <description of why is it an issue>
    }}
    """

def prompt_issue_reason(previous_response: str, source_code: str, context: str) -> str:
    return f"""
    <Context>
        {context}
    </Context>

    <Previous Response>
        {previous_response}
    </Previous Response>

    <Source Code>
        {source_code}
    </Source Code>

    Given the context, source code, as well as your previous responses, respond to the user's query. I want to know why is this a security issue. 

    Explain your reason in depth. 

    Respond in the following JSON format only:

    {{
        "reason": <an in depth description of why is it an issue>
        "fix": <description of issue fix>
    }}
    """

def prompt_issue_fix(previous_response: str, source_code: str, context: str) -> str:
    return f"""
    <Context>
        {context}
    </Context>

    <Previous Response>
        {previous_response}
    </Previous Response>

    <Source Code>
        {source_code}
    </Source Code>

    Given the context, source code, as well as your previous responses, respond to the user's query. I want to know what are the best ways to fix this a security issue. Give me multiple alternatives based on the context provided.

    Explain why each provided fix would solve the security hotspot.

    Also, explain the consequences of leaving this issue unfixed.

    Respond in the following JSON format only:

    {{
        "fixes": [
            {{
                "fix": <description of the fix for security hotspot>
                "reason": <description of why this fix will solve the issue>
            }}
        ],
        "consequences": <in-depth description of negative impacts of leaving this issue unfixed>,
        "priority": <category of P1 or P2 depending on the severity of the consequences. If it cannot be pushed to production, it's a P1 else it's a P2>
    }}
    """

def main():

    #example hotspot
    hotspot = {
        "key": "AZXuxmIAWcmXo5BiV16c",
        "component": {
            "key": "commons-io:src/main/java/org/apache/commons/io/input/MessageDigestCalculatingInputStream.java",
            "qualifier": "FIL",
            "name": "MessageDigestCalculatingInputStream.java",
            "longName": "src/main/java/org/apache/commons/io/input/MessageDigestCalculatingInputStream.java",
            "path": "src/main/java/org/apache/commons/io/input/MessageDigestCalculatingInputStream.java"
        },
        "project": {
            "key": "commons-io",
            "qualifier": "TRK",
            "name": "Apache Commons IO",
            "longName": "Apache Commons IO"
        },
        "rule": {
            "key": "java:S4790",
            "name": "Using weak hashing algorithms is security-sensitive",
            "securityCategory": "others",
            "vulnerabilityProbability": "LOW",
            "riskDescription": "<p>Cryptographic hash algorithms such as <code>MD2</code>, <code>MD4</code>, <code>MD5</code>, <code>MD6</code>, <code>HAVAL-128</code>,\n<code>HMAC-MD5</code>, <code>DSA</code> (which uses <code>SHA-1</code>), <code>RIPEMD</code>, <code>RIPEMD-128</code>, <code>RIPEMD-160</code>,\n<code>HMACRIPEMD160</code> and <code>SHA-1</code> are no longer considered secure, because it is possible to have <code>collisions</code> (little\ncomputational effort is enough to find two or more different inputs that produce the same hash).</p>\n",
            "vulnerabilityDescription": "<h2>Ask Yourself Whether</h2>\n<p>The hashed value is used in a security context like:</p>\n<ul>\n  <li> User-password storage. </li>\n  <li> Security token generation (used to confirm e-mail when registering on a website, reset password, etc …​). </li>\n  <li> To compute some message integrity. </li>\n</ul>\n<p>There is a risk if you answered yes to any of those questions.</p>\n<h2>Sensitive Code Example</h2>\n<pre>\nMessageDigest md1 = MessageDigest.getInstance(\"SHA\");  // Sensitive:  SHA is not a standard name, for most security providers it's an alias of SHA-1\nMessageDigest md2 = MessageDigest.getInstance(\"SHA1\");  // Sensitive\n</pre>\n",
            "fixRecommendations": "<h2>Recommended Secure Coding Practices</h2>\n<p>Safer alternatives, such as <code>SHA-256</code>, <code>SHA-512</code>, <code>SHA-3</code> are recommended, and for password hashing, it’s even\nbetter to use algorithms that do not compute too \"quickly\", like <code>bcrypt</code>, <code>scrypt</code>, <code>argon2</code> or <code>pbkdf2</code>\nbecause it slows down <code>brute force attacks</code>.</p>\n<h2>Compliant Solution</h2>\n<pre>\nMessageDigest md1 = MessageDigest.getInstance(\"SHA-512\"); // Compliant\n</pre>\n<h2>See</h2>\n<ul>\n  <li> <a href=\"https://owasp.org/Top10/A02_2021-Cryptographic_Failures/\">OWASP Top 10 2021 Category A2</a> - Cryptographic Failures </li>\n  <li> <a href=\"https://www.owasp.org/www-project-top-ten/2017/A3_2017-Sensitive_Data_Exposure\">OWASP Top 10 2017 Category A3</a> - Sensitive Data\n  Exposure </li>\n  <li> <a href=\"https://owasp.org/www-project-top-ten/2017/A6_2017-Security_Misconfiguration\">OWASP Top 10 2017 Category A6</a> - Security\n  Misconfiguration </li>\n  <li> <a href=\"https://mobile-security.gitbook.io/masvs/security-requirements/0x08-v3-cryptography_verification_requirements\">Mobile AppSec\n  Verification Standard</a> - Cryptography Requirements </li>\n  <li> <a href=\"https://owasp.org/www-project-mobile-top-10/2016-risks/m5-insufficient-cryptography\">OWASP Mobile Top 10 2016 Category M5</a> -\n  Insufficient Cryptography </li>\n  <li> <a href=\"https://cwe.mitre.org/data/definitions/1240\">MITRE, CWE-1240</a> - Use of a Risky Cryptographic Primitive </li>\n  <li> <a href=\"https://www.sans.org/top25-software-errors/#cat3\">SANS Top 25</a> - Porous Defenses </li>\n</ul>"
        },
        "status": "TO_REVIEW",
        "line": 156,
        "hash": "251eb7e346cc9b6b77ea9d03fe19a372",
        "message": "Make sure this weak hash algorithm is not used in a sensitive context here.",
        "author": "gardgregory@gmail.com",
        "creationDate": "2022-07-26T13:04:31+0000",
        "updateDate": "2025-04-01T00:34:58+0000",
        "textRange": {
            "startLine": 156,
            "endLine": 156,
            "startOffset": 29,
            "endOffset": 40
        },
        "changelog": [],
        "comment": [],
        "users": [],
        "canChangeStatus": True,
        "flows": [],
        "messageFormattings": []
    }

    system_message, dev_json, manager_json = prompt()

    # Initialize model
    security_analyst = GenerativeModel(
        model="llama3.1:8b",
        system_messages=system_message,
    )

    #first iteration of prompting
    prompt_issue_identify = prompt_issue_identify()
    prompt_issue_identify_response = security_analyst._reasoning(prompt_issue_identify_response)

    #try catch needed if issue is not in the json
    try:
        issue = prompt_issue_identify_response["issue"]
    except Exception as e:
        print(e)

    # search the RAG database and fetch the indexed documents that match the search query
    rag = RagClient(collection_name="owasp_db")
    context_docs = rag.get_context(query=issue, semantic_limit=100, ranked_limit=5)

    # combine the context with the hotspots to form the input to the LLM
    context = "----------------------".join([doc['heading_stack']+"\n"+doc['content'] for doc in context_docs])

    # Perform reasoning
    dev_output_json = security_analyst._reasoning(hotspot, context, dev_json)
    manager_output_json = security_analyst._reasoning(hotspot, context, manager_json)
    #print(dev_output_json, manager_output_json, sep ="\n\n")

    dev_latex, manager_latex = latext_format()
    
    # Generate final report
    dev_report = security_analyst.generate_report(dev_output_json, dev_latex)
    manager_report = security_analyst.generate_report(manager_output_json, manager_latex)
    
    #print(dev_report, manager_report, sep = "\n\n")


if __name__ == "__main__":
    main()