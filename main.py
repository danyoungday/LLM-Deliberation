"""
Main interface to run the negotiation experiment.
"""
import argparse
import os
import shutil

from agent import Agent
from initial_prompts import InitialPrompt
from mystuff.moderator_agent import Moderator
from mystuff.moderator_initial_prompt import ModeratorInitialPrompt
from mystuff.moderator_round_prompts import ModeratorRoundPrompts
from rounds import RoundPrompts
from save_utils import create_outfiles, save_conversation
from utils import load_setup, randomize_agents_order, set_constants


def run_command_line():
    """
    Main command line logic for running the negotiation experiment.
    """
    parser = argparse.ArgumentParser(description="big negotiation!!")

    parser.add_argument(
        "--moderator",
        action="store_true",
        help="Use the moderator to select the next speaker.",
    )

    parser.add_argument("--temp", type=float, default="0")

    parser.add_argument("--agents_num", type=int, default=6)
    parser.add_argument("--issues_num", type=int, default=5)
    parser.add_argument("--rounds_num", type=int, default=24)
    parser.add_argument("--window_size", type=int, default=6)


    parser.add_argument("--output_dir", type=str, default="./output/")
    parser.add_argument("--game_dir", type=str, default="./games_descriptions/base")
    parser.add_argument("--exp_name", type=str, default="all_greedy")

    # if restart, specifiy output_file to continue on
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--output_file", type=str, default="history.json")

    # if any gemini model, set this true
    parser.add_argument("--gemini", action="store_true")
    parser.add_argument("--gemini_project_name", type=str, default="")
    parser.add_argument("--gemini_loc", type=str, default="")
    parser.add_argument("--gemini_model", type=str, default="gemini-1.0-pro-001")

    # if any open-source model, set this true
    parser.add_argument("--hf_home", type=str, default="/disk1/")

    # for GPTs and using Azure APIs, set this true
    parser.add_argument("--azure", action="store_true")
    parser.add_argument("--azure_openai_api", default="", help="azure api")
    parser.add_argument("--azure_openai_endpoint", default="", help="azure endpoint")

    # for GPTs and OpenAI APIs, set key
    parser.add_argument(
        "--api_key", type=str, default="", help="OpenAI key, set if using OpenAI APIs"
    )


    args = parser.parse_args()

    # SET AZURE, OpenAI and GEMINI APIs env variables
    set_constants(args)

    run_experiment(
        args.exp_name,
        moderator=args.moderator,
        temp=args.temp,
        agents_num=args.agents_num,
        rounds_num=args.rounds_num,
        issues_num=args.issues_num,
        window_size=args.window_size,
        output_dir=args.output_dir,
        game_dir=args.game_dir,
        restart=args.restart,
        output_file=args.output_file
    )


