from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from core.xray_client import XRayClient
from core.config import Config

class XRayAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4.1-mini")
        self.client = XRayClient()

    def map_test_cases_to_xray(self, generated_test_cases):
        """Uses LLM to format and map generated test cases to X-Ray JSON format."""
        template = """
        Format the following test cases into the X-Ray Bulk Import JSON format.
        Ensure fields like 'testType', 'steps', and 'customFields' are correctly mapped.
        
        Test Cases: {test_cases}
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm
        formatted_json = chain.invoke({"test_cases": generated_test_cases}).content
        # In a real scenario, we would parse this JSON and call self.client.import_test_cases
        return formatted_json

    def sync_results(self, playwright_results):
        """Processes Playwright results and pushes them to X-Ray."""
        # Logic to transform Playwright JSON to X-Ray Execution JSON
        return self.client.push_results(playwright_results)
