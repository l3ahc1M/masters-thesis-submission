

## Create System documentation embedding
if False:
    from chroma_handler import ChromaDB
    from system_documentation import APIDocumentation, DBDocumentation, BusinessObjectDescription

    APIDocumentation.instanciate_from_json_list()
    DBDocumentation.instanciate_from_list()
    BusinessObjectDescription.instanciate_from_list()

    for documentation in APIDocumentation.all:
        print(f"Processing file: {documentation.file_name}")
        documentation.create_swagger_chunks()
        for chunk in documentation.get_chunks():
            chroma_client = ChromaDB()
            chroma_client.add_embedding_to_db(str(chunk), documentation.get_file_name(), documentation.get_business_object_name(), "API")

    for documentation in DBDocumentation.all:
        print(f"Processing file: {documentation.file_name}")
        chroma_client = ChromaDB()
        chroma_client.add_embedding_to_db(documentation.get_db_description(), documentation.get_file_name(), documentation.get_business_object_name(), "DB")

    for documentation in BusinessObjectDescription.all:
        print(f"Processing file: {documentation.file_name}")
        chroma_client = ChromaDB()
        chroma_client.add_embedding_to_db(documentation.get_business_object_description(), documentation.get_file_name(), documentation.get_business_object_name(), "TXT")

## run and evaluate tests
if True:
    import yaml
    import os
    from support_functions import SupportFunctions
    from testcase import APITestcase, SQLTestcase, Testcase
    from evaluation import Evaluation


    APITestcase.instantiate_from_raw_test_case()
    SQLTestcase.instantiate_from_raw_test_case()

    test_evaluation_folder = SupportFunctions.get_next_result_folder("test_runs")
    error_folder = os.path.join(test_evaluation_folder, "ERROR")
    
    # run test case
    i = 1

    with open('config.yaml', 'r') as f:
        cfg = yaml.safe_load(f)

    if cfg.get('process_orchestration').get('rag_framework') == "RAG":
        from rag_framework_rag import RAGProcess

        for test_case in Testcase.all:
            try:
                print(f"Processing test case {i}/{len(Testcase.all)}")
                test_run = RAGProcess(test_case)
                test_run.generate_response() 
            except Exception as e:
                print(f"[ERROR] Test case {i} failed during RAG run: {e}")
                try:
                    setattr(test_case, "error", f"RAG run failed: {e}")
                    test_case.save_to_json(error_folder, i)
                except Exception as inner_e:
                    print(f"[ERROR] Failed to save error JSON for test case {i}: {inner_e}")
            finally:
                i += 1

    if cfg.get('process_orchestration').get('rag_framework') == "SelfRAG":
        from rag_framework_selfrag import SelfRAGProcess
        for test_case in Testcase.all:
            try:
                print(f"Processing test case {i}/{len(Testcase.all)}")
                test_run = SelfRAGProcess(test_case)
                test_run.generate_response()
            except Exception as e:
                print(f"[ERROR] Test case {i} failed during Self-RAG run: {e}")
                try:
                    setattr(test_case, "error", f"Self-RAG run failed: {e}") # type:ignore
                    test_case.save_to_json(error_folder, i) # type: ignore
                except Exception as inner_e:
                        print(f"[ERROR] Failed to save error JSON for test case {i}: {inner_e}")
            finally:
                i += 1
        


    if cfg.get('process_orchestration').get('rag_framework') == "CoRAG":
        from rag_framework_corag import CoRAGProcess
        for test_case in Testcase.all:
            try:
                print(f"Processing test case {i}/{len(Testcase.all)}")
                test_run = CoRAGProcess(test_case)
                test_run.generate_response()
            except Exception as e:
                print(f"[ERROR] Test case {i} failed during CoRAG run: {e}")
                try:
                    setattr(test_case, "error", f"CoRAG run failed: {e}") # type: ignore
                    test_case.save_to_json(error_folder, i) # type: ignore
                except Exception as inner_e:
                        print(f"[ERROR] Failed to save error JSON for test case {i}: {inner_e}")
            finally:
                i += 1

    # evaluate results
    print("Evaluating api test cases...")
    for api_test_case in APITestcase.all:
        try:
            api_test_case.clean_output(api_test_case.get_reference_output(), 'Reference')
            api_test_case.clean_output(api_test_case.get_test_output(), 'Test')
            api_evaluation = Evaluation(api_test_case)
            api_evaluation.perform_component_matching(api_test_case.get_cleaned_reference_output(), api_test_case.get_cleaned_test_output(), APITestcase.api_components)
            api_evaluation.perform_exact_matching()
            api_test_case.execut_api_request()
        
        except Exception as e:
            print(f"[ERROR] API testcase evaluation failed: {e}")
            try:
                setattr(api_test_case, "error", f"API evaluation failed: {e}")
                api_test_case.save_to_json(error_folder)
            except Exception as inner_e:
                print(f"[ERROR] Failed to save error JSON for API testcase: {inner_e}")
        finally:
            continue

    print("Evaluating sql test cases...")

    for sql_test_case in SQLTestcase.all:
        try:
            sql_test_case.clean_output(sql_test_case.get_reference_output()['sql'], 'Reference')
            sql_test_case.clean_output(sql_test_case.get_test_output(), 'Test')
            sql_evaluation = Evaluation(sql_test_case)
            sql_evaluation.perform_component_matching(sql_test_case.get_cleaned_reference_output(), sql_test_case.get_cleaned_test_output(), SQLTestcase.sql_components)
            sql_evaluation.perform_exact_matching()
            sql_test_case.execute_sql_query()
        except KeyError as e:
            print(f"[ERROR] SQL testcase missing expected keys: {e}")
            try:
                setattr(sql_test_case, "error", f"SQL evaluation failed (KeyError): {e}")
                sql_test_case.save_to_json(error_folder)
            except Exception as inner_e:
                print(f"[ERROR] Failed to save error JSON for SQL testcase: {inner_e}")
        except Exception as e:
            print(f"[ERROR] SQL testcase evaluation failed: {e}")
            try:
                setattr(sql_test_case, "error", f"SQL evaluation failed: {e}")
                sql_test_case.save_to_json(error_folder)
            except Exception as inner_e:
                print(f"[ERROR] Failed to save error JSON for SQL testcase: {inner_e}")
        finally:
            continue
    print("Storing results...")
    # store results
    i = 1
    for test_case in Testcase.all:
        try:
            test_case.save_to_json(test_evaluation_folder, i)
        except Exception as e:
            print(f"[ERROR] Saving testcase {i} failed: {e}")
            try:
                setattr(test_case, "error", f"Saving to results failed: {e}")
                test_case.save_to_json(error_folder, i)
            except Exception as inner_e:
                print(f"[ERROR] Failed to save error JSON for testcase {i}: {inner_e}")
        finally:
            i += 1
    try: 
        Testcase.generate_overview(test_evaluation_folder)
    except Exception as e:
        print(f"[WARN] Could not generate overview due to error: {e}")
 

    