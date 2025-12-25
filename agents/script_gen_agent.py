from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

class ScriptGenAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4.1-mini")

    def generate_playwright_script(self, gherkin_scenario, test_type="web"):
        """Generates Playwright TypeScript code for a given Gherkin scenario."""
        template = """
        Generate a Playwright TypeScript test script for the following Gherkin scenario.
        Type: {test_type} (web, rest_api, or graphql)
        Scenario: {scenario}
        
        Requirements:
        - Use Page Object Model for web tests.
        - Use 'expect' for assertions.
        - For API tests, use Playwright's request context.
        - For GraphQL, include the query/mutation structure.
        - Include necessary imports.
        - Ensure the code is clean and modular.
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm
        return chain.invoke({"scenario": gherkin_scenario, "test_type": test_type}).content

    def generate_api_client(self, swagger_or_schema):
        """Auto-generates API client methods based on schema."""
        template = """
        Based on the following API schema (Swagger/GraphQL), generate Playwright TypeScript utility methods for interacting with these endpoints.
        
        Schema: {schema}
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm
        return chain.invoke({"schema": swagger_or_schema}).content
