"""
Runs an experiment multiple times with the given parameters so we can do statistical significance.
"""
from main import run_experiment


def run_n_times(exp_name: str, n: int, moderator: bool):
    """
    Runs the experiment n times with fixed parameters.
    """
    for i in range(n):
        print(f"Running experiment: {exp_name}-trial-{i}")
        run_experiment(
            exp_name=f"{exp_name}-trial-{i}",
            moderator=moderator,
            temp="0",
            agents_num=6,
            rounds_num=24,
            issues_num=5,
            window_size=6,
            output_dir=f"./output/{exp_name}/",
            verbose=False
        )


def baseline_vs_simple_moderator():
    """
    Runs the baseline and simple moderator 10x
    """
    run_n_times("baseline-repeats", 10, moderator=False)
    run_n_times("moderator-repeats", 10, moderator=True)


if __name__ == "__main__":
    baseline_vs_simple_moderator()