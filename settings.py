from cat.mad_hatter.decorators import tool, hook, plugin
from pydantic import BaseModel, Field

class StrawberryCatSettings(BaseModel):
    trigger: str = Field(
        title="The prefix that will trigger the reasoning.",
        default="Q*"
    )
    # Step 1: Context Analysis
    problem_analysis_prompt: str = Field(
        title="Analyse the problem",
        default="""Slow down. Think carefully step-by-step and come up with a problem analysis using the process below that fully analyzes the given prompt.
    
    Process:
    - Define the problem space and constraints
    - Identify key variables and their relationships
    - Determine evaluation criteria for success

    Format your analysis following this blueprint:
    **Problem space and constraints**:
    (Succinctly define the problem space and constraints)
    **Key variables and their relationships**:
    (Identify key variables and their relationships)
    **Success criteria**:
    (Determine evaluation criteria for success)
    
    Prompt:
            {user_prompt}
    
    Problem Analysis:
        """
    )
    # Step 2: Strategy planning
    strategy_planning_prompt: str = Field(
        title="Strategy planning",
        default="""Slow down. Think carefully step-by-step and brainstorm 3 distinct strategies for solving this problem space:
        {problem_analysis_result}
        
        Strategies: """
    )
    # Step 3: Select Strategy
    select_strategy_prompt: str = Field(
        title="Strategy Selection",
        default="""Take your time to pick a strategy that will best solve the problem space. After you pick one, write it out exactly.
        Problem Space: {problem_analysis_result}
        Strategies to choose from:
        {strategy_planning_result}
        Write out all the text of the chosen plan: """
    )


    # Step 4: Tactical breakdown
    tactical_breakdown_prompt: str = Field(
        title="Tactical breakdown",
        default="""Given the problem space and strategy to solve it, create a list of tactical tasks to follow that will solve the problem.
        Do NOT solve the proble, ONLY create the tasks to be followed.
        Problem space: {problem_analysis_result}
        Strategy: {select_strategy_result}
        Tactical tasks:"""
    )

    # Step 5: Final Answer
    final_answer_prompt: str = Field(
        title="Answering",
        default="""Follow the given steps to solve the given problem.
        Problem: {user_prompt}
        Steps: {tactical_breakdown_result}
        Final answer:"""
    )
     # Step 6: Final check
    final_check_prompt: str = Field(
            title="Final check",
            default="""check your answer: {final_answer_result} to this problem: {user_prompt} and avoid lack of attention to detail and lack of pattern recognition."""
        )   
    # Reasoning Display Option
    show_reasoning: bool = Field(
        default=True,
        description="If On, the answer will include the full reasoning."
    )
@plugin
def settings_model():
    return StrawberryCatSettings
