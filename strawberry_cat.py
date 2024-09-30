from cat.mad_hatter.decorators import hook

@hook(priority=10)
def agent_fast_reply(fast_reply, cat):
    prompt = cat.working_memory.user_message_json.text
    settings = cat.mad_hatter.get_plugin().load_settings()
    trigger = settings.get("trigger")
    
    if prompt.startswith(trigger):
        user_prompt = prompt[len(trigger):].strip()
        

        # Step 1: Analyze problem
        problem_analysis_prompt = settings.get("problem_analysis_prompt").format(user_prompt=user_prompt)
        cat.agent_prefix = "You are an AI agent"
        cat.send_ws_message("Let'analyze the problem...")
        problem_analysis_result = cat.llm(problem_analysis_prompt)
        
        # Step 2: Strategic planning
        strategy_planning_prompt = settings.get("strategy_planning_prompt").format(
            problem_analysis_result=problem_analysis_result
        )
        cat.send_ws_message("Generating strategies...")
        strategy_planning_result = cat.llm(strategy_planning_prompt)
        
        # Step 3: Strategy Selection
        select_strategy_prompt = settings.get("select_strategy_prompt").format(
            problem_analysis_result=problem_analysis_result,
            strategy_planning_result=strategy_planning_result
        )
        cat.send_ws_message("Choosing the best strategy...")
        select_strategy_result = cat.llm(select_strategy_prompt)

        # Step 4: Tactical breakdown
        tactical_breakdown_prompt = settings.get("tactical_breakdown_prompt").format(
            problem_analysis_result=problem_analysis_result,
            select_strategy_result=select_strategy_result
        )
        cat.send_ws_message("Test the strategy...")
        tactical_breakdown_result = cat.llm(tactical_breakdown_prompt)

        # Step 5: Final answer
        final_answer_prompt = settings.get("final_answer_prompt").format(
            user_prompt=user_prompt,
            tactical_breakdown_result=tactical_breakdown_result
        )
        cat.send_ws_message("Preparing the final answer...")
        if not settings.get("show_reasoning"):
            final_answer_prompt += "\n\nIMPORTANT: Reply ONLY with the final answer. Do NOT include full reasoning!"
        final_answer_result = cat.llm(final_answer_prompt)
        
        # Step 6: Final check
        cat.send_ws_message("Check the answer...")
        final_check_prompt = settings.get("final_check_prompt").format(
            final_answer_result=final_answer_result,
            user_prompt=user_prompt
        )
        
        fast_reply["output"] = cat.llm(final_check_prompt)

        return fast_reply

@hook
def agent_prompt_prefix(prefix, cat):
    prompt = cat.working_memory.user_message_json.text
    settings = cat.mad_hatter.get_plugin().load_settings()
    trigger = settings.get("trigger")
    if prompt.startswith(trigger):
        prefix = ("""
        You are an advanced AI assistant with the following characteristics:

        1. **Follow Instructions**: You strictly adhere to the user's instructions and ensure all requirements are met.
        2. **Reason Smartly**: You apply dynamic, logical reasoning to analyze and solve problems, adapting your approach based on the context.
        3. **Communicate Efficiently**: You provide concise, direct, and essential answers without unnecessary details.
        4. **Self-Evaluate**: Before finalizing your answer, you review and correct it to ensure accuracy and completeness.
        5. **Be Organized**: Structure your responses clearly using bullet points or numbered lists if necessary.
        6. **Be Professional**: Maintain a polite and helpful tone in all interactions.
        7. **Be Reflective**: You take your time to think carefully before responding, ensuring that each answer is well-considered and thoroughly verified before being given.

        Your goal is to thoroughly understand the problem, select the best approach, and deliver an accurate and efficient solution.
        """
        )
        return prefix
