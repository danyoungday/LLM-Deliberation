import os
import re
import string


def load_setup(output_dir, agents_num, num_issues):

    with open(os.path.join(output_dir, "config.txt"), "r") as f:
        agents_config_file = f.readlines()

    issue_names = string.ascii_uppercase[:26]

    agents = {}
    role_to_agents = {}
    incentive_to_agents = {}

    assert len(agents_config_file) == agents_num

    for line in agents_config_file:
        agent_game_name, file_name, role, incentive, model = line.split(",")
        model = model.strip()
        agents[agent_game_name] = {
            "file_name": file_name,
            "role": role,
            "incentive": incentive,
        }
        if not role in role_to_agents:
            role_to_agents[role] = []
        if not incentive in incentive_to_agents:
            incentive_to_agents[incentive] = []
        role_to_agents[role].append(agent_game_name)
        incentive_to_agents[incentive].append(agent_game_name)

    for agent in agents:
        scores = {}
        with open(
            os.path.join(output_dir, "scores_files", agents[agent]["file_name"])
            + ".txt",
            "r",
        ) as f:
            Lines = f.readlines()
            assert len(Lines) == num_issues + 1
            for i, line in enumerate(Lines):
                if i == len(Lines) - 1:  # min thresholds
                    scores["min"] = int(line.strip())
                    break
                scores[issue_names[i]] = [int(num.strip()) for num in line.split(",")]
        agents[agent]["scores"] = scores

    for role in role_to_agents:
        if len(role_to_agents[role]) == 1:
            role_to_agents[role] = role_to_agents[role][0]

    for incentive in incentive_to_agents:
        if len(incentive_to_agents[incentive]) == 1:
            incentive_to_agents[incentive] = incentive_to_agents[incentive][0]

    return agents, role_to_agents, incentive_to_agents


def calculator(scores, deal, num_issues=5):
    if len(deal) != num_issues:
        return 0
    deal_sum = 0
    for issue in deal:
        if issue == "" or len(issue) != 2:
            return 0
        issue, number = issue[0], int(issue[1])
        if issue not in scores:
            return 0
        deal_sum += scores[issue][number - 1]
    return deal_sum


def extract_deal(answer, num_issues=5):
    answer = answer.replace("\n", "")
    issue_names = string.ascii_uppercase[:26]
    deal = []
    issues_suggested = 0
    for i in range(0, num_issues):
        option = re.findall(f"{issue_names[i]}[1-9]", answer, re.DOTALL)
        deal.append(option[0]) if option else deal.append("")
        if option:
            issues_suggested += 1

    return deal, issues_suggested
