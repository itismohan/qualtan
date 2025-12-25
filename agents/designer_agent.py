from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

class DesignerAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4.1-mini")

    def generate_gherkin(self, story_analysis):
        """Generates Gherkin feature files based on story analysis."""
        template = """
        Based on the following story analysis, generate a Gherkin feature file with multiple scenarios (Positive, Negative, Edge cases).
        
        Analysis: {analysis}
        
        Output format:
        Feature: [Feature Name]
          Scenario: [Scenario Name]
            Given ...
            When ...
            Then ...
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm
        return chain.invoke({"analysis": story_analysis}).content

    def generate_test_cases(self, gherkin_content):
        """Converts Gherkin scenarios into detailed test cases for X-Ray."""
        template = """
        Convert the following Gherkin scenarios into detailed test cases suitable for X-Ray (JIRA).
        Include: Test Summary, Pre-conditions, Steps, Expected Results, and Test Data.
        
        Gherkin: {gherkin}
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm
        return chain.invoke({"gherkin": gherkin_content}).content
