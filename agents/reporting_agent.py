from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

class ReportingAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4.1-mini")

    def generate_executive_summary(self, test_results):
        """Generates a high-level executive summary from raw test results."""
        template = """
        Summarize the following test execution results for a stakeholder report.
        Results: {results}
        
        Include:
        - Pass/Fail rate
        - Critical failures
        - Risk assessment
        - Recommendations for the next sprint
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm
        return chain.invoke({"results": test_results}).content
