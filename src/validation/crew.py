from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class Validation():
    """Validation crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def rubric_grader(self) -> Agent:
        return Agent(
            config=self.agents_config['rubric_grader'], # type: ignore[index]
            verbose=True
        )

    # @agent
    # def feedback_writer(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['feedback_writer'], # type: ignore[index]
    #         verbose=True
    #     )

    # @agent
    # def parent_messenger(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['parent_messenger'], # type: ignore[index]
    #         verbose=True
    #     )

    # @agent
    # def report_architect(self) -> Agent:
    #     return Agent(
    #         config=self.agents_config['report_architect'], # type: ignore[index]
    #         verbose=True
    #     )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def grade_responses_task(self) -> Task:
        return Task(
            config=self.tasks_config['grade_responses_task'], # type: ignore[index]
        )

    # @task
    # def generate_feedback_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['generate_feedback_task'], # type: ignore[index]
    #         output_file='report.md'
    #     )

    # @task
    # def summarize_for_parent_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['summarize_for_parent_task'], # type: ignore[index]
    #         output_file='report.md'
    #     )

    # @task
    # def finalize_report_task(self) -> Task:
    #     return Task(
    #         config=self.tasks_config['finalize_report_task'], # type: ignore[index]
    #         output_file='report.md'
    #     )

    @crew
    def crew(self) -> Crew:
        """Creates the Validation crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
