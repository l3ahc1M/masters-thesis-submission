
from chroma_handler import ChromaDB
from llm_handler import LLMQuery

class CoRAGProcess:
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
        original_query = self.test_case.get_user_prompt()
        sub_answers = []
        max_steps = 5 
        for step in range(max_steps):
            # Prepare system and user prompts for sub-query generation
            if step == 0:
                sub_query_system = ("""Role: You are an expert assistant for breaking down complex queries into simpler sub-queries for step-by-step retrieval. The main goal is to provide the step-by-step information to complete the 'Final task'. 
Output: 
- Analyze the user's query and provide the first sub-query needed to find information that will help answer the overall question.
- If no sub-query is needed (i.e., the question can be answered directly), respond with 'FINAL' and do not create any additional text.""")

                sub_query_user = f"User Query: {original_query}"        
            else:
                known_info_str = "\n".join([f"Sub-answer {i+1}: {ans}" for i, ans in enumerate(sub_answers)])
                sub_query_system = ("""Role: You are an support assistant required for breaking down complex queries into simpler sub-queries for step-by-step retrieval. The main goal is to provide the step-by-step information to complete the 'Final task'. From previous steps there is already 'known information' gathered, and we still need to answer the 'Original question'.

Output: 
- Based on the original question and the information gathered so far, provide the next sub-query to find the remaining information.
- If no sub-query is needed (i.e., the question can be answered directly), respond with 'FINAL' and do not create any additional text.""")

                sub_query_user = (
                    f"Original Question:\n{original_query}\n"
                    f"Known Information:\n{known_info_str}\n"
                )

            task = "\n".join(["User request: ", sub_query_user, "Final task: ", self.system_prompt])
            # Generate sub-query or final decision using LLM
            query_agent = LLMQuery(sub_query_system, task)
            sub_query = query_agent.process()
            self.test_case.add_corag_history(f"Generated sub-query at step {step+1}:{sub_query}")
            #print(f"\n*****\nGenerated sub-query at step {step+1}:\n{sub_query}\n*****")
            if sub_query is None:
                # No response from LLM (edge case)
                break
            sub_query_text = sub_query.strip()
            
            # Check if no further sub-query is needed
            if sub_query_text.upper().startswith("FINAL"):
                if step == 0:
                    # If even the first step says FINAL, do a direct retrieval on the original query
                    retrieved_docs = chroma.retrieve(original_query)
                    for doc in retrieved_docs:
                        self.test_case.add_retrieved_documentation(doc['document'])
                break  # end the chain
            
            
            # Retrieve documents for the generated sub-query
            retrieved_docs = chroma.retrieve(sub_query_text)
            if not retrieved_docs:
                # If no docs found for this sub-query, stop the chain
                break
            # Store retrieved docs from this step
            for doc in retrieved_docs:
                self.test_case.add_retrieved_documentation(doc['document'])
            
            # Use LLM to extract a concise sub-answer from the retrieved docs
            docs_content = "\n".join([doc['document'] for doc in retrieved_docs])
            sub_answer_system = (
                """You are an expert assistant tasked with extracting the specific answer to a question from provided documentation.
Using only the following documents, provide a concise answer to the sub-query."""
            )
            sub_answer_user = f"Sub-query: {sub_query_text}\nDocuments:\n{docs_content}"
            answer_agent = LLMQuery(sub_answer_system, sub_answer_user)
            sub_answer = answer_agent.process()
            #print(f"\n*****\nExtracted sub-answer at step {step+1}:\n{sub_answer}\n*****")
            if not sub_answer:
                # If LLM failed to produce an answer, stop the chain
                break
            sub_answer_text = str(sub_answer).strip()

            # store the sub-answer in corag documentation
            self.test_case.add_corag_history(sub_answer)
            

            # Add the sub-answer to our context and continue to next iteration
            sub_answers.append(sub_answer_text)

        self.test_case.add_corag_number_of_iterations(step + 1) # type: ignore

    def generate_response(self):
        # Perform the chain-of-retrieval process to gather documentation
        self.get_system_documentation()
        docs = self.test_case.get_retrieved_documentation()
        # Build the final system prompt with all retrieved context (if any)
        if not docs:
            documentation_string = ""
        else:
            documentation_string = "\n" + " - \n".join([item for item in docs])
        self.test_case.add_final_system_prompt(self.system_prompt + documentation_string)
        # Query the LLM with the full context and original user query to get the final answer
        final_query = LLMQuery(self.test_case.get_final_system_prompt(), self.test_case.get_user_prompt())
        self.test_case.add_test_output(final_query.process())
