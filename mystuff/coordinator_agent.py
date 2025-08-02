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

    from save_utils import create_outfiles

    class FakeArgs:
        def __init__(self):
            self.restart = False
            self.output_file = "temp_history.json"
    args = FakeArgs()
    OUTPUT_DIR = "./temp"
    agent_round_assignment, start_round_idx, history  = create_outfiles(args, OUTPUT_DIR)

    from mystuff.coordinator_round_prompts import CoordinatorRoundPrompts
    round_prompt_agent = CoordinatorRoundPrompts("Moderator", role_to_agent_names['p1'],initial_deal,\
                                    incentive="collaborative",
                                    rounds_num=24, agents_num=6) 
    print(round_prompt_agent.build_slot_prompt(history["content"], start_round_idx))

if __name__ == "__main__":
    test()