from ollama import chat
from ollama import ChatResponse
import json

class GenerativeModel():

    def __init__(self, model, system_messages, output_structure):
        self.model = model
        self.system_messages = system_messages
        self.output_structure = output_structure
        self.reasoning_response = None
    
    def _reasoning(self, hotspot, context, json_structure):
        """
        Perform reasoning analysis using:
        - System message instructions
        - Hotspot JSON data
        - Retrieved context from vector store
        """
        messages = [
            {
                'role': 'system', 
                'content': self.system_messages
            },
            {
                'role': 'user',
                'content': f"""
                Analyze this security hotspot with the provided context:

                <Hotspot>
                {json.dumps(hotspot, indent=2)}
                </Hotspot>

                <Context>
                {context}
                </Context>

                Think step-by-step about:
                1. Validity of the hotspot concerns
                2. Potential attack vectors
                3. Relevant security principles
                4. Possible mitigation strategies

                Finally give a JSON output as detailed below:
                {json_structure}
                Use double quotes ("") for the keys and values. 
                """
            }
        ]
        
        response = chat(model=self.model, messages=messages, format="json", stream = False)
        self.reasoning_response = response['message']['content']
        return self._parse_response(response['message']['content'])
        
    
    def generate_report(self, json_output, latex_structure):
        """
        Generate final report using the JSON provided
        """

        report_system_prompt = f"""
        You need to convert the JSON given to you to Latex format. 
        Adhere to the instructions provided to be rewarded. 
        """

        messages = [
            {
                'role': 'system',
                'content': report_system_prompt
            },
            {
                'role': 'user',
                'content': f"""
                This is the JSON information you have: \n
                {json_output} \n

                The following is the tex document template: \n
                {latex_structure} \n

                Give me only the latex document. 

                """
            }
        ]

        response = chat(model=self.model, messages=messages)
        return response['message']['content']

    def _parse_response(self, response):
        """Extract JSON from response with error handling"""
        try:
            # Attempt direct JSON parse
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback: Try to extract JSON from markdown
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                return json.loads(response[start:end])
            except Exception as e:
                print(f"Failed to parse response: {e}")
                return {
                    "error": "Failed to generate valid JSON",
                    "raw_response": response
                }