def run_experiment(
    exp_name: str,
    moderator: bool = False,
    temp: float = "0",
    agents_num: int = 6,
    rounds_num: int = 24,
    issues_num: int = 5,
    window_size: int = 6,
    output_dir: str = "./output/",
    game_dir: str = "./games_descriptions/base",
    restart: bool = False,
    output_file: str = "history.json",
    verbose: bool = True
):
    """
    Runs the experiment with the given parameters.
    moderator: whether or not to use an agent to moderate, otherwise agents take turns in random order each round
    """
    OUTPUT_DIR = os.path.join(game_dir, output_dir, exp_name)

    # Create output file, or load files if restart is given to continue on last experiments
    agent_round_assignment, start_round_idx, history = create_outfiles(restart, output_file, OUTPUT_DIR)

    # Dump config file and scores in OUTPUT_DIR
    shutil.copyfile(
        os.path.join(game_dir, "config.txt"), os.path.join(OUTPUT_DIR, "config.txt")
    )
    shutil.copytree(
        os.path.join(game_dir, "scores_files"),
        os.path.join(OUTPUT_DIR, "scores_files"),
        dirs_exist_ok=True,
    )

    # Load setups of agents from config file. File should contain names, file names, roles, incentives, and models
    # Also load initial deal file and return a dict of role to agent names
    agents, initial_deal, role_to_agent_names = load_setup(game_dir, agents_num)

    # Load HF models
    hf_models = {}


    # Instaniate agents (initial prompt, round prompt, agent class)
    for name, agent in agents.items():
        # if "hf" in agent["model"] and not agent["model"] in hf_models:
        #     hf_models[agent["model"]] = setup_hf_model(
        #         agent["model"].split("hf_")[-1], cache_dir=args.hf_home
        #     )

        inital_prompt_agent = InitialPrompt(
            game_dir,
            name,
            agent["file_name"],
            role_to_agent_names["p1"],
            role_to_agent_names["p2"],
            num_issues=issues_num,
            num_agents=agents_num,
            incentive=agent["incentive"],
        )

        round_prompt_agent = RoundPrompts(
            name,
            role_to_agent_names["p1"],
            initial_deal,
            incentive=agent["incentive"],
            window_size=window_size,
            target_agent=role_to_agent_names.get("target", ""),
            rounds_num=rounds_num,
            agents_num=agents_num,
        )

        agent_instance = Agent(
            inital_prompt_agent,
            round_prompt_agent,
            name,
            temp,
            model=agent["model"],
            # azure=args.azure,
            azure=False,
            hf_models=hf_models,
        )
        agent["instance"] = agent_instance

    # Initialize moderator agent
    if moderator:
        initial_prompt_moderator = ModeratorInitialPrompt(
            None,
            None,
            None,
            role_to_agent_names["p1"],
            role_to_agent_names["p2"],
            issues_num,
            agents_num,
            incentive="cooperative",
        )
        round_prompt_moderator = ModeratorRoundPrompts(
            None,
            role_to_agent_names["p1"],
            initial_deal,
            "cooperative",
            window_size=window_size,
            rounds_num=rounds_num,
            agents_num=agents_num,
        )
        moderator_agent = Moderator(
            initial_prompt_moderator,
            round_prompt_moderator,
            "Moderator",
            temp,
            "gpt-4.1",
        )

        # Create moderator history
        _, _, moderator_history = create_outfiles(False, "moderator-history.json", OUTPUT_DIR)

    # If not restart, agent_round_assignment is empty, then randomize order
    if not restart:
        agent_round_assignment = randomize_agents_order(
            agents, role_to_agent_names["p1"], rounds_num
        )

    for round_idx in range(start_round_idx, rounds_num):
        if round_idx == 0:
            # For first round, initialize with p1 suggesting the first deal from 'initial_deal.txt' file
            current_agent = role_to_agent_names["p1"]
            slot_prompt, agent_response = agents[current_agent]["instance"].execute_round(
                history["content"], round_idx
            )
            history = save_conversation(
                history,
                current_agent,
                agent_response,
                slot_prompt,
                round_assign=agent_round_assignment,
                initial=True,
            )
            if verbose:
                print("=====")
                print(f"{current_agent} response: {agent_response}")

        # Continue with rounds
        # Get next agent
        if moderator:
            moderator_slot_prompt, moderator_response = moderator_agent.execute_round(
                history["content"], round_idx
            )
            # TODO: For now we don't save the moderator's response in the history.
            # history = save_conversation(history, "Moderator", agent_response, slot_prompt, agent_round_assignment)
            current_agent = moderator_agent.get_next_speaker(moderator_response)
            if verbose:
                print("*****")
                print(f"Moderator: {moderator_response}")
            # Save moderator's response in its own history
            moderator_history = save_conversation(
                moderator_history,
                "Moderator",
                moderator_response,
                moderator_slot_prompt,
                initial=(round_idx == 0)
            )
        else:
            current_agent = agent_round_assignment[round_idx]
        # Query next agent
        slot_prompt, agent_response = agents[current_agent]["instance"].execute_round(
            history["content"], round_idx
        )
        history = save_conversation(history, current_agent, agent_response, slot_prompt)
        if verbose:
            print("=====")
            print(f"{current_agent} response: {agent_response}")


    # Final deal by P1
    if verbose:
        print(" ==== Deal Suggestions ==== ")
    current_agent = role_to_agent_names["p1"]
    slot_prompt, agent_response = agents[current_agent]["instance"].execute_round(
        history["content"], rounds_num
    )
    history = save_conversation(history, current_agent, agent_response, slot_prompt)
    if verbose:
        print("=====")
        print(f"{current_agent} response: {agent_response}")


if __name__ == "__main__":
    run_command_line()
