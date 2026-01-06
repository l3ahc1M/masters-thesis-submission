import json
import yaml
import os
import re
import time
import ast
import pandas as pd

class Testcase:
    all = []
    def __init__(
            self, 
            test_case_type, 
            business_object_name, 
            user_prompt, 
            reference_output, 
            framework, 
            llm_provider, 
            llm, 
            knowledge_basis,
            retrieved_documentation=None,
            relevant_documentation=None,
            corag_history=None,
            corag_number_of_iterations=None,
            final_system_prompt = "", 
            test_output={}, 
            cleaned_test_output = "", 
            cleaned_reference_output = "", 
            component_matching_result=[], 
            exact_match_result=None, 
            execution_result=None,
            execution_error_message = ""
        ):
        # Run validations to the received arguments
        assert test_case_type in ('SQL', 'API'), f"test_case_type must either be 'SQL' or 'API'. Received {test_case_type} instead."
        assert type(business_object_name) == str, f"business_object_name must be a string. Received {type(business_object_name)} instead."
        assert type(user_prompt) == str, f"user_prompt must be a string. Received {type(user_prompt)} instead."
        assert type(user_prompt) == str, f"user_prompt must be a string. Received {type(user_prompt)} instead."
        assert type(reference_output) == dict, f"reference_output must be of type dict. Received {type(reference_output)} instead."
        assert framework in ('RAG', 'SelfRAG', 'CoRAG') , f"framework must be in ('RAG', 'SelfRAG', 'CoRAG'). Received {framework} instead."
        assert llm_provider in ('openAI', 'xai') , f"llm_provider must be in ('openAI', 'xai'). Received {llm_provider} instead."
        assert llm in ('gpt-5', 'grok-4') , f"llm must be in ('gpt-5', 'grok-4'). Received {llm} instead."
    

        # Assign to self object
        self.test_case_type = test_case_type
        self.business_object_name = business_object_name
        self.user_prompt = user_prompt
        self.reference_output = reference_output
        self.framework = framework
        self.llm_provider = llm_provider
        self.llm = llm
        self.knowledge_basis = knowledge_basis
        self.retrieved_documentation = retrieved_documentation
        self.relevant_documentation = relevant_documentation
        self.corag_history = corag_history
        self.corag_number_of_iterations = corag_number_of_iterations
        self.final_system_prompt = final_system_prompt
        self.test_output = test_output
        self.cleaned_test_output = cleaned_test_output
        self.cleaned_reference_output = cleaned_reference_output
        self.component_matching_result = component_matching_result
        self.exact_match_result = exact_match_result
        self.execution_result = execution_result
        self.execution_error_message = execution_error_message

        # Actions to be executed
        Testcase.all.append(self)

    @classmethod
    def load_test_cases(cls, category):

        test_cases = []
        with open('config.yaml', 'r') as f:
            cfg = yaml.safe_load(f)
        test_case_folder = cfg.get('test_cases').get('source_folder')
        rag_framework = cfg.get('process_orchestration', {}).get('rag_framework')
        llm_provider = cfg.get('llm').get('provider')
        llm = cfg.get('llm').get(f'{llm_provider}_model')

        
        test_case_dir = os.path.join(test_case_folder, category)
        for subfolder in os.listdir(test_case_dir):
            subfolder_path = os.path.join(test_case_dir, subfolder)

            for filename in os.listdir(subfolder_path):
                        if filename.endswith(".json"):
                            file_path = os.path.join(subfolder_path, filename)
                            with open(file_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                                data['type'] = category
                                data['rag_framework'] = rag_framework
                                data['llm_provider'] = llm_provider
                                data['business_object_name'] = str(subfolder)
                                data['llm'] = llm
                                test_cases.append(data)
                            list(test_cases)
        return test_cases      
############################################
    @classmethod
    def generate_overview(cls, folder):
        data = []

        directory_path = os.path.join("test_runs", folder)
       
        for subdir, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(subdir, file)
                    with open(file_path, encoding="utf-8") as f:
                        raw_data = json.load(f)
                        method_has_component = False
                        method_match = False
                        endpoint_has_component = False
                        endpoint_match = False
                        body_has_component = False
                        body_match = False
                        select_has_component = False
                        select_match = False
                        from_has_component = False
                        from_match = False
                        join_has_component = False
                        join_match = False
                        on_has_component = False
                        on_match = False
                        where_has_component = False
                        where_match = False
                        group_by_has_component = False
                        group_by_match = False
                        having_has_component = False
                        having_match = False
                        order_by_has_component = False
                        order_by_match = False
                        limit_has_component = False
                        limit_match = False

                        
                        for item in raw_data.get('component_matching_result'):
                            comp = item.get('component')
                            if comp == 'method':
                                method_has_component = item.get('has_component')
                                method_match = item.get('match')
                        for item in raw_data.get('component_matching_result'):
                            comp = item.get('component')
                            if comp == 'endpoint':
                                endpoint_has_component = item.get('has_component')
                                endpoint_match = item.get('match')
                        for item in raw_data.get('component_matching_result'):
                            comp = item.get('component')
                            if comp == 'body':
                                body_has_component = item.get('has_component')
                                body_match = item.get('match')
                        for item in raw_data.get('component_matching_result'):
                            comp = item.get('component')
                            if comp == 'select':
                                select_has_component = item.get('has_component')
                                select_match = item.get('match')
                        for item in raw_data.get('component_matching_result'):
                            comp = item.get('component')
                            if comp == 'from':
                                from_has_component = item.get('has_component')
                                from_match = item.get('match')
                        for item in raw_data.get('component_matching_result'):
                            comp = item.get('component')
                            if comp == ["join", "inner join", "left join", "right join", "full join", "cross join"]:
                                join_has_component = item.get('has_component')
                                join_match = item.get('match')
                        for item in raw_data.get('component_matching_result'):
                            comp = item.get('component')
                            if comp == "on":
                                on_has_component = item.get('has_component')
                                on_match = item.get('match')
                        for item in raw_data.get('component_matching_result'):
                            comp = item.get('component')
                            if comp == "where":
                                where_has_component = item.get('has_component')
                                where_match = item.get('match')
                        for item in raw_data.get('component_matching_result'):
                            comp = item.get('component')
                            if comp == "group by":
                                group_by_has_component = item.get('has_component')
                                group_by_match = item.get('match')
                        for item in raw_data.get('component_matching_result'):
                            comp = item.get('component')
                            if comp == "having":
                                having_has_component = item.get('has_component')
                                having_match = item.get('match')
                        for item in raw_data.get('component_matching_result'):
                            comp = item.get('component')
                            if comp == "order by":
                                order_by_has_component = item.get('has_component')
                                order_by_match = item.get('match')
                        for item in raw_data.get('component_matching_result'):
                            comp = item.get('component')
                            if comp == "limit":
                                limit_has_component = item.get('has_component')
                                limit_match = item.get('match')

                        my_dict = {
                            "test_case_type": raw_data.get('test_case_type'),
                            "business_object_name": raw_data.get('business_object_name'),
                            "user_prompt": raw_data.get('user_prompt'),
                            "framework": raw_data.get('framework'),
                            "llm_provider": raw_data.get('llm_provider'),
                            "llm": raw_data.get('llm'),
                            "has method component": method_has_component,                        
                            "method match": method_match,
                            "has endpoint component": endpoint_has_component,                        
                            "endpoint match": endpoint_match,
                            "has body component": body_has_component,                        
                            "body match": body_match,
                            "has select component": select_has_component,                        
                            "select match": select_match,
                            "has from component": from_has_component,                        
                            "from match": from_match,
                            "has join component": join_has_component,                        
                            "join match": join_match,
                            "has on component": on_has_component,                        
                            "on match": on_match,
                            "has where component": where_has_component,                        
                            "where match": where_match,
                            "has group by component": group_by_has_component,                        
                            "group by match": group_by_match,
                            "has having component": having_has_component,                        
                            "having match": having_match,
                            "has order by component": order_by_has_component,                        
                            "order by match": order_by_match,
                            "limit component": limit_has_component,                        
                            "limit match": limit_match,
                            "exact_match_result": raw_data.get('exact_match_result'),
                            "execution_result": raw_data.get('execution_result'),
                            "execution_error_message": raw_data.get('execution_error_message')
                        }

                        data.append(my_dict)

        df = pd.DataFrame(data)

        # Ensure the folder exists 
        base_dir = os.path.join("test_runs", str(folder))
        os.makedirs(base_dir, exist_ok=True)

        # Write a file inside that folder
        csv_file_path = os.path.join(base_dir, "overview.csv")
        df.to_csv(csv_file_path, index=False)


##################################################
    def print_information(self):
        print(f"Test case type: {self.test_case_type}")
        print(f"User prompt: {self.user_prompt}")
        print(f"Reference output: {self.reference_output}")
        print(f"Framework: {self.framework}")
        print(f"LLM provider: {self.llm_provider}")
        print(f"LLM: {self.llm}")
        print(f"Test output: {self.test_output}")
        print(f"Component Matching result: {self.component_matching_result}")
        print(f"Exact Match result: {self.exact_match_result}")

    def __repr__(self):
        return f"{__class__.__name__}('{self.test_case_type}', '{self.user_prompt}', {self.reference_output})"
    
    def add_final_system_prompt(self, system_prompt):
        self.final_system_prompt = system_prompt

    def get_final_system_prompt(self):
        return self.final_system_prompt

    def add_retrieved_documentation(self, documentation):
        if self.retrieved_documentation is None:
            self.retrieved_documentation = []
        self.retrieved_documentation.append(documentation)

    def add_test_output(self, test_output):
        self.test_output = test_output

    def add_relevant_documentation(self, relevance_list):
        if self.relevant_documentation is None:
            self.relevant_documentation = []    
        self.relevant_documentation.append(relevance_list)
    
    def add_corag_history(self, corag_history):
        if self.corag_history is None:
            self.corag_history = []    
        self.corag_history.append(corag_history)
    
    def add_corag_number_of_iterations(self, corag_number_of_iterations):
        self.corag_number_of_iterations = corag_number_of_iterations

    def get_retrieved_documentation(self):
        return self.retrieved_documentation
    
    def get_relevant_documentation(self):
        return self.relevant_documentation
    
    def get_corag_history(self):
        return self.corag_history
    
    def get_corag_number_of_iterations(self):
        return self.corag_number_of_iterations

    def get_type(self):
            return self.test_case_type
    
    def get_user_prompt(self):
        return self.user_prompt
    
    def get_reference_output(self):
        return self.reference_output
    
    def get_framework(self):
        return self.framework
    
    def get_llm_provider(self):
        return self.llm_provider
    
    def get_llm(self):
        return self.llm
    
    def get_cleaned_reference_output(self):
        return self.cleaned_reference_output
    
    def get_cleaned_test_output(self):
        return self.cleaned_test_output
    
    def get_test_output(self):
        return self.test_output
    
    def get_component_matching_result(self):
        return self.component_matching_result 
    
    def add_component_matching_result(self, component_matching_result: list):
        self.component_matching_result = component_matching_result
    
    def get_exact_match_result(self):
        return self.exact_match_result
    
    def add_exact_match_result(self, exact_match_result):
        self.exact_match_result = exact_match_result
    
    def save_to_json(self, subfolder: str, file_appendix: int | None = None):

        # Build output directory
        base_dir = os.path.join("test_runs", subfolder)
        os.makedirs(base_dir, exist_ok=True)

        ts = int(time.time())
        safe_bo = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(self.business_object_name))
        filename = f"{self.test_case_type}_{safe_bo}_{ts}_{file_appendix}"

        file_path = os.path.join(base_dir, f"{filename}.json")

        # Prepare fully serializable payload
        payload = {
            "test_case_type": self.test_case_type,
            "business_object_name": self.business_object_name,
            "user_prompt": self.user_prompt,
            "reference_output": self.reference_output,
            "cleaned_reference_output": self.cleaned_reference_output,
            "framework": self.framework,
            "llm_provider": self.llm_provider,
            "llm": self.llm,
            "knowledge_basis": self.knowledge_basis,
            "retrieved_documentation": self.retrieved_documentation,
            "relevant_documentation": self.relevant_documentation,
            "corag_history": self.corag_history,
            "corag_number_of_iterations": self.corag_number_of_iterations,
            "final_system_prompt": self.final_system_prompt,
            "test_output": self.test_output,
            "cleaned_test_output": self.cleaned_test_output,
            "component_matching_result": self.component_matching_result,
            "exact_match_result": self.exact_match_result,
            "execution_result": self.execution_result,
            "execution_error_message": self.execution_error_message
        }

        # Write JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        return file_path

