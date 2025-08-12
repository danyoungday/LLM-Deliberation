"""
Coordinator initial prompt builder.
"""


class ModeratorInitialPrompt:
    """
    Initial prompt building class for the moderator agent.
    """

    def __init__(
        self,
        game_description_dir,
        agent_game_name,
        agent_file_name,
        p1: str,
        p2: str,
        num_issues: int = 5,
        num_agents: int = 6,
        incentive: str = "cooperative",
        incentive_function=None,
    ):
        """
        p1: who is the p1 agent
        p2: who is the p2 agent
        num_issues: number of issues in the negotiation paramter
        num_agents: number of agents negotiating
        """
        self.incentive = incentive
        self.incentive_fn = incentive_function
        self.p1 = p1
        self.p2 = p2

        self.agent_game_name = "Moderator"
        self.global_instructions = self.load_global_instructions(
            "mystuff/moderator_global_instructions.txt"
        )

        self.num_issues = num_issues
        self.num_agents = num_agents

        self.initial_prompt = self.build_initial_prompt()

    def return_initial_prompt(self) -> str:
        """
        Main method to be called, returns the initial prompt to go into the agent.
        """
        return self.initial_prompt

    def load_global_instructions(self, file: str) -> str:
        """
        Load global instructions from file and replace agent name placeholder.
        """
        with open(file, "r", encoding="utf-8") as f:
            global_instructions = f.read()
        global_instructions = global_instructions.replace(
            f'"{self.agent_game_name}"',
            f'"{self.agent_game_name}" (represented by you)',
        )
        return global_instructions

    def get_voting_rules(self) -> str:
        """
        Voting rules component.
        """
        voting_rules = """
        Voting rules:
        - Parties interact with each other by taking turns to speak.
        - Parties only have a limited number of interactions, then the negotiation ends even if no agreement is reached.
        """
        voting_rules += f"- Finally, {self.p1} will consolidate all suggestions and pass a formal proposal for a test vote. "
        return voting_rules

    def cooperative_incentive_rules(self) -> str:
        """
        Incentive rules component.
        """
        incentive_rules = """
        - The max score a party can achieve is 100. However, any deal with a score higher than their minimum threshold is preferable to them than no deal. They are very open to any compromise to achieve that
        """
        # incentive_rules += f'- Ensuring "{self.p1}"\'s and "{self.p2}"\'s approval is crucial because they have veto power. Focus on keys issues that appeal to them. '
        incentive_rules += f"\n\t- The proposal will pass if at least {self.num_agents-1} parties agree (must include {self.p1} and the {self.p2}). Your score will be this final deal's score. "
        return incentive_rules

    def build_initial_prompt(self) -> str:
        """
        Constructs the initial prompt for the moderator.
        """
        # These are unified rules for all agents
        voting_rules = self.get_voting_rules()

        # These are incentive-related rules
        incentive_rules = self.cooperative_incentive_rules()

        final_initial_prompt = (
            self.global_instructions + "\n" + voting_rules + incentive_rules
        )

        return final_initial_prompt
