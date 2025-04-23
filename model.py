from ollama import chat
from ollama import ChatResponse
import json



#initial prompt -> source code + hotspot -> what is the issue
#second prompt -> source code + hotspot + prev response (identified issue) + prev response context (rag context based on prev response)-> why is this an issue?
#third prompt -> source code + hotspot + prev response (identified issue, why is this an issue) + prev response context (rag context based on prev response)-> consequences and fix
class GenerativeModel():

    def __init__(self, model, system_messages):
        self.model = model
        self.system_messages = system_messages

        messages = [
            {
                'role' : 'system',
                'content' : self.system_messages
            }
        ]

        response = chat(model=self.model, messages=messages, stream = False)
        # self.reasoning_response = response['message']['content']
        # return self._parse_response(response['message']['content'])


    
    def _reasoning(self, user_prompt):
        """
        The format used for every step of the LLM 
        
        """
        messages = [
            {
                'role': 'user',
                'content': user_prompt
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
