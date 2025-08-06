"""
Moderator class for managing who talks next.
"""
import re

from openai import OpenAI

from mystuff.moderator_initial_prompt import ModeratorInitialPrompt
from mystuff.moderator_round_prompts import ModeratorRoundPrompts


class Moderator:
    """
    Similar to the basic agent class but ripped some of the stuff out.
    The moderator determines who talks next.
    TODO: For now it doesn't do history.
    """
    def __init__(
        self,
        initial_prompt_cls: ModeratorInitialPrompt,
        round_prompt_cls: ModeratorRoundPrompts,
        agent_name: str,
        temperature: float,
        model: str,
        rounds_num=24,
        agents_num=6,
    ):
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

    def execute_round(self, answer_history: dict, round_idx: int) -> tuple[str, str]:
        """
        Runs a round of the moderator agent using the stored slot prompt and history.
        Then passes the parsed prompt into the agent.
        """
        slot_prompt = self.round_prompt_cls.build_slot_prompt(answer_history, round_idx)
        agent_response = self.prompt("user", slot_prompt)
        return slot_prompt, agent_response

    def prompt(self, role: str, msg: str):
        """
        Prompts the agent with the message and returns the response.
        """
        messages = self.messages + [{"role": role, "content": msg}]
        response = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=self.temperature
        )
        return response.choices[0].message.content

    def get_next_speaker(self, agent_response: str) -> str:
        """
        Uses regex to extract the next speaker's name from the agent's response.
        Can error for now for debugging purposes. Otherwise should probably default to p1 in the future.
        """
        # Use regex to find text between <PARTY> and </PARTY>
        next_speaker = re.search(r"<PARTY>(.*?)</PARTY>", agent_response)
        if next_speaker:
            return next_speaker.group(1)
        raise ValueError("Next speaker not found in the response.")
