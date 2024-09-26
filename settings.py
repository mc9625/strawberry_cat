from cat.mad_hatter.decorators import tool, hook, plugin
from pydantic import BaseModel, Field

class StrawberryCatSettings(BaseModel):
    trigger: str = Field(
        title="The prefix that will trigger the reasoning.",
        default="Q*"
    )
    # Step 1: Context Analysis
    context_analysis_prompt: str = Field(
        title="Context Analysis Statement",
        default="""Please **carefully read** the problem below and **thoroughly analyze it** by:

        - Identifying all **key elements** (objects, characters, relationships, sequences of events).
        - Noting any **explicit and implicit constraints or conditions**.
        - Highlighting any **potential ambiguities or pitfalls**.
        - **Determining the exact goal** of the problem and any specific questions that need to be answered.

        Problem:
        {user_prompt}"""
    )
    # Step 2: Solution Generation
    solution_generation_prompt: str = Field(
        title="Solution Generation Statement",
        default="""Based on the thorough analysis above, **develop several specific and feasible strategies** to solve the problem. For each strategy:

        - **Explain the approach in detail**.
        - **Justify why it is suitable** given the key elements and constraints.
        - **Consider potential challenges** and how they can be addressed.

        Analysis:
        {context_analysis_result}"""
    )
    # Step 3: Select Strategy
    select_strategy_prompt: str = Field(
        title="Select Strategy Statement",
        default="""Evaluate the proposed strategies above using the following criteria:

        - **Alignment with the problem's goal and constraints**.
        - **Feasibility and practicality** of implementation.
        - **Effectiveness** in addressing all key elements.
        - **Efficiency** in reaching a solution.

        **Select the most appropriate strategy** and **provide a detailed justification** for your choice, referencing specific aspects of the problem.

        Strategies:
        {solution_generation_result}
        Problem:
        {user_prompt}"""
    )
    
    # Self-Revision Prompt
    revision_prompt: str = Field(
            title="Revision Prompt",
            default="""Please review your previous output for the step "{step_name}" and check for any errors, omissions, or inconsistencies. Make corrections as needed to improve the accuracy and completeness of your work.

    Previous Output:
    {previous_output}
    """
        )   

    # Step 4: Develop Solution
    develop_solution_prompt: str = Field(
        title="Develop Solution Statement",
        default="""Using the selected strategy above, **apply meticulous, step-by-step logical reasoning** to solve the problem. In your solution:

        - **Detail each step** clearly and sequentially.
        - **Reference relevant information** from the problem at each step.
        - **Verify the correctness** of each step before proceeding.
        - **Identify and justify any assumptions** made.

        After completing your solution, **review it to ensure all aspects of the problem have been addressed**, and **provide a clear and direct final answer**.

        Problem:
        {user_prompt}
        Selected Strategy:
        {select_strategy_result}"""
    )
    
    # Reasoning Display Option
    show_reasoning: bool = Field(
        default=True,
        description="If On, the answer will include the full reasoning."
    )
@plugin
def settings_model():
    return StrawberryCatSettings
