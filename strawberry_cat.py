from cat.mad_hatter.decorators import hook

@hook(priority=10)
def before_cat_reads_message(user_message_json, cat):
    prompt = user_message_json["text"]
    settings = cat.mad_hatter.get_plugin().load_settings()
    trigger = settings.get("trigger")
    
    if prompt.startswith("Q*"):
        user_prompt = prompt[len(trigger):].strip()
        
        # Initialize a dictionary to store intermediate results
        intermediate_results = {}

        # Step 1: Context Analysis
        context_analysis_prompt = settings.get("context_analysis_prompt").format(user_prompt=user_prompt)
        cat.send_ws_message("Analyzing problem context...")
        context_analysis_result = cat.llm(context_analysis_prompt)
        intermediate_results['context_analysis'] = context_analysis_result

        # Self-Revision for Context Analysis
        context_revision_prompt = settings.get("revision_prompt").format(
            step_name="Context Analysis",
            previous_output=context_analysis_result,
            user_prompt=user_prompt
        )
        cat.send_ws_message("Revising context analysis...")
        context_analysis_revision = cat.llm(context_revision_prompt)
        # Use the revised output
        context_analysis_result = context_analysis_revision
        intermediate_results['context_analysis'] = context_analysis_result

        # Step 2: Solution Generation
        solution_generation_prompt = settings.get("solution_generation_prompt").format(
            context_analysis_result=context_analysis_result
        )
        cat.send_ws_message("Generating possible strategies...")
        solution_generation_result = cat.llm(solution_generation_prompt)
        intermediate_results['solution_generation'] = solution_generation_result

        # Self-Revision for Solution Generation
        solution_revision_prompt = settings.get("revision_prompt").format(
            step_name="Solution Generation",
            previous_output=solution_generation_result,
            context_analysis_result=context_analysis_result
        )
        cat.send_ws_message("Revising solution generation...")
        solution_generation_revision = cat.llm(solution_revision_prompt)
        solution_generation_result = solution_generation_revision
        intermediate_results['solution_generation'] = solution_generation_result

        # Step 3: Strategy Selection
        select_strategy_prompt = settings.get("select_strategy_prompt").format(
            solution_generation_result=solution_generation_result,
            user_prompt=user_prompt
        )
        cat.send_ws_message("Selecting the most effective strategy...")
        select_strategy_result = cat.llm(select_strategy_prompt)
        intermediate_results['select_strategy'] = select_strategy_result

        # Self-Revision for Strategy Selection
        strategy_revision_prompt = settings.get("revision_prompt").format(
            step_name="Strategy Selection",
            previous_output=select_strategy_result,
            solution_generation_result=solution_generation_result
        )
        cat.send_ws_message("Revising strategy selection...")
        select_strategy_revision = cat.llm(strategy_revision_prompt)
        select_strategy_result = select_strategy_revision
        intermediate_results['select_strategy'] = select_strategy_result

        # Step 4: Develop Solution
        develop_solution_prompt = settings.get("develop_solution_prompt").format(
            select_strategy_result=select_strategy_result,
            user_prompt=user_prompt
        )
        cat.send_ws_message("Developing the solution...")

        if not settings.get("show_reasoning"):
            develop_solution_prompt += "\n\nIMPORTANT: Reply ONLY with the final answer. Do NOT include full reasoning!"

        # Replace the user's message with the final prompt
        user_message_json["text"] = develop_solution_prompt

        return user_message_json



@hook
def agent_prompt_prefix(prefix, cat):
    prefix = (
        "You are an advanced AI language model that solves problems efficiently and accurately "
        "using a structured chain-of-thought reasoning process. "
        "Your goal is to understand problems thoroughly, plan effective solutions, "
        "and provide clear, correct answers. "
        "Follow each step carefully and ensure your reasoning is logical and well-explained."
    )
    return prefix