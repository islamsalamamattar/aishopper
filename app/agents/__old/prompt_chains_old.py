import json
import os
import random
from dotenv import load_dotenv
import llm
import time

load_dotenv()

# ------ Helpers Methods


def build_models():

    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    haiku_model = llm.get_model("claude-3-haiku")
    haiku_model.key = ANTHROPIC_API_KEY

    sonnet_model = llm.get_model("claude-3-sonnet")
    sonnet_model.key = ANTHROPIC_API_KEY

    opus_model = llm.get_model("claude-3-opus")
    opus_model.key = ANTHROPIC_API_KEY

    return haiku_model, sonnet_model, opus_model


def coin_flip():
    return random.randint(0, 1)


# ------ Prompt Chains


def prompt_chain_snowball(haiku_model):
    """
    Snowball prompt - start with a little information, that is developed over each prompt.
    Use Case
    - Blogs
    - Newsletters
    - Research
    - Summaries
    Mermaid Diagram
    A[Start]
    B{Base Information}
    C[Snowball Prompt 1]
    D[Snowball Prompt 2]
    E[Snowball Prompt 3]
    F[Summary/Format Prompt]
    G[End]
    A --> B --> C --> D --> E --> F --> G
    """

    base_information = "3 Unusual Use Cases for LLMs"

    snowball_prompt_response_1 = haiku_model.prompt(
        f"Generate a clickworthy title about this topic: '{base_information}'. Respond in JSON format {{title: 'title', topic: '{base_information}'}}"
    )

    print("Snowball #1: ", snowball_prompt_response_1.text())

    snowball_prompt_response_2 = haiku_model.prompt(
        f"Generate a compelling 3 section outline given this information: '{snowball_prompt_response_1.text()}'. Respond in JSON format {{title: '<title>', topic: '<topic>', sections: ['<section1>', '<section2>', '<section3>']}}"
    )

    print("Snowball #2: ", snowball_prompt_response_2.text())

    snowball_prompt_response_3 = haiku_model.prompt(
        f"Generate 1 paragraph of content for each section outline given this information: '{snowball_prompt_response_2.text()}'. Respond in JSON format {{title: '<title>', topic: '<topic>', sections: ['<section1>', '<section2>', '<section3>'], content: ['<content1>', '<content2>', '<content3>']}}"
    )

    print("Snowball #3: ", snowball_prompt_response_3.text())

    snowball_markdown_prompt = haiku_model.prompt(
        f"Generate a markdown formatted blog post given this information: '{snowball_prompt_response_3.text()}'. Respond in JSON format {{markdown_blog: '<entire markdown blog post>'}}"
    )

    print("Final Snowball: ", snowball_markdown_prompt.text())

    with open("snowball_prompt_chain.txt", "w") as file:
        file.write(snowball_markdown_prompt.text())

    pass


def prompt_chain_workers(haiku_model, sonnet_model, opus_model):
    """
    Delegate different parts of your workload to individual prompt workers.
    Use Case
    - Research
    - Parallelization
    - Autocomplete
    - Divide and Conquer
    - Similar Tasks More Scalable
    Mermaid Diagram
    A[Start]
    B[Plan Prompt]
    C[Worker Prompt 1]
    D[Worker Prompt 2]
    E[Worker Prompt 3]
    F[Summary/Format Prompt]
    G[End]
    A --> B --> C
    B --> D
    B --> E
    E --> F
    C --> F
    D --> F
    F --> G
    """

    print("Generating function stubs...")

    code_planner_prompt_response = opus_model.prompt(
        '''Create the function stubs with detailed comments of how to write the code to build write_json_file, write_yml_file, write_toml_file. 
Example Function Stub:
def read_toml_file(file_path: str) -> str:
    """
    Read the file at the given file path and return the contents as a string.
    Use a toml parser to parse the file.
    Usage:
    read_toml_file("path/to/file.toml")
    """
    pass
Respond in json format {function_stubs: ["def function_stub1...", "def function_stub2...", ...]}'''
    )
    code_planner_result = code_planner_prompt_response.text()

    print(code_planner_result)

    function_stubs = json.loads(code_planner_result)["function_stubs"]

    function_stub_raw_results = ""

    for stub in function_stubs:

        time.sleep(0.5)

        print(f"\n\nImplementing function stub in worker prompt...\n\n")

        code_executor_prompt_response = opus_model.prompt(
            f"Implement this function stub in python: {stub}. Assume all imports are already installed. Respond exclusively with runnable code in json format {{code: '<code>'}}"
        )
        print(code_executor_prompt_response.text())

        function_stub_raw_results += code_executor_prompt_response.text()

    print(function_stub_raw_results)

    final_module = opus_model.prompt(
        f"Clean up and combine the following python code and combine every code stub into a final python file that can be executed. Code: {function_stub_raw_results}. Respond exclusively with the finalized code in json format {{code: '<code>'}}"
    )

    print(final_module.text())

    # write to python file
    with open("files.py", "w") as file:
        file.write(final_module.text())

    pass


