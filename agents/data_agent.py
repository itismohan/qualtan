from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

class DataAgent:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4.1-mini")

    def generate_test_data(self, schema, count=5):
        """Generates synthetic test data based on a schema or description."""
        template = """
        Generate {count} rows of synthetic test data in JSON format based on the following schema.
        Schema: {schema}
        
        Ensure the data is realistic and covers edge cases (nulls, long strings, special characters).
        """
        prompt = PromptTemplate.from_template(template)
        chain = prompt | self.llm
        return chain.invoke({"schema": schema, "count": count}).content
