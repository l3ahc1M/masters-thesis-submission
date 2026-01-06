import os
import yaml
from dotenv import load_dotenv
load_dotenv()

with open('config.yaml', 'r') as f:
    cfg = yaml.safe_load(f)


class LLMQuery():
    def __init__(self, system_prompt: str, user_prompt: str):
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt

    def __open_ai(self, system_prompt=None, user_prompt=None):
        from openai import OpenAI

        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        # if no specific user_prompt and system_prompt provided, use the ones from test case
        if not system_prompt and not user_prompt:
            response = client.chat.completions.create(
                model=cfg.get('llm', {}).get('openAI_model'),
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": self.user_prompt
                    }
                ],
            )
        elif system_prompt and user_prompt:
            response = client.chat.completions.create(
                model=cfg.get('llm', {}).get('openAI_model'),
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
            )
        else:
            raise ValueError("Both system_prompt and user_prompt must be provided together.")
            
        return response.choices[0].message.content
    
    def __xai(self):
        from xai_sdk import Client
        from xai_sdk.chat import user, system
        client = Client(
            api_key=os.getenv("XAI_API_KEY"),
            timeout=3600,  
            )

        chat = client.chat.create(
            model=cfg.get('llm', {}).get('xai_model'), 
            temperature=0
            )
        chat.append(system(self.system_prompt))
        chat.append(user(self.user_prompt))

        response = chat.sample()
        return response.content
    
    def process(self, user_prompt=None, system_prompt=None):
        provider = cfg.get('llm').get('provider')
        if provider == 'openAI': 
            return self.__open_ai(user_prompt=user_prompt, system_prompt=system_prompt)
        elif provider == 'xai':
            return self.__xai()
        else:
            raise ValueError(f"Unsupported llm provider: {provider!r}. Must be 'openAI' or 'xai'.")
        
 