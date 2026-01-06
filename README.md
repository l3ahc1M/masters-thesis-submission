config.yaml to configure the processes 

main.py to 
- create new chroma embedding (can be toggled)
- execute test cases (can be toggled)
  ! configuration in config.yaml needs to be checked
  ! prompts in the respective rag variant (rag_framework_rag.py/rag_framework_selfrag.py/rag_framework_corag.py) need to be adjusted per task

rag_framework_rag.py/rag_framework_selfrag.py/rag_framework_corag.py orchestrate the respective rag variant

evaluation.py: component match is depritated and not used for the thesis (it does not work properly, if order inside a component is mixed up)
