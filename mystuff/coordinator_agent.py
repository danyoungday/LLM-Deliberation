import re

from openai import OpenAI


class Coordinator:
    def __init__(self, initial_prompt_cls, round_prompt_cls, agent_name, temperature, model, rounds_num=24, agents_num=6):
        self.model = model

        self.agent_name = agent_name        
        self.temperature = temperature
        self.initial_prompt_cls = initial_prompt_cls 
        self.rounds_num = rounds_num 
        self.agents_num = agents_num

        self.initial_prompt = initial_prompt_cls.return_initial_prompt()
        self.round_prompt_cls = round_prompt_cls
        self.messages = [{"role": "user", "content": self.initial_prompt}]

        self.client = OpenAI()

    def execute_round(self, answer_history, round_idx):
        slot_prompt = self.round_prompt_cls.build_slot_prompt(answer_history,round_idx) 
        agent_response = self.prompt("user", slot_prompt)    
        return slot_prompt, agent_response

    def prompt(self, role, msg):
        messages = self.messages + [ {"role": role, "content": msg} ]
        response = self.client.chat.completions.create(
        model=self.model, 
        messages=messages,
        temperature=self.temperature 
        )
        return response.choices[0].message.content
    
    def get_next_speaker(self, agent_response):
        """
        Uses regex to extract the next speaker's name from the agent's response.
        Can error for now for debugging purposes. Otherwise should probably default to p1 in the future.
        """
        # Use regex to find text between <PARTY> and </PARTY>
        next_speaker = re.search(r'<PARTY>(.*?)</PARTY>', agent_response)
        if next_speaker:
            return next_speaker.group(1)
        raise ValueError("Next speaker not found in the response.")
