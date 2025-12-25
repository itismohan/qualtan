import os
from jira import JIRA
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

class JiraAgent:
    def __init__(self):
        self.jira_url = os.getenv("JIRA_URL")
        self.jira_user = os.getenv("JIRA_USER")
        self.jira_token = os.getenv("JIRA_TOKEN")
        self.client = JIRA(server=self.jira_url, basic_auth=(self.jira_user, self.jira_token)) if self.jira_url else None
        self.llm = ChatOpenAI(model="gpt-4.1-mini")

    def get_story_details(self, issue_key):
        """Extracts story details from JIRA."""
        if not self.client:
            return {"key": issue_key, "summary": "Sample Story", "description": "Sample Description"}
        
        issue = self.client.issue(issue_key)
        return {
            "key": issue.key,
            "summary": issue.fields.summary,
            "description": issue.fields.description,
            "acceptance_criteria": getattr(issue.fields, 'customfield_10100', 'No AC provided') # Example custom field
        }

    def analyze_story(self, story_data):
        """Uses LLM to summarize and identify key testing areas."""
        template = """
        Analyze the following JIRA story and identify key testing areas, edge cases, and data requirements.
        
        Summary: {summary}
        Description: {description}
        Acceptance Criteria: {ac}
        
        Provide a structured analysis.
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm
        response = chain.invoke({
            "summary": story_data['summary'],
            "description": story_data['description'],
            "ac": story_data.get('acceptance_criteria', 'N/A')
        })
        return response.content
