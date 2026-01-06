from chroma_handler import ChromaDB
from llm_handler import LLMQuery

class RAGProcess:
    def __init__(self, test_case):
        self.test_case = test_case
        self.system_prompt = """Role: You will receive natural languange user queries. These queries require one of two tasks: 
- Task 1: finding corresponding data in a data in a database
- Task 2: triggering corresponding actions through REST API calls
You need to first decide which of the two tasks is required to fulfill the user query and then execute exactly this task.
Here are the two corresponding task descriptions:
Task 1: finding corresponding data in a database
Your task is to generate an SQL statement so that the user can access the required data in the database.
Restrictions to generate SQL statements: 
-  Rely exclusively on the “CONTEXT” in the section CONTEXT.
-  Use exclusively read-only queries. Do not use INSERT, UPDATE, DELETE, MERGE, CREATE, ALTER, DROP. 
Date: Assume that today is May 1st 2025
Validation: For validation, check if the SQL statement contains all relevant clauses and their respective expressions, predicates, identifiers, literals, functions, operators, subqueries, tables, keys, values/literals, columns/fields, constraints and indexes, schema and database qualifiers, etc. to generate an SQL statement so that the user can access the data in the database. 
Output: Return only a single, complete, correct and executable SQL statement. Do not generate additional text.
-----
Task 2: triggering corresponding actions through REST API calls
Your task is to generate a REST API request so that the user can perform the required action through the available API endpoints.
Restrictions to generate REST API calls:
- Rely exclusively on the “CONTEXT” in the section CONTEXT.
- Use exclusively action-triggering requests. Do not generate calls that only read or retrieve data (e.g., GET requests). Use only POST, PUT, PATCH, or DELETE requests as appropriate for performing actions.
Date: Assume that today is May 1st 2025
Validation: For validation, check if the REST API request contains all relevant components and their respective elements — endpoint, HTTP method, body — to generate a correct and executable API call so that the user can perform the intended action.
Output: Return only a single, complete, correct, and executable REST API call. Do not generate additional text. The final format must contain the following elements if relevant as key value pair in any order:
- method
- endpoint 
- body
-----
CONTEXT:"""

    def get_system_documentation(self):
        chroma = ChromaDB()
        retrieved_documentation = chroma.retrieve(self.test_case.get_user_prompt())
        if not retrieved_documentation:
            return None
        else:
            for documentation in retrieved_documentation:
                self.test_case.add_retrieved_documentation(documentation['document'])
        
    
    def generate_response(self):
        self.get_system_documentation()

        docs = self.test_case.get_retrieved_documentation()

        if not docs:
            documentation_string = ""
        else:
            documentation_string = (
                "\n" + 
                " - \n".join([item for item in self.test_case.get_retrieved_documentation()])
            )
        self.test_case.add_final_system_prompt(self.system_prompt + documentation_string)
        query = LLMQuery(self.test_case.get_final_system_prompt(), self.test_case.get_user_prompt())
        self.test_case.add_test_output(query.process())

        #raise ValueError ("You are here 5")
