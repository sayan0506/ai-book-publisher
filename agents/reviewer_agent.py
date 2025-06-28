# AI Book Publication Workflow
# This agent will be used to review the book and provide feedback on it.
from google import genai
from utils.config import Config, WorkflowState 
from google.genai.types import GenerateContentConfig
from langchain_core.messages import AIMessage, HumanMessage


class ReviewerAgent:
    def __init__(self):
        self.config = Config()
        self.generation_config = GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=self.config.GEMINI_OUTPUT_TOKEN_LIMIT,
        )
        self.client = genai.Client(
            vertexai=True,
            project=self.config.PROJECT_ID,
            location=self.config.LOCATION,
        )

    def review_content(self, state: WorkflowState) -> WorkflowState:
        """Review the spun content against the original content and provide feedback."""
        prompt = f"""
        You are a literary reviewer. Compare original content with rewritten content and provide feedback.

        Original Content:
        {state['original_content']}...

        Rewritten Content:
        {state['current_content']}...

        Please provide:
        1. Overall quality score: (1-10)
        2. Strength of the rewrite
        3. Areas of improvement
        4. Specific suggestions for enhancement
        5. Whether the core meaning is preserved

        Review:
        """

        try:
            # as we are using async then need to use await keyword before client call
            reviewer_feedback = self.client.models.generate_content(
                model = self.config.MODEL_NAME,
                contents = [prompt],
                config = self.generation_config,
            )

            return {
                **state,
                "reviewer_feedback": reviewer_feedback.text,
                "iteration_count": state.get("iteration_count", 1) + 1,
                "messages": state.get("messages", []) + [AIMessage(content=f"Reviewer: Feedback recieved by the Reviewer!")],
                "status": "reviewer_completed",
            }
        except Exception as e:
            print(f"Error in generating review: {e}")
            return {**state,
                    "messages": state.get("messages", []) + [HumanMessage(content=f"Reviewer: Error occured during reviewing!")],
                    "status": "reviewer_error",
            }
        


# if __name__ == "__main__":
#     # Example usage
#     reviewer = ReviewerAgent()

#     # Sample input
#     original_text = (
#         "The sun was setting behind the hills as the village slowly came to life. "
#         "Children ran across the fields while elders sat outside, sharing stories from the past."
#     )

#     spun_content = (
#         """As twilight painted the hills with fire, the village stirred from its slumber.\n 
#         A tapestry of laughter unfurled as children, like dandelion seeds on the wind, scattered across emerald fields.\n 
#         Meanwhile, beneath the eaves of time-worn homes, elders gathered, their voices weaving tales of yesteryear, each word a thread in the rich fabric of memory."""
#     )
    
#     state: WorkflowState = {
#         "original_content": original_text,
#         "current_content": spun_content,
#         "messages": [],
#         "reviewer_feedback": "",
#         "manager_decision": "",
#         "iteration_count": 1,
#         "status": "",
#         "metadata": {},
#     }

#     result = reviewer.review_content(state)

#     print(result["reviewer_feedback"])