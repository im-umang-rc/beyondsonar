from model import GenerativeModel
# from vector import retriever
import json
# import langchain
# langchain.verbose = False
# langchain.debug = False
# langchain.llm_cache = False

def latext_format():
    dev_report_latex = """
    output a tex document given this template, use the json output to replace the template strings in <>:
    latex```
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
    ```
    """

    manager_report_latex = """
    output a tex document given this template, use the json output to replace the template strings in <>:
    latex```
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
    ```
    """

    return dev_report_latex, manager_report_latex

def prompt():

    system_message = """
    <System instructions>

        You are a Senior Security Analyst. 
        You are skilled at identifying issues related to security.
        You are skilled at diagnosing security bugs.
        You are capable of suggesting solutions to fix these bugs. 
        You are highly capable, thoughtful and precise at your job. 
        Your goal is to deeply understand the security issue at hand from the <Hotspot> section only.
        Think step-by-step through the issues reported in <Hotspot> and use the information provided in <Context> to augment your understanding of the issue and potential fix.
        Provide clear and accurate answers.
        Always prioritize being truthful, nuanced, insightful, and efficient. 
        Use only the content provided to you in terms of <Hotspots> section and <Context> section.
        Always follow the above rules.
        Do not deviate.
    

        A hotspot in a code file is defined as below:

        <Hotspot>
            A piece of code which is likely to be a security issue as identified by Sonar QUBE.

            It will at least have the following fields: 

            {   
                "component" : {
                    "key" : "The exact location of the hotspot in terms of file location."
                }
                "name" : "A description of what the hotspot is.",
                "riskDescription" : "The description of the risks posed by utilizing the current code in this context.",
                "vulnerabilityDescription" : "Questions to evaluate if the current usage of this piece of code leads to a vulnerability.",
            }

        </Hotspot>

        <Sonar Qube>
            Sonar QUBE is a software that integrates into the CI/CD pipeline to analyze code.
            It analyzes the code complexity, the bugs, technical debt and potential hotspots. 
        </Sonar Qube>

        <Context>
            Context is the owasp recommendations for steps needed to fix the issues reported in hotspots. You are to only use this to better undestand the hotspot issues at hand and ways to fix them.
        </Context>

    </System instructions>
    
    """

    dev_output_structure_json = """

    <Output Structure>
        You are supposed to return a report in JSON format. 
        The output will be a report, structured as JSON, whose format is given below.
        Avoid any extra back-ticks "`" or any other keywords like "JSON" in the output.
        Do 'NOT' use any special characters inside the JSON. 
        Follow the output structure as indicated by the JSON format.
        Each fields description is provided to you to help you make the report. 

        given a Json output which is in following format, <> represents a string template that will be replaced with actual content:

        {
            "count": <total count of the vulnerability hotspots in integer format>,
            "p1Count": <count of high priority issues that can lead to security incidents in production leading to data loss, reputation loss>,
            "p2Count": <count of vulnerability hotspots whose fix can be postponed in favor of other priority issues and bugs but they still need to be addressed eventually>,
            "top5": <Array that will contain only the top 5 most pressing vulnerabilities, start picking them from the P1s and then move onto P2s if no P1s remain, refer "top5" for the format>,
            "assessment": <A paragraph that highlights the most pressing issues in the project and informs if this is production ready. Production readiness is defined as absence of P1s. This needs to be read by the developers who need to understand why the project is not production ready by using the most pressing issues and the steps needed to make it production ready.>
        }

        "top5": {
            {
                "issue": <a brief description of what the issue is>,
                "consequences": <An in-depth description of the harms this issue can cause with reference to the context provided to you. Why is this a P1/ P2. This description is aimed at developers, ensure you are explaining the technicalities of what harms this can cause in production.>,
                "fixSteps": <Possible solutions (max 3) with in-depth steps to fix the issue. The description is aimed at developers who will be reading this to fix the issue.>,
                "priority": <one of P1 or P2 based on the severity. P1s can lead to security incidents in production leading to data loss, reputation loss. P2s can be postponed in favor of other priority issues but still need to be addressed eventually>
            },
            <repeat for a total of 5 issues in the array, start from P1s and include P2s to meet the count of 5.>
        }

    </Output Structure>
    
    """

    manager_output_structure_json = """
        given a Json output which is in following format, <> represents a string template that will be replaced with actual content:

        {
            "count": <total count of the vulnerability hotspots in integer format>,
            "p1Count": <count of high priority issues that can lead to security incidents in production leading to data loss, reputation loss>,
            "p2Count": <count of vulnerability hotspots whose fix can be postponed in favor of other priority issues and bugs but they still need to be addressed eventually>,
            "top5": <Array that will contain only the top 5 most pressing vulnerabilities, start picking them from the P1s and then move onto P2s if no P1s remain, refer "Top5 Array Json" for the format>,
            "assessment": <A 2 line sentence that highlights the most pressing issues in the project and informs if this is production ready. This is to be read by a manager who might not undestand the technicalities being the issues.>
        }

        "Top5": {
            {
                "issue": <a brief description of what the issue is, limit to a single sentence>,
                "fixSteps": <A 1 sentence solution to fix the issue. The description is aimed at developers who will be reading this to fix the issue.>,
                "consequences": <A 1 sentence description of the harms this issue can cause. Why is this a P1/ P2. The description is aimed at managers who might not understand the technicalities behind the issue>,
                "priority": <one of P1 or P2 based on the severity. P1s can lead to security incidents in production leading to data loss, reputation loss, P2s can be postponed in favor of other priority issues but still need to be addressed eventually>
            },
            <repeat for a total of 5 issues in the array, start from P1s and include P2s to meet the count of 5.>
        }


    """

    return system_message, dev_output_structure_json, manager_output_structure_json

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


    # Retrieve relevant context
    context_docs = retriever.invoke(hotspot["rule"]["name"])
    context = " \n".join([doc.page_content for doc in context_docs])

    system_message, dev_json, manager_json = prompt()

    # Initialize model
    security_analyst = GenerativeModel(
        model="llama3.1:8b",
        system_messages=system_message,
        output_structure=dev_json
    )

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