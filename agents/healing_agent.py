from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

class HealingAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4.1-mini")

    def analyze_failure(self, error_log, script_content, html_snapshot=None):
        """Analyzes a test failure and suggests a fix."""
        template = """
        A Playwright test failed. Analyze the error and the script to suggest a fix.
        If an HTML snapshot is provided, use it to find better selectors (Self-Healing).
        
        Error Log: {error}
        Script Content: {script}
        HTML Snapshot: {html}
        
        Provide the corrected code snippet and an explanation of the fix.
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm
        return chain.invoke({
            "error": error_log,
            "script": script_content,
            "html": html_snapshot or "Not provided"
        }).content