def prompt_chain_fallback(haiku_model, sonnet_model, opus_model):
    """
    Fallback Prompt Chain
    Use Case
    - Save Money (Cheap LLMs first)
    - Save Time (Fast LLMs first)
    - Generating Content
    - Specific Formats
    - Last Resort
    Mermaid Diagram
    A[Start]
    B[Top Priority Prompt/Model]
    C[Run Process]
    D[Secondary Fallback Prompt/Model]
    E[Run Process]
    F[Final Fallback Prompt/Model]
    G[End]
    A --> B --> C --> D --> E --> F --> G
    C --> G
    E --> G
    """

    def run_fallback_flow(evaluator_function, fallback_functions):
        for fallback_function, model_name in fallback_functions:
            response = fallback_function()
            print(f"{model_name} Response: ", response.text())

            success = evaluator_function(response.text())

            if success:
                print(f"{model_name} Success - Returning")
                return True
            else:
                print(f"{model_name} Failed - Fallback")

        print("All Fallback Functions Failed")
        return False

    def run_code(code):
        """
        Fake run code that returns a random boolean.
        50% chance of returning True.
        """
        return coin_flip()

    function_generation_prompt = f"Generate the solution in python given this function definition: 'def text_to_speech(text) -> Bytes'. Respond in JSON format {{python_code: '<python code>'}}"

    fallback_functions = [
        (
            lambda: haiku_model.prompt(function_generation_prompt),
            "(Haiku) Cheap, Fast Top Priority Prompt/Model",
        ),
        (
            lambda: sonnet_model.prompt(function_generation_prompt),
            "(Sonnet) Cheap, Moderate Secondary Fallback Prompt/Model",
        ),
        (
            lambda: opus_model.prompt(function_generation_prompt),
            "(Opus) Expensive, Slow, Accurate Final Fallback Prompt/Model",
        ),
    ]

    success = run_fallback_flow(run_code, fallback_functions)

    print(f"Fallback Flow was {'✅ Successful' if success else '❌ Unsuccessful'}")

    pass


def prompt_chain_decision_maker(haiku_model):
    """
    Based on a decision from a prompt, run a different prompt chain.
    Use Case
    - Creative Direction
    - Dictate Flow Control
    - Decision Making
    - Dynamic Prompting
    - Multiple Prompts
    Mermaid Diagram
    A[Start]
    B[Decision Prompt]
    C[Prompt Chain 1]
    D[Prompt Chain 2]
    E[Prompt Chain 3]
    F[End]
    A --> B
    B --IF--> C --> F
    B --IF--> D --> F
    B --IF--> E --> F
    """

    mock_live_feed = [
        "Our revenue exceeded expectations this quarter, driven by strong sales in our core product lines.",
        "We experienced some supply chain disruptions that impacted our ability to meet customer demand in certain regions.",
        "Our new product launch has been well-received by customers and is contributing significantly to our growth.",
        "We incurred higher than expected costs related to our expansion efforts, which put pressure on our margins.",
        "We are seeing positive trends in customer retention and loyalty, with many customers increasing their spend with us.",
        "The competitive landscape remains challenging, with some competitors engaging in aggressive pricing strategies.",
        "We made significant progress on our sustainability initiatives this quarter, reducing our carbon footprint and waste.",
        "We had to write off some inventory due to changing consumer preferences, which negatively impacted our bottom line.",
    ]

    live_feed = random.choice(mock_live_feed)

    print(f"Analyzing Sentiment Of Latest Audio Clip: '{live_feed}'")

    sentiment_analysis_prompt_response = haiku_model.prompt(
        f"Analyze the sentiment of the following text as either positive or negative: '{live_feed}'. Respond in JSON format {{sentiment: 'positive' | 'negative'}}."
    )

    sentiment = json.loads(sentiment_analysis_prompt_response.text())["sentiment"]

    def positive_sentiment_action(live_feed):
        positive_sentiment_thesis_prompt_response = haiku_model.prompt(
            f"The following text has a positive sentiment: '{live_feed}'. Generate a short thesis statement about why the sentiment is positive."
        )
        print(
            f"\n\nPositive Sentiment Thesis: {positive_sentiment_thesis_prompt_response.text()}"
        )

    def negative_sentiment_action(live_feed):
        negative_sentiment_thesis_prompt_response = haiku_model.prompt(
            f"The following text has a negative sentiment: '{live_feed}'. Generate a short thesis statement about why the sentiment is negative."
        )
        print(
            f"\n\nNegative Sentiment Thesis: {negative_sentiment_thesis_prompt_response.text()}\n\n"
        )

    def unknown_sentiment_action(_):
        print(
            f"Could not determine sentiment. Raw response: {sentiment_analysis_prompt_response.text()}"
        )

    sentiment_actions = {
        "positive": positive_sentiment_action,
        "negative": negative_sentiment_action,
    }

    sentiment_action = sentiment_actions.get(sentiment, unknown_sentiment_action)

    sentiment_action(live_feed)

    pass


