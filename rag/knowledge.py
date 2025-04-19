import os
import requests

class Knowledge:
    def __init__(self, output_dir: str) -> None:
        self.__output_dir = output_dir
        
    def download_md_files(self, api_url: str):
        os.makedirs(self.__output_dir, exist_ok=True)

        # Fetch file list from GitHub
        response = requests.get(api_url)
        if response.status_code != 200:
            raise Exception("Error fetching data:", response.json())

        files = response.json()

        # Download .md files
        for file in files:
            if file["name"].endswith(".md"):
                file_url = file["download_url"]
                file_path = os.path.join(api_url, file["name"])

                # Download file
                file_content = requests.get(file_url).text
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_content)

                print(f"Downloaded: {file['name']}")
    
    def chunk_data(self, file_path: str):
        data_chunks = []
        heading_stack = []
        content = []

        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()

                # skipping empty lines
                if not line:
                    continue

                # heading check
                if line.startswith('#'):
                    # append previous content with heading stack
                    if content:
                        data_chunks.append({
                            'heading_stack': ', '.join(heading_stack),
                            'content': ''.join(content)
                        })
                        # data_chunks.append((heading_stack.copy(), content.copy()))
                        content.clear()

                    heading_height = len(line) - len(line.lstrip('#'))
                    heading = line.lstrip('#').strip()

                    # adjusting heading stack
                    while len(heading_stack) >= heading_height:
                        heading_stack.pop()
                    heading_stack.append(heading)

                # content
                else:
                    content.append(line.strip())

        return data_chunks


    def get_knowledge_base(self):
        knowledge_base = []
        for file in os.listdir(self.__output_dir):
            if file.endswith(".md"):
                file_path = os.path.join(self.__output_dir, file)
                data_chunks = self.chunk_data(file_path)
                knowledge_base.extend(data_chunks)
        return knowledge_base

if __name__ == "__main__":
    OUTPUT_DIR = "./assets/cheatsheets"
    API_URL = "https://api.github.com/repos/OWASP/CheatSheetSeries/contents/cheatsheets"
    knowledge = Knowledge(output_dir=OUTPUT_DIR)
    try:
        knowledge.download_md_files(api_url=API_URL)
    except Exception as e:
        print(e)
        