class APITestcase(Testcase):
    all = []
    api_components = [
        'method',
        'endpoint',
        'body'
    ]
    def __init__ (self, test_case_type, business_object_name, user_prompt, reference_output, framework, llm_provider, llm, knowledge_basis, test_output={}, component_matching_result=[], exact_match_result=None):
        # call to super function
        super().__init__(test_case_type, business_object_name, user_prompt, reference_output, framework, llm_provider, llm, knowledge_basis, test_output={}, component_matching_result=[], exact_match_result=None)

        # Actions to be executed
        APITestcase.all.append(self)

    @classmethod
    def instantiate_from_raw_test_case(cls):
        with open('config.yaml', 'r') as f:
            cfg = yaml.safe_load(f)  
        json_list = cls.load_test_cases('API')
        for test_case in json_list: # type: ignore
            reference_output_object = {
                "method": test_case.get("output").get("method"),
                "endpoint": test_case.get("output").get("endpoint"),
                "body": test_case.get("output").get("body"),
            }
            APITestcase(
                  test_case_type=test_case.get('type'),
                  user_prompt=test_case.get('input'),
                  reference_output=reference_output_object,
                  business_object_name=str(test_case.get('business_object_name')),
                  framework=test_case.get('rag_framework'),
                  llm_provider=test_case.get('llm_provider'),
                  llm=test_case.get('llm'),
                  knowledge_basis=cfg.get('process_orchestration').get('knowledge_basis')
            )

    def clean_json(self, text: str):
        text = str(text).strip()
        text = re.sub(r';+\s*$', '', text)  # strip trailing semicolons
        text = text.lower()
        text = text.replace("\n", " ") # replace newlines with spaces
        return text

    def clean_output(self, text, output_type):
        if output_type not in ('Reference', 'Test'):
            raise ValueError(
                "Invalid value for output_type. Expected: ('Reference', 'Test'). "
                f"Received: {output_type}"
            )

        obj = None
        if isinstance(text, (dict, list)):
            obj = text
        else:
            s = str(text).strip()

            # If the input might contain multiple lines / multiple objects,
            # pick the first JSON-ish / dict-looking chunk.
            # (Adjust if you actually want to handle multiple entries.)
            if s.startswith("Data:"):
                # drop a leading "Data:" prefix if present
                s = s[s.find("{"):].strip()

            # Try JSON first
            try:
                obj = json.loads(s)
            except json.JSONDecodeError:
                obj = ast.literal_eval(s)

        if isinstance(obj, dict) and 'body' in obj and isinstance(obj['body'], (dict, list, str)):
            cleaned_body = obj['body']
            if isinstance(cleaned_body, str):
                try:
                    cleaned_body = json.loads(cleaned_body)
                except Exception:
                    try:
                        cleaned_body = ast.literal_eval(cleaned_body)
                    except Exception:
                        pass
            obj['body'] = cleaned_body

        cleaned_json = json.dumps(obj, ensure_ascii=False)

        if output_type == 'Reference':
            self.cleaned_reference_output = cleaned_json
        elif output_type == 'Test':
            self.cleaned_test_output = cleaned_json

    def execut_api_request(self):
        import requests
        from test_cases.name_to_url import NAME_TO_URL
        
        try:
            base_url = NAME_TO_URL.get(self.business_object_name)
            if not base_url:
                raise ValueError(f"Base URL not found for subfolder: {self.business_object_name}")
            
            test_output_json = json.loads(self.test_output)

            method = test_output_json.get("method")
            endpoint = test_output_json.get("endpoint")
            body = test_output_json.get("body")
            url = f"{base_url}{endpoint}"
            
            
            if method.upper() == "GET":
                response = requests.get(url, json=body)
            elif method.upper() == "POST":
                response = requests.post(url, json=body)
            elif method.upper() == "PUT":
                response = requests.put(url, json=body)
            elif method.upper() == "DELETE":
                response = requests.delete(url, json=body)
            elif method.upper() == "PATCH":
                response = requests.patch(url, json=body)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            if response.status_code in (200, 201, 204):
                self.execution_result = True

            else:
                self.execution_result = False
                self.execution_error_message = f"{response.status_code} // {response.text}"
        
        except Exception as e:
            # Error path
            self.execution_result = False
            self.execution_error_message = str(e)
            return None


    

