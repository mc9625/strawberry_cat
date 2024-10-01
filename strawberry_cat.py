from cat.mad_hatter.decorators import hook
from cat.log import log
import json

# Constants
JSON_FORMATTING_SUFFIX = """
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

OLD_START_PROMPT = """You are an AI assistant specialized in logical analysis and problem-solving. Analyze the user's request and provide a comprehensive response. Be concise for simple queries and more detailed for complex ones. Do not anticipate conclusions, do not try to answer the original problem until you reach a good level of reasoning."""

START_PROMPT = """
You are an AI assistant capable of deep analysis, problem-solving, and content generation. Follow these guidelines:

1. Carefully analyze the user's request to understand the true intent and required output format.
2. Use step-by-step reasoning to break down complex problems or requests.
3. Provide responses in the most appropriate format:
   - For coding tasks, provide actual code, not just steps to create it.
   - For analysis tasks, provide detailed explanations and insights.
   - For list requests, provide structured, numbered, or bulleted lists.
   - Adapt to other formats as needed by the specific request.
4. Ensure your reasoning is logically sound and leads to accurate conclusions.
5. Be comprehensive in your analysis but concise in your final response.
6. If a request is ambiguous, make reasonable assumptions but state them clearly.
7. For multi-part questions, address each part separately in your reasoning and response.

Remember, the user is expecting a direct and appropriate response to their request, not just a description of how to achieve it.
"""


# Helper functions
def append_json_instructions(prompt):
    return prompt + JSON_FORMATTING_SUFFIX

def extract_json(content):
    try:
        start = content.find('{')
        end = content.rfind('}') + 1
        if start != -1 and end != 0:
            json_str = content[start:end]
            return json.loads(json_str)
    except json.JSONDecodeError as e:
        log.error(f"JSON Decode Error: {e}")
    except Exception as e:
        log.error(f"Unexpected error in extract_json: {e}")
    return None

def categorize_query(query):
    # Simple query categorization based on length and complexity
    words = query.split()
    if len(words) < 10 and '?' in query:
        return "simple"
    elif any(word in query.lower() for word in ['analyze', 'compare', 'explain']):
        return "complex"
    else:
        return "moderate"

def generate_response(cat, prompt, max_steps=3):
    settings = cat.mad_hatter.get_plugin().load_settings()
    cat.send_ws_message("Generating initial analysis and reasoning plan...", msg_type='notification')
    response = cat.llm(prompt)
    result = extract_json(response)
    if not result:
        cat.send_ws_message("Unable to generate a valid initial plan.", msg_type='error')
        return "I apologize, but I couldn't generate a proper response. Could you please rephrase your request?"
    
    cat.send_ws_message("Initial plan generated. Starting reasoning process...", msg_type='notification')
    reasoning_chain = []
    for step in range(1, max_steps + 1):
        if 'step_result' in result:
            reasoning_chain.append(result['step_result'])
            if settings.get("show_reasoning"):
                cat.send_ws_message(f"Step {step} completed: {result['step_result'].get('analysis', 'Analysis step completed.')}", msg_type='chat')
        
        if 'next_step' not in result or not result['next_step']['questions']:
            break
        
        cat.send_ws_message(f"Executing step {step + 1}: {result['next_step']['description']}", msg_type='notification')
        next_prompt = f"""
        Previous reasoning: {json.dumps(reasoning_chain)}
        Next step: {result['next_step']['description']}
        Questions to address: {', '.join(result['next_step']['questions'])}
        Provide your response in the specified JSON format.
        """
        response = cat.llm(append_json_instructions(next_prompt))
        result = extract_json(response)
        if not result:
            cat.send_ws_message(f"Error in extracting JSON for step {step + 1}", msg_type='error')
            break
    
    return reasoning_chain

@hook(priority=10)
def agent_fast_reply(fast_reply, cat):
    user_prompt = cat.working_memory.user_message_json.text
    query_type = categorize_query(user_prompt)
    settings = cat.mad_hatter.get_plugin().load_settings()
    trigger = settings.get("trigger")

    if user_prompt.startswith(trigger):
        user_prompt = user_prompt[len(trigger):].strip()
        cat.send_ws_message(f"Analyzing query: {query_type} complexity detected", msg_type='notification')
        
        if query_type == "simple":
            cat.send_ws_message("Generating a concise response for your simple query...", msg_type='notification')
            response = cat.llm(f"{START_PROMPT}\n\nUser Request: {user_prompt}\nProvide a concise answer.")
            fast_reply["output"] = response
        else:
            max_steps = 3 if query_type == "moderate" else 5
            initial_prompt = f"{START_PROMPT}\n\nUser Request: {user_prompt}\nProvide a detailed analysis and response."
            reasoning_chain = generate_response(cat, append_json_instructions(initial_prompt), max_steps)
            
            cat.send_ws_message("Generating final response based on the analysis...", msg_type='notification')
            final_prompt = f"""
            Based on the following reasoning chain, provide a final response to the user's request:
            {json.dumps(reasoning_chain, indent=2)}
            User request: {user_prompt}
            """
            if settings.get("show_reasoning"):
                final_prompt = final_prompt + """Summarize the key points and present a clear conclusion, if needed format the output to make it clear to find the correct answer or the requested code."""
            final_response = cat.llm(final_prompt)
            fast_reply["output"] = final_response
        
        cat.send_ws_message("Response generation completed.", msg_type='notification')
        return fast_reply