def prompt_chain_plan_execute(haiku_model):
    """
    Plan Execute Prompt Chain
    Use Case
    - Tasks
    - Projects
    - Research
    - Coding
    Mermaid Diagram
    A[Start]
    B<Plan Prompt>
    C<Execute Prompt>
    D<End>
    A --> B --> C --> D
    """

    task = "Design the software architecture for an AI assistant that uses tts, llms, local sqlite. "

    plan_prompt_response = haiku_model.prompt(
        f"Let's think step by step about how we would accomplish this task: '{task}'. Write all the steps, ideas, variables, mermaid diagrams, use cases, and examples concisely in markdown format. Respond in JSON format {{markdown_plan: '<plan>'}}"
    )

    print(plan_prompt_response.text())

    execute_prompt_response = haiku_model.prompt(
        f"Create a detailed architecture document on how to execute this task '{task}' given this detailed plan {plan_prompt_response.text()}.  Respond in JSON format {{architecture_document: '<document>'}}"
    )

    print(execute_prompt_response.text())

    # write the plan and execute to a file
    with open("plan_execute_prompt_chain.txt", "w") as file:
        file.write(execute_prompt_response.text())


def prompt_chain_human_in_the_loop(haiku_model, sonnet_model):
    """
    Human In The Loop Prompt Chain
    Use Case
    - Human In The Loop
    - Validation
    - Content Creation
    - Coding
    - Chat
    Mermaid Diagram
    A[Start]
    B[Initial Prompt]
    C[Human Feedback]
    D[Iterative Prompt]
    E[End]
    A --> B --> C --> D
    D --> C
    D --> E
    """
    topic = "Personal AI Assistants"
    prompt = f"Generate 5 ideas surrounding this topic: '{topic}'"
    result = haiku_model.prompt(prompt).text()
    print(result)

    while True:
        user_input = input("Iterate on result or type 'done' to finish: ")
        if user_input.lower() == "done":
            break
        else:
            prompt += f"\n\n----------------\n\nPrevious result: {result}\n\n----------------\n\nIterate on the previous result and generate 5 more ideas based on this feedback: {user_input}"
            result = sonnet_model.prompt(prompt).text()
            print(result + "\n\n----------------\n\n")

    pass


def prompt_chain_self_correct(haiku_model):
    """
    Self correct/review the output of a prompt.
    Use Case
    - Coding
    - Execution
    - Self Correct
    - Review
    - Iterate
    - Improve
    Mermaid Diagram
    A[Start]
    B[Prompt]
    C[Execute Output]
    D[Self Correct]
    E[End]
    A --> B --> C --> D --> E
    C --> E
    """

    def run_bash(command):
        print(f"Running command: {command}")
        if coin_flip() == 0:
            return "Mock error: command failed to execute properly"
        else:
            return "Command executed successfully"

    outcome = "list all files in the current directory"

    initial_response = haiku_model.prompt(
        f"Generate a bash command that enables us to {outcome}. Respond with only the command."
    )
    print(f"Initial response: {initial_response.text()}")

    # Run the generated command and check for errors
    result = run_bash(initial_response.text())

    if "error" in result.lower():

        print("Received error, running self-correction prompt")

        # If error, run self-correction prompt
        self_correct_response = haiku_model.prompt(
            f"The following bash command was generated to {outcome}, but encountered an error when run:\n\nCommand: {initial_response.text()}\nError: {result}\n\nPlease provide an updated bash command that will successfully {outcome}. Respond with only the updated command in JSON format {{command: '<command>'}}."
        )
        print(f"Self-corrected response: {self_correct_response.text()}")

        # Run the self-corrected command
        run_bash(self_correct_response.text())

    else:
        print(f"Original command executed successfully: {result}")


def main():

    haiku_model, sonnet_model, opus_model = build_models()

    prompt_chain_snowball(haiku_model)

    # prompt_chain_workers(haiku_model, sonnet_model, opus_model)

    # prompt_chain_fallback(haiku_model, sonnet_model, opus_model)

    # prompt_chain_decision_maker(haiku_model)

    # prompt_chain_plan_execute(haiku_model)

    # prompt_chain_human_in_the_loop(haiku_model, sonnet_model)

    # prompt_chain_self_correct(haiku_model)


if __name__ == "__main__":
    main()