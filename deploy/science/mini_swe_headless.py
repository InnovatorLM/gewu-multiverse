"""Select upstream's noninteractive agent for bounded Harbor batch jobs."""


def configure_headless_mini_swe(job):
    """Mutate only the mini-SWE agent class; retain budgets and task settings.

    mini-SWE 2.2.8's interactive agent prompts for a new budget even with
    --yolo --exit-immediately. Its default agent records LimitsExceeded and
    saves the trajectory without asking stdin. This is budget exhaustion,
    not a successful submission or scientific acceptance.
    """
    agents = job.get('agents', [])
    if len(agents) != 1 or agents[0].get('name') not in (
        'mini-swe-agent', 'mini-swe-agent-preinstall'
    ):
        raise ValueError('Expected one explicit mini-SWE Harbor agent')
    config = agents[0].setdefault('kwargs', {}).setdefault('config', {})
    config.setdefault('agent', {})['agent_class'] = 'default'
    return job
