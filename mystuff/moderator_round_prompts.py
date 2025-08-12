"""
Prompts for the moderator per round.
"""
from prompt_utils import build_first_slot, format_history


class ModeratorRoundPrompts:
    """
    Takes in history and constructs the slot prompt for the moderator agent.
    """
    def __init__(
        self,
        agent_name: str,
        p1_name: str,
        initial_deal: str,
        incentive: str = None,
        scratch_pad_function=None,
        window_size: int = 6,
        target_agent: str = "",
        rounds_num: int = 24,
        agents_num: int = 6,
    ):
        self.agent_name = agent_name
        self.p1_name = p1_name
        self.incentive = incentive
        self.scratch_pad_function = scratch_pad_function
        self.window_size = window_size
        self.initial_deal = initial_deal
        self.target_agent = target_agent
        self.rounds_num = rounds_num
        self.agents_num = agents_num

    def build_slot_prompt(self, history: dict, round_idx: int, other_args={}) -> str:
        """
        Constructs prompt based on history and round.
        Combines history, scratchpad, unified instructions, then plan.
        """
        first = round_idx == 0  # first round
        final_round = (
            self.rounds_num - round_idx
        ) <= self.agents_num  # final time the agent would speak
        final_vote = round_idx == self.rounds_num  # final voting session

        if (
            first and self.p1_name == self.agent_name
        ):  # start the negotiation by P1's deal
            return build_first_slot(self.initial_deal, self.p1_name)

        # get history
        history_prompt = self.get_history_input(
            history, final_round=final_round, final_vote=final_vote
        )

        # get scratchpad by incentive
        scratch_pad = ""
        if self.incentive == "cooperative":
            scratch_pad = self.cooperative_scratch_pad()
        elif self.scratch_pad_function:
            scratch_pad = self.scratch_pad_function(other_args)

        # get unified instructions about formatting
        unified_instructions = self.get_unified_instructions()

        # prompt agent to generate plan
        plan_prompt = self.get_plan_prompt(
            self.agent_name == self.p1_name, final_round, final_vote
        )

        # collate
        slot_prompt = history_prompt + scratch_pad + unified_instructions + plan_prompt

        return slot_prompt

    def get_history_input(self, history: dict, final_round: bool = False, final_vote: bool = False) -> str:
        """
        Creates the history prompt using the history data.
        """
        personalized_history, last_plan = format_history(
            self.agent_name, history, self.window_size
        )
        slot_prompt = f"The following is a chronological history of up to {self.window_size} interactions <HISTORY> {personalized_history} </HISTORY> "

        if last_plan:
            slot_prompt += f"The following are your previous plans from last interactions. You should follow them while also adjusting them according to new observations. <PREV_PLAN> {last_plan} </PREV_PLAN> "

        slot_prompt += "\n Now it is your turn to talk."

        if final_round:
            slot_prompt += " This is the final discussion session."
        elif final_vote:
            slot_prompt += " This is an official and final voting session."
        return slot_prompt

    def get_unified_instructions(self) -> str:
        """
        General instructions for the agent.
        """
        prompt = """ 
        Enclose the scratchpad between <SCRATCHPAD> and </SCRATCHPAD>. The scratchpad is secret and not seen by other parties.
        Your final answer is public and must never contain scores. Enclose your final answer after the scratchpad between <ANSWER> and </ANSWER>.
        Make your final answer very short and brief in 2-3 sentences and containing only your main proposals.
        Use options' short notations instead of long descriptions.
        Enclose the exact name of the party you propose to speak next between: <PARTY> </PARTY>. "
        """
        return prompt

    def get_plan_prompt(self, is_p1, final_round: bool, final_vote) -> str:
        """
        Planning prompt.
        """
        plan_prompt = ""
        if not final_round:
            plan_prompt = """ 
            After the final answer, building on your current move and analysis,
            briefly write down short notes for yourself of what exact options you can explore the next time you speak.
            Enclose the notes between <PLAN> and </PLAN>. """
        return plan_prompt

    def cooperative_scratch_pad(self) -> str:
        """
        Scratchpad prompt.
        """
        scratch_pad = """ 
        Please use a scratchpad to show intermediate calculations and explain yourself and why you are choosing a certain party to speak next. 
        In your scratchpad, 
            1) think about what others may prefer,
            2) Based on others' preferences and history and your notes, propose one party to speak so that it balances all scores and accommodates others and is more likely to lead to an agreement. 

        You must follow these important negotiation guidelines in all your suggestions:
        Make sure all parties speak and have a chance to express their preferences.
        Aim for a balanced agreement considering all parties' interests.
        Show flexibility and openness to accommodate others' preferences.
        Express your objectives clearly and actively listen to others.
        Empathize with other parties' concerns to foster rapport.
        Focus on common interests to create a win-win situation.
        It is very important for you that they all reach an agreement and their minimum scores are met."""

        return scratch_pad
