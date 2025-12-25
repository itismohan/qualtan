from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

class SecurityAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4.1-mini")

    def generate_security_scenarios(self, api_spec):
        """Generates security-focused test scenarios (SQLi, XSS, Auth bypass)."""
        template = """
        Based on the following API specification, generate security test scenarios.
        API Spec: {spec}
        
        Focus on:
        - Authentication and Authorization bypass
        - Input validation (SQL Injection, XSS)
        - Sensitive data exposure
        - Rate limiting
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm
        return chain.invoke({"spec": api_spec}).content
