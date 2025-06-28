# manager_agent.py
# This agent will manage the agents and their interactions with each other decide whether it needs to write, review or human_review needed
from google import genai
from google.genai.types import GenerateContentConfig
from utils.config import Config, WorkflowState
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


class ManagerAgent:
    def __init__(self):
        self.config = Config() 
        self.generation_config = GenerateContentConfig(
            temperature=self.config.TEMPERATURE, 
            max_output_tokens=self.config.GEMINI_OUTPUT_TOKEN_LIMIT
            )
        self.client = genai.Client(
            project=self.config.PROJECT_ID,
            location=self.config.LOCATION,
            vertexai=True
        )

    def manager_workflow(self, state: WorkflowState)->WorkflowState:
        """Content Manager Agent - Makes workflow decisions based on current state of workflow"""

        manager_prompt = f"""
        You are a content management specialist responsible for managing the workflow for AI book publication. Your task is to make decisions about how to proceed in the workflow.
        Based on the reviewer feedback and content quality, decide what is the next step in the workflow.

        Options:
        - "human_review": Content needs human review before proceeding further
        - "quality_check": Content is good, proceed to final quality check
        - "revision_needed": Content needs revision by writer
        - "approved": Content is excellent and ready for publication

        Consider iteration count (max 3 iterations) before requiring human review. 
        Respond with ONLY the decision keyword from above options without any additional text.

        Current Content:
        {state['current_content']} 

        Reviewer Feedback:
        {state['reviewer_feedback']}

        Iteration Count: 
        {state['iteration_count']}

        What should be the next step?"""

        # as we are using async then need to use await keyword before client call
        manager_decision = self.client.models.generate_content(
            model = self.config.MODEL_NAME,
            contents=[manager_prompt],
            config = self.generation_config
        )        

        print(f"Manager Decision: {manager_decision.candidates[0].content.parts[0].text.strip().lower()}")
        print(f"Manager Iteration Count: {state['iteration_count']}")
        # Clean up the decision (remove extra text)
        #decision = manager_decision.text.strip().lower()
        decision = manager_decision.candidates[0].content.parts[0].text.strip().lower() 
        print(f"Decision: {decision}")
        if "human_review" in decision:
            decision = "human_review"
            # if human review is needed then change status to awaiting human review
            # need to update the status field as everytime human_review node is called it checks the status field to "NO FEEDBACK" and then only
            # it interrupts else it passed to human_review router
            state["human_feedback"] = "NO FEEDBACK"
        elif "quality_check" in decision:
            decision = "quality_check"
        elif "revision_needed" in decision:
            decision = "revision_needed"
        elif "approved" in decision:
            decision = "approved"
        else:
            # default fallback
            decision = "human_review"

        #print(f"Manager decision: {decision}")
        # here it seems like state is not getting updated but langgraph does the state merging
        # so if we pass the previous state value
        # in a dict form where am passing the updated values then it gets merged with the previous state
        return {
            **state,
            "manager_decision":decision,
            "messages": state.get("messages", []) + [AIMessage  (content=f"Manager: Decision made: {decision}")],
            "status": f"Manager Decision: {decision}"
        }


#### FOR TESTING PURPOSES ONLY ####
# if __name__ == "__main__":
#     manager_agent = ManagerAgent()

#     original_text = (
#         "The sun was setting behind the hills as the village slowly came to life. "
#         "Children ran across the fields while elders sat outside, sharing stories from the past."
#     )

#     spun_content = (
#         """As twilight painted the hills with fire, the village stirred from its slumber.\n 
#         A tapestry of laughter unfurled as children, like dandelion seeds on the wind, scattered across emerald fields.\n 
#         Meanwhile, beneath the eaves of time-worn homes, elders gathered, their voices weaving tales of yesteryear, each word a thread in the rich fabric of memory."""
#     )

#     reviewer_feedback = """
#     Okay, here's a review of the original and rewritten content:

#     **Review:**

#     **1. Overall Quality Score:**

#     *   **Original Content:** 5/10
#     *   **Rewritten Content:** 9.5/10

#     **2. Strength of the Rewrite:**

#     The rewrite is significantly stronger than the original. It demonstrates a clear improvement in several key areas:

#     *   **Imagery:** The rewrite uses much more vivid and evocative imagery. Phrases like "twilight painted the hills with fire," "dandelion seeds on the wind," and "emerald fields" create a much stronger visual impression.
#     *   **Figurative Language:** The rewrite employs effective metaphors and similes (e.g., children like dandelion seeds, voices weaving tales) to add depth and richness to the description.
#     *   **Sensory Detail:** The rewrite appeals to more senses. We can almost see the colors of the twilight, hear the laughter, and feel the weight of the elders' memories.
#     *   **Flow and Rhythm:** The sentence structure in the rewrite is more varied and sophisticated, creating a more pleasing rhythm and flow. The use of longer, more descriptive sentences interspersed with shorter, impactful phrases enhances the reading experience.
#     *   **Voice:** The rewrite has a more distinct and poetic voice. It feels more deliberate and crafted.
    
#     **3. Areas of Improvement:**
#     Not found as such!!


#     **3. Areas of Improvement:**

#     While the rewrite is strong, there are a few areas where it could be further improved:

#     *   **Potential for Overwriting:** The rewrite flirts with the line between descriptive and overwritten. While the imagery is beautiful, it's important to ensure it doesn't become too dense or distracting.
#     *   **Pacing:** The rewrite slows down the pace considerably. This can be a strength, but it's important to consider the overall context of the piece. If the scene needs to move quickly, some of the descriptive elements might need to be trimmed.
#     *   **Clarity:** While the imagery is strong, a few phrases could be slightly clearer. For example, "beneath the eaves of time-worn homes" is a bit clunky.

#     **4. Specific Suggestions for Enhancement:**

#     *   **Refine the "Eaves" Phrase:** Consider alternatives to "beneath the eaves of time-worn homes." Perhaps something like "under the shelter of ancient eaves" or "in the shadow of weathered homes" would be smoother.
#     *   **Consider the Context:** Think about the purpose of this description within the larger story. Is it meant to be a brief snapshot, or a more immersive scene? Adjust the level of detail accordingly. If it's a brief snapshot, consider trimming some of the more elaborate descriptions.
#     *   **Vary Sentence Length:** While the rewrite does a good job of varying sentence length, ensure there's a balance between longer, descriptive sentences and shorter, more impactful ones. Too many long sentences in a row can become tiring for the reader.
#     *   **Read Aloud:** Read the rewritten passage aloud to identify any awkward phrasing or areas where the rhythm feels off.

#     **5. Whether the Core Meaning is Preserved:**

#     Yes, the core meaning is preserved. Both the original and rewritten content convey the same basic information: the village is coming to life as the sun sets, children are playing, and elders are sharing stories. However, the rewrite elevates this basic information into a much more evocative and memorable scene. The rewrite has successfully taken the core meaning and amplified it with richer language and imagery.
#     """

#     state: WorkflowState = {
#         "original_content": original_text,
#         "current_content": spun_content,
#         "messages": [],
#         "reviewer_feedback": reviewer_feedback,
#         "manager_decision": "",
#         "iteration_count": 1,
#         "status": "",
#         "metadata": {},
#     }

#     updated_state = manager_agent.manager_workflow(state)

#     # Print results
#     # print("✅ Manager Decision:", updated_state["manager_decision"])
#     # print("🔄 Status:", updated_state["status"])
#     # print("💬 Messages:")
#     print(updated_state["messages"])
#     # for msg in updated_state["messages"]:
#     #     print("-", msg.content)
    


