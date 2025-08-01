class Coordinator:
    def __init__(self, initial_prompt_cls, round_prompt_cls, agent_name, temperature, model, rounds_num=24, agents_num=6):
        self.model = model

        self.agent_name = agent_name        
        self.temperature = temperature
        self.initial_prompt_cls = initial_prompt_cls 
        self.rounds_num = rounds_num 
        self.agents_num = agents_num

        self.initial_prompt = initial_prompt_cls.return_initial_prompt()
        self.messages = [{"role": "user", "content": self.initial_prompt}]

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
    

def test():
    import json
    from utils import load_setup, set_constants, randomize_agents_order, setup_hf_model
    agents, initial_deal, role_to_agent_names = load_setup('./games_descriptions/base', 6)
    print(json.dumps(agents, indent=4))
    print(initial_deal)
    print(role_to_agent_names)

    from mystuff.coordinator_initial_prompt import CoordinatorInitialPrompt
    initial_prompt_agent = CoordinatorInitialPrompt('./games_descriptions/base', "Moderator", None, role_to_agent_names['p1'], role_to_agent_names['p2'])
    print(initial_prompt_agent.return_initial_prompt())

if __name__ == "__main__":
    test()