class SQLTestcase(Testcase):
    all = []
    sql_components = [
    'select',
    'from',
    ('join', 'inner join', 'left join', 'right join', 'full join', 'cross join'),
    'on',
    'where',
    'group by',
    'having',
    'order by',
    'limit',
    ]
    def __init__ (self, test_case_type, business_object_name, user_prompt, reference_output, framework, llm_provider, llm, knowledge_basis, test_output={}, component_matching_result=[], exact_match_result=None):
        # call to super function
        super().__init__(test_case_type, business_object_name, user_prompt, reference_output, framework, llm_provider, llm, knowledge_basis, test_output={}, component_matching_result=[], exact_match_result=None)

    
        # Actions to be executed
        SQLTestcase.all.append(self)

    @classmethod
    def instantiate_from_raw_test_case(cls):
        json_list = cls.load_test_cases('SQL')
        with open('config.yaml', 'r') as f:
            cfg = yaml.safe_load(f)
        
        for test_case in json_list: # type: ignore
            reference_output_object = {
                "sql": test_case.get("output").get("sql")
            }
            SQLTestcase(
                test_case_type=test_case.get('type'),
                user_prompt=test_case.get('input'),
                reference_output=reference_output_object,
                business_object_name=str(test_case.get('business_object_name')),
                framework=test_case.get('rag_framework'),
                llm_provider=test_case.get('llm_provider'),
                llm=test_case.get('llm'),
                knowledge_basis=cfg.get('process_orchestration').get('knowledge_basis')

            )

    def _coerce_sql(self, value, *, label):
        """
        Try to coerce various shapes (str, dict with 'sql'/'query'/'text', list/tuple)
        into a SQL string. Raise a helpful error if not possible.
        """
        if value is None:
            raise ValueError(f"{label} is None; expected a SQL string.")

        if isinstance(value, str):
            return value

        if isinstance(value, dict):
            for k in ('sql', 'query', 'text'):
                if k in value and isinstance(value[k], str):
                    return value[k]
            raise ValueError(f"{label} looks like a dict without a 'sql'/'query'/'text' string")

        if isinstance(value, (list, tuple)):
            return " ".join(map(str, value))

        return str(value)
    
    def clean_output(self, text: str, output_type):
        if output_type not in ('Reference', 'Test'):
            raise ValueError(f"Invalid value for output_type. Expected: ('Reference', 'Test'). Received: {output_type}")
        """
        Remove SQL comments:
        - line comments starting with --
        - block comments /* ... */
        Keeps string/identifier literals intact.
        """
        i = 0
        length = len(text)
        output = []
        inside_single_quote = False
        inside_double_quote = False
        inside_line_comment = False
        inside_block_comment = False

        while i < length:
            char = text[i]
            next_char = text[i+1] if i + 1 < length else ''

            # Handle line comment
            if inside_line_comment:
                if char == '\n':
                    inside_line_comment = False
                    output.append(char)
                i += 1
                continue

            # Handle block comment
            if inside_block_comment:
                if char == '*' and next_char == '/':
                    inside_block_comment = False
                    i += 2
                else:
                    i += 1
                continue

            # Inside single-quoted string
            if inside_single_quote:
                output.append(char)
                if char == "'" and next_char == "'":  # escaped quote
                    output.append(next_char)
                    i += 2
                    continue
                if char == "'":
                    inside_single_quote = False
                i += 1
                continue

            # Inside double-quoted identifier
            if inside_double_quote:
                output.append(char)
                if char == '"' and next_char == '"':  # escaped double quote
                    output.append(next_char)
                    i += 2
                    continue
                if char == '"':
                    inside_double_quote = False
                i += 1
                continue

            # Detect new comments
            if char == '-' and next_char == '-':
                inside_line_comment = True
                i += 2
                continue
            if char == '/' and next_char == '*':
                inside_block_comment = True
                i += 2
                continue

            # Detect start of string literals
            if char == "'":
                inside_single_quote = True
                output.append(char)
                i += 1
                continue
            if char == '"':
                inside_double_quote = True
                output.append(char)
                i += 1
                continue

            # Normal character
            output.append(char)
            i += 1

        cleaned = []
        for item in output:
            item = item.replace("\n", " ")
            item = item.replace("\"", " ")
            while "  " in item: 
                item.replace("  ", " ")

            cleaned.append(item)

        if output_type == 'Reference':
            self.cleaned_reference_output = ''.join(cleaned)
        
        if output_type == 'Test':
            self.cleaned_test_output = ''.join(cleaned)

    def execute_sql_query(self, db_path: str = "test_cases/dummy.db"):
        """
        Execute a SQL statement safely.
        - If it succeeds (regardless of result rows), sets:
            self.execution_result = True
            self.execution_error_message = ""
        - If it errors, sets:
            self.execution_result = False
            self.execution_error_message = <error message>
            and returns None.

        Args:
        db_path: path to SQLite db
        sql: SQL to run. If None, it tries self.test_output then self.reference_output.
            Works with str or dict({'sql': ...}) thanks to _coerce_sql().
        params: sequence of parameters for the SQL (tuple/list). Defaults to ().
        fetch: 'all' | 'one' | 'none'  (for SELECTs vs DDL/DML)

        Returns:
        - list[sqlite3.Row] for fetch='all'
        - sqlite3.Row or None for fetch='one'
        - int rowcount for fetch='none' (DDL/DML), if available
        - None if an error occurred
        """
        import sqlite3


        try:

            with sqlite3.connect(db_path) as conn:
                cur = conn.execute(self.test_output)

                rows = cur.fetchall()

            # Success path
            self.execution_result = True
            self.execution_error_message = ""
            return rows

        except Exception as e:
            # Error path
            self.execution_result = False
            self.execution_error_message = str(e)
            return None
