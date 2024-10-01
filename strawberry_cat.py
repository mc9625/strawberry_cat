from cat.mad_hatter.decorators import hook
from cat.log import log
import json

json_formatting_suffix = """

To ensure your response can be properly processed, please format your entire response as a valid JSON object. Here's an example of the expected structure:

{
  "step_result": {
    "analysis": "Your detailed analysis goes here.",
    "deductions": [
      "List your deductions or key points here",
      "Each deduction should be a separate string in this array"
    ],
    "conclusion": "Your conclusion for this step goes here."
  },
  "next_step": {
    "description": "Brief description of the next step, if applicable",
    "questions": [
      "List any questions to be addressed in the next step",
      "Each question should be a separate string in this array"
    ]
  }
}

Please ensure that:
1. All keys and string values are enclosed in double quotes.
2. There are no trailing commas after the last item in an array or object.
3. All opening braces or brackets have a corresponding closing one.
4. Your response is a single, valid JSON object.
"""

def append_json_instructions(prompt):
    return prompt + json_formatting_suffix

@hook(priority=10)
def agent_fast_reply(fast_reply, cat):
    prompt = cat.working_memory.user_message_json.text
    settings = cat.mad_hatter.get_plugin().load_settings()
    trigger = settings.get("trigger")
    start_prompt = """You are an AI assistant specialized in logical analysis and problem-solving. Your task is to carefully analyze the user's request and develop a detailed plan to provide a comprehensive and accurate response. Follow these guidelines:

    1. In-depth Analysis:
    - Identify the main objective of the request.
    - List all relevant facts provided in the request, including seemingly minor details.
    - Identify any implicit constraints or conditions in the problem.
    - Highlight possible ambiguous interpretations or necessary assumptions.

    2. Reasoning Plan:
    - Develop a series of logical steps to analyze the problem.
    - Each step should focus on a specific aspect of the problem or a logical deduction.
    - Include steps to verify assumptions and consider alternative scenarios.
    - Ensure all provided information is considered, even details that might initially seem irrelevant.

    3. Definition of Reasoning Steps:
    - For each step, provide:
        - A clear objective.
        - Detailed instructions on how to proceed, including specific questions to consider.
        - The desired format for the output.
    - Include steps to:
        - Analyze each relevant fact.
        - Examine relationships between facts.
        - Consider the logical implications of each piece of information.
        - Verify the consistency of deductions with all provided facts.

    4. Response Structure:
    Provide your analysis and plan in a structured JSON format as follows:

    {
        "initial_analysis": {
        "main_objective": "Description of the main objective",
        "relevant_facts": ["Fact 1", "Fact 2", "..."],
        "constraints_and_conditions": ["Constraint 1", "Constraint 2", "..."],
        "potential_ambiguities": ["Ambiguity 1", "Ambiguity 2", "..."]
        },
        "reasoning_plan": [
        {
            "step_number": 1,
            "name": "Descriptive name of the step",
            "objective": "Specific objective of the step",
            "instructions": "Detailed instructions for reasoning",
            "questions_to_consider": ["Question 1?", "Question 2?", "..."],
            "output_format": "Description of the required output format"
        },
        // Repeat for each additional step
        ],
        "final_considerations": "Any additional notes or considerations on the reasoning plan"
    }

    Ensure that the plan is comprehensive, logical, and suitable for examining all aspects of the problem, including non-obvious or counterintuitive scenarios. Your plan will guide an in-depth reasoning process, so be as precise and detailed as possible.
    """
    
    if prompt.startswith(trigger):
        user_prompt = prompt[len(trigger):].strip()
        
        # Generate the initial plan
        cat.send_ws_message("Generating initial analysis and reasoning plan...")
        initial_analysis_prompt = append_json_instructions(start_prompt + f"\n\nUser Request: {user_prompt}")
        initial_analysis = cat.llm(initial_analysis_prompt)
        
        # Log the full response for debugging
        print("Full LLM Response:")
        print(initial_analysis)

        plan = extract_json(initial_analysis)
        
        if not plan:
            cat.send_ws_message("Unable to generate a valid initial plan.", msg_type = 'eror')
            fast_reply["output"] = "I apologize, but I couldn't properly analyze your request. Could you please rephrase it?"
            return fast_reply

        cat.send_ws_message("Initial plan generated. Starting reasoning process...")

        reasoning_chain = []
        for step in plan['reasoning_plan']:
            cat.send_ws_message(f"Executing step {step['step_number']}: {step['name']}", msg_type='notification')
            
            # Construct the prompt for this step
            step_prompt = f"""
            Original request context:
            {user_prompt}

            Initial analysis:
            {json.dumps(plan['initial_analysis'], indent=2)}

            Step {step['step_number']}: {step['name']}
            Objective: {step['objective']}
            Instructions: {step['instructions']}

            Questions to consider:
            {' '.join(step['questions_to_consider'])}

            Previous reasoning:
            {json.dumps(reasoning_chain, indent=2)}

            Based on the original context, initial analysis, and previous reasoning, proceed with executing this step.
            Provide a detailed response, carefully considering all questions and instructions provided.
            """
            
            step_prompt_with_json_instructions = append_json_instructions(step_prompt)
            step_response = cat.llm(step_prompt_with_json_instructions)
            step_result = extract_json(step_response)
            if step_result:
                reasoning_chain.append(step_result)
            else:
                cat.send_ws_message(f"Error in extracting JSON for step {step['step_number']}", msg_type='error')

        # Generate the final response
        cat.send_ws_message("Generating final response...")
        final_prompt = f"""
        Original request context:
        {user_prompt}

        Initial analysis:
        {json.dumps(plan['initial_analysis'], indent=2)}

        Complete reasoning chain:
        {json.dumps(reasoning_chain, indent=2)}

        Based on the original context, initial analysis, and the complete reasoning chain, generate a final response.
        The response should:
        1. Briefly summarize the reasoning process.
        2. Present the final conclusion clearly and concisely.
        3. Explain why this conclusion is the most logical, considering all facts and deductions.
        4. If applicable, indicate which of the provided options (A, B, C, D, etc.) is correct and why.
        5. Mention any assumptions made or remaining ambiguities.

        Provide a complete, accurate, and well-reasoned response.
        """

        
        final_result = cat.llm(final_prompt)
        
        if final_result:
            fast_reply["output"] = final_result
        else:
            fast_reply["output"] = "I apologize, but I encountered an error while processing your request."
        
        return fast_reply

def extract_json(content):
    try:
        # Find the first '{' and the last '}'
        start = content.find('{')
        end = content.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            # Extract the potential JSON string
            json_str = content[start:end+1]
            
            # Attempt to parse the JSON
            data = json.loads(json_str)
            return data
        else:
            print("No JSON-like structure found in the content.")
            return None
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print("Content causing the error:")
        print(content)
        return None
    except Exception as e:
        print(f"Unexpected error in extract_json: {e}")
        return None