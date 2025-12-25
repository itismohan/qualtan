from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import os

class PerformanceAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4.1-mini")

    def generate_locust_script(self, api_spec, load_profile="standard"):
        """Generates a Locust performance script based on API spec and load profile."""
        template = """
        Generate a Python Locust script for the following API specification.
        Load Profile: {profile}
        API Spec: {spec}
        
        Requirements:
        - Include tasks for all major endpoints.
        - Use appropriate weightage.
        - Include setup and teardown if necessary.
        - Support both REST and GraphQL if present in spec.
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm
        return chain.invoke({"spec": api_spec, "profile": load_profile}).content

    def analyze_performance_results(self, stats_csv):
        """Analyzes Locust results and suggests optimizations."""
        template = """
        Analyze the following Locust performance statistics and identify bottlenecks.
        Stats: {stats}
        
        Provide recommendations for infrastructure or code improvements.
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm
        return chain.invoke({"stats": stats_csv}).content
