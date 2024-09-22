from cat.mad_hatter.decorators import tool, hook, plugin
from cat.log import log
from pydantic import BaseModel, Field

# Definisci il modello delle impostazioni
class strawberryCatSettings(BaseModel):
    context_analysis_prompt: str = Field(
        title="Context Analysis Prompt 2",
        default="""Analyze the following problem, paying close attention to real-world implications and contextual factors:

        {user_prompt}

        Consider these context relevant information: {declarative_memories}

        This is what has been already said about this topic: {episodic_memories}

        Provide your analysis in the following structure:

        1. Main Question: [Restate the primary question]
        2. Given Options: [List the multiple-choice options provided]
        3. Key Facts: [List the most important given facts]
        4. Contextual Factors: [List factors that could influence the real-world outcome]
        5. Implicit Information: [List any important implied information]


        IMPORTANT: ALWAYS reply using the {user_prompt} orginal language (es. Italian, English, Spanish...)
        """
    )
    solution_generation_prompt: str = Field(
        title="Solution Generation Prompt",
        default="""Based on the following problem analysis:

        {context_analysis_result}

        Solve the problem, considering all real-world implications and contextual factors. Provide your solution in the following structure:

        FINAL ANSWER: [Answer with the solution of the problem, in clear and succinct format]

        \nEXPLANATION:
        1. Initial Calculations: [Show any necessary mathematical calculations]
        2. Real-World Considerations: [Explain how real-world factors affect the result]
        3. Reasoning: [Provide a step-by-step explanation of your thought process]
        4. Justification: [Explain why the chosen answer is the most realistic]
        5. Confidence Level: [High/Medium/Low] - [Brief explanation]

        Remember, the goal is to choose the most realistic answer, taking into account both the mathematical aspects, if any, and the real-world context of the problem.
        ALWAYS answer using the original {user_prompt} language!
"""
    )
    show_reasoning: bool = Field(
        default=False,
        description="If On, the answer will include the full reasoning. "
                "If off you can access the reasoing in working_memory.reasoning."
    )

# Carica le impostazioni nel plugin
@plugin
def settings_model():
    return strawberryCatSettings


# Context-Aware Chain of Thought Algorithm Prompts with Descriptive Names

context_analysis_prompt = """Analyze the following problem, paying close attention to real-world implications and contextual factors:

{user_prompt}

Consider these context relevant information: {declarative_memories}

This is what has been already said about this topic: {episodic_memories}

Provide your analysis in the following structure:

1. Main Question: [Restate the primary question]
2. Given Options: [List the multiple-choice options provided]
3. Key Facts: [List the most important given facts]
4. Contextual Factors: [List factors that could influence the real-world outcome]
5. Implicit Information: [List any important implied information]


IMPORTANT: ALWAYS reply using the {user_prompt} orginal language (es. Italian, English, Spanish...)
"""

solution_generation_prompt = """Based on the following problem analysis:

{context_analysis_result}

Solve the problem, considering all real-world implications and contextual factors. Provide your solution in the following structure:

FINAL ANSWER: [Answer with the solution of the problem, in clear and succinct format]

\nEXPLANATION:
1. Initial Calculations: [Show any necessary mathematical calculations]
2. Real-World Considerations: [Explain how real-world factors affect the result]
3. Reasoning: [Provide a step-by-step explanation of your thought process]
4. Justification: [Explain why the chosen answer is the most realistic]
5. Confidence Level: [High/Medium/Low] - [Brief explanation]

Remember, the goal is to choose the most realistic answer, taking into account both the mathematical aspects, if any, and the real-world context of the problem.
ALWAYS answer using the original {user_prompt} language!
"""


@hook(priority=1)
def agent_fast_reply(fast_reply, cat):
    message = cat.working_memory.user_message_json.text
    declarative_memories = cat.working_memory.declarative_memories[0][0].page_content if cat.working_memory.declarative_memories else ""
    episodic_memories = cat.working_memory.episodic_memories[0][0].page_content if cat.working_memory.episodic_memories else ""
    if message.startswith("Q*"): 
        user_prompt = message[2:].strip()
        cat.send_ws_message("Analyzing problem context...")
        context_analysis_result = cat.llm(context_analysis_prompt.format(user_prompt=user_prompt, declarative_memories=declarative_memories, episodic_memories=episodic_memories))
        cat.send_ws_message("Generating solution...")
        solution_result = cat.llm(solution_generation_prompt.format(context_analysis_result=context_analysis_result, user_prompt=user_prompt))
        fast_reply["output"] = solution_result
        return fast_reply

