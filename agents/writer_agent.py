"""
We are defining Writer Agent here
"""
from google.genai.types import GenerateContentConfig,SafetySetting
import os, tempfile, re, uuid
from google.cloud import aiplatform
from google import genai
from utils.config import Config, WorkflowState
from typing import Dict 
from langchain_google_vertexai import (
    VertexAI,
    ChatVertexAI,
    VertexAIEmbeddings,
    VectorSearchVectorStore
)
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from chroma_manager import ChromaManager



class WriterAgent:
    def __init__(self):
        self.config = Config()
        self.generation_config = GenerateContentConfig(
            temperature = 0,
            max_output_tokens = self.config.GEMINI_OUTPUT_TOKEN_LIMIT
        )
        self.client = genai.Client(
            vertexai=True,
            project=self.config.PROJECT_ID,
            location=self.config.LOCATION,
        )

        # chromadb
        self.chroma_manager = ChromaManager()
        # self.model = VertexAI(
        #     temperature = 0,
        #     model_name = self.config.MODEL_NAME,
        #     max_output_tokens = self.config.MAX_TOKENS
        # )

    # This function will take original content and generate new content based on it
    # the instrucitons is initialized to "" emoty string instructions: str=""
    def spin_content(self, state: WorkflowState) -> WorkflowState:
    #def spin_content(self, original_content: str, instructions: str = "") -> Dict:
        """
        Create a spun version of the content
        """ 

        print("Spinning content...")
        # print("Original Content:", state['original_content'])
        # print("Current Content:", state['current_content'])
        # print("Reviewer Feedback: ", state['reviewer_feedback'])

        #Instructions: {state['instructions'] if state['instructions'] else "Rewrite the content into a more engaging, well-crafted prose where the essense of the original content is retained."}
        prompt = f"""
        You are a creative writer tasked with rewriting the following while maintaining the same tone and style:

        Please provide a rewritten version that:
        1. Maintains the original meaning and kep plot points intact.
        2. Uses fresh language and varied sentence structures
        3. Enhances narrative flow, paicng, readability and engagement for readers.
        4. Improving descriptive language
        5. Developing character voices and depth
        6. Preserves the overall mood and atmosphere of the original content.
        7. Preserves the original length approximately.PermissionError

        If this is a revision (iteration>1), consider the previous reviewer feedback carefully and rewrite the content accordingly but keep the core meaning intact.

        Original Content:
        {state['original_content']}

        Current Content:
        {state['current_content']}

        Previous Feedback:
        {state['reviewer_feedback']}

        Iteration: {state['iteration_count']}

        Rewritten content:
        """

        try:
            writer_output = self.client.models.generate_content(
                model = self.config.MODEL_NAME,
                contents= [prompt],
                config = self.generation_config
            )

            # store content to chromadb
            metadata = {
                "type": "writer_output",
                "version": f"v{state['iteration_count']}",
                "status": "writer_completed",
                "source_url": "https://www.google.com",
                "chapter": "Chapter 1",
                "iteration": state.get("iteration_count", 1)
            }

            # call Chromamanager to store the content with versioning
            self.chroma_manager.store_content(writer_output.text, metadata)
            print(f"Storing content to chroma: {metadata}")

            return {
                **state,
                'current_content': writer_output.text,
                'writer_output': writer_output.text,
                'messsages' : AIMessage(content=f"Writer: Content enhanced and rewritten"),
                "status": "writer_completed"
            }
        except Exception as e:
            print(f"An error occurred: {e}")
            return {
                **state,
                'messages': AIMessage(content=f"Writer: Error occurred during spinning content"),
                'status': 'writer_error',       
                }


#### FOR TESTING PURPOSES ONLY ####
# if __name__ == "__main__":
#     agent = WriterAgent()

#     # Sample input
#     original_text = (
#         "The sun was setting behind the hills as the village slowly came to life. "
#         "Children ran across the fields while elders sat outside, sharing stories from the past."
#     )
#     instructions = "Rewrite the content in a poetic tone."

#     state: WorkflowState = {
#         "original_content": original_text,
#         "current_content": "",
#         "messages": [],
#         "reviewer_feedback": "",
#         "manager_decision": "",
#         "iteration_count": 1,
#         "status": "",
#         "metadata": {},
#     }

#     #result = agent.spin_content(original_text,instructions)
    
#     result = agent.spin_content(state)
    
#     print(result["writer_output"])
#     # results
#     # if result.get('status') == 'success':
#     #     print(result.get('spun_content'))
#     # else:
#     #     print(f"Error: {result.get('error')}")