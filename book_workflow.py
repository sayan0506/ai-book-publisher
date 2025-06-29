# AI Book Publication Workflow
# Objective: Create a system to fetch content from a web URL, apply an AI-driven "spin" to chapters, allow multiple human-in-the-loop iterations, and manage content versions.

## Installations ##
# pip install langgraph-checkpoint-sqlite

from google import genai
import os
import json
# Graph is a stateless no global state is maintained
# StateGraph is a complete graph maintains the state of the graph between calls
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from datetime import datetime 
import operator
from utils.config import Config, WorkflowState 
from scraper import ContentScraper
from agents.writer_agent import WriterAgent
from agents.reviewer_agent import ReviewerAgent
from chroma_manager import ChromaManager
from agents.manager_agent import ManagerAgent
from agents.quality_agent import QualityAgent
#from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver
#from langgraph.checkpoint.sqlite import SqliteSaver
#from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
# used to interrupt langgraph flows
from langgraph.types import interrupt 
#from langgraph.checkpoint import InMemorySaver



class BookPublicationWorkflow:
    def __init__(self):
        self.scraper = ContentScraper()
        self.writer = WriterAgent()
        self.reviewer = ReviewerAgent()
        self.chroma = ChromaManager()
        self.manager = ManagerAgent()
        self.quality = QualityAgent()
        # build the workflow graph
        self.workflow = self._build_graph() 

        # Initialize checkpoint saver for persistence
        # Use MemorySaver instead of SqliteSaver
        self.checkpointer = MemorySaver() # <--- Changed here
        # Initialize checkpoint saver for persistence
        # it saves the snapshot of graph state at each step.(it helps in long term memory retention)
        #
        # self.checkpointer = SqliteSaver.from_conn_string(":memory:")
        #self.checkpointer = InMemorySaver()
        #self.app = self.workflow.compile()
        self.app = self.workflow.compile(checkpointer=self.checkpointer)


    def _build_graph(self)->StateGraph:
        """Build LangGraph workflow for book publication process."""
        
        workflow = StateGraph(WorkflowState)

        # add nodes
        #workflow.add_node("scrape", self._scrape_node)
        workflow.add_node("writer_agent", self.writer.spin_content)
        workflow.add_node("reviewer_agent", self.reviewer.review_content)
        workflow.add_node("manager_agent", self.manager.manager_workflow)
        workflow.add_node("quality_check", self.quality.check_quality)
        workflow.add_node("human_review", self.human_feedback_node)
        #workflow.add_node("finalize", self._finalize_node)

        # define workflow edges
        workflow.set_entry_point("writer_agent")
        #workflow.add_edge("scrape", "write")
        
        # Writer -> Reviewer
        workflow.add_edge("writer_agent", "reviewer_agent")

        # Reviewer -> Manager Agent (decision point)
        workflow.add_edge("reviewer_agent", "manager_agent")

        # manager decision routing
        workflow.add_conditional_edges(
            "manager_agent",
            self.manager_decision_router,
            {
                "human_review": "human_review",
                "quality_check": "quality_check",
                "revision_needed": "writer_agent",
                "approved": END 
            } 
        )
        # here we are mentioning conditional mapping
        # - if decision is revision needed then route to writer agent else route to end
        # - if decision is quality check then route to quality_check node
        # if review is approved then route to end

        # Human review routing
        workflow.add_conditional_edges(
            "human_review",
            self.human_review_decision_router,
            {
                "approved": "quality_check",
                #"awaiting_human_feedback": "manager_agent",
                "revision_needed": "writer_agent",
                #"awaiting_human_feedback": "human_review",
                "rejected": END
            }
        )

        workflow.add_edge("quality_check", END)

        return workflow
    

    def manager_decision_router(self, state: WorkflowState)->str:
        """Route manager decision to appropriate node"""
        
        # this below code implies if manager_decision exists in state then use that value, else use the value of "human_review" key.
        # if manager_decision key doesn't exist the decision will be "human_review"
        decision = state.get("manager_decision", "human_review")

        # if it shows decision needed 
        # if decision == "revision_needed":
        #     state["iteration_count"] = state.get("iteration_count",1)+1
        print(f"Iteration Count: {state['iteration_count']}")
        
        return decision


    def human_review_decision_router(self, state: WorkflowState) -> str:
        """Route human review decision to appropriate node"""

        # take manager decision as default
        # so in human_review_routing it check if the manager decision exists then ok else approved to quality check if human review is not there
        # this decision is used to route the content whether to send to quality check or human review node

        decision = state.get("status", "approved")
        print(f"HUMAN REVIEW DECISION STATE: {state['status']}")
        #if decision == "awaiting_human_feedback":\
        #    return "awaiting_human_feedback"

        print(f"HUMAN REVIEW DECISION ROUTER: {decision}")

        # if human_review is given
        #if decision == "approved":
        return decision



    def human_feedback_node(self, state: WorkflowState)->WorkflowState:
        """Node for human feedback on content."""

        # print("\n" + "="*50)
        # print("HUMAN REVIEW REQUIRED")
        # print("="*50)
        # print(f"Current Content:\n{state.get('current_content', '')[:500]}...")
        # print(f"\nReviewer Feedback:\n{state.get('reviewer_feedback', '')}")
        # print(f"\nIteration: {state.get('iteration_count', 1)}")
        # # Simulate human decision (in real app, this comes from GUI)
        # human_feedback = "Content quality is acceptable, proceed to final check"
        # human_decision = "approved" # or "revision_needed" or "rejected"

        print(f"Human Feedback: {state['human_feedback']}")
        print(f"Current Status: {state['status']}")
        
        # if no feedback is there, then only pause the workflow, else the status is automatically changed from the streamlit app
        # using app.update_status(state["status"])

        # once feedback is recieved
        if state.get('status')=="approved":
            print("✅ Human feedback recieved, continue workflow.")

        elif state.get('status')=="rejected":
            print(f"The content is not acceptable, getting into rejected state. Human Feedback: {state['human_feedback']}")

        elif state.get('status')=="revision_needed":
            print(f"The content needs revisions, getting into revision_needed state. Human Feedback: {state['human_feedback']}")
        else:
            if state.get("human_feedback") in [None, "NO FEEDBACK"]:
                print(f"🛑 Waiting for human feedback. Workflow paused with status: {state['status']}")
                
                # interrupt keyword is used to pause the execution until user provides some feedback
                # interrupt is the key to pause the flow and return to object of current state
                print(f"Interrupting workflow...")

                # set the status to "awaiting human feedback"
                state["status"] = "awaiting_human_feedback"
                print(f"Current Status: {state['status']}")
                state["status"] = interrupt("awaiting_human_feedback")
                print(f"Current Status: {state['status']}")
                return state
            

        return {
            **state,
            "human_feedback": state["human_feedback"],
            #"manager_decision": state["manager_decision"],
            "messages": state.get("messages", [])+[HumanMessage(content=f"Human: {state['human_feedback']}")]
        }


from graphviz import Digraph

# Visualize the workflow graph
def visualize_with_graphviz(graph):
    dot = Digraph(comment="Workflow Graph")
    
    # Add nodes and edges
    for name, node in graph.nodes.items():
        dot.node(name, name)  # Add nodes
        for dep in node.inputs:
            dot.edge(dep, name)  # Add edges for dependencies
    
    return dot


# ### ==== FOR TESTING PURPOSES ==== ####
# if __name__=="__main__":

#     workflow = BookPublicationWorkflow()

#     # # # Get DOT representation
#     # #graphviz_dot = workflow.workflow.get_graph().draw()  # Returns a graphviz.Digraph object
#     # graphviz_dot = workflow.workflow.get_graph().draw(format='svg')
#     # # # Save to image
#     # # Draw it using graphviz
#     # graphviz = graphviz_dot.draw()

#     # graphviz_dot.render(filename="book_workflow", format="png", cleanup=True)

#     # Define a basic starting state (as per your TypedDict)
#     initial_state: WorkflowState = {
#         "original_content": "The sun was setting behind the hills as the village slowly came to life. Children ran across the fields while elders sat outside, sharing stories from the past.",
#         "instructions": "Make the prose more poetic and immersive.",
#         "current_content": "The sun was setting behind the hills as the village slowly came to life. Children ran across the fields while elders sat outside, sharing stories from the past.",
#         "writer_output": "",
#         "reviewer_feedback": "",
#         "manager_decision": "",
#         "human_feedback": "",
#         "iteration_count": 0,
#         "messages": [],
#         "status": "",
#         "metadata": {},
#         "quality_report": ""
#     }

#     ### Generate Mermaid diagram and save to file
#     from IPython.display import Image, display

#     # Get the PNG image bytes
#     image_bytes = workflow.app.get_graph().draw_mermaid_png()

#     # Save to file
#     with open("book_workflow_mermaid.png", "wb") as f:
#         f.write(image_bytes)

#     # Display (optional)
#     #display(Image("book_workflow_mermaid.png"))
    
#     import uuid

#     thread_id = str(uuid.uuid4())
    
#     config={"configurable": {"thread_id": thread_id}}

#     # run the compiled langgraph with initial state
#     final_state = workflow.app.invoke(initial_state,
#                                       config=config)

#      # Print final outputs
#     print("\n✅ FINAL OUTPUT:")
#     print("Status:", final_state["status"])
#     print("Manager Decision:", final_state["manager_decision"])
#     print("Iteration Count:", final_state["iteration_count"])
#     print("\n✍️ Final Content:\n", final_state["current_content"])
#     print("\n💬 Messages:")
#     for msg in final_state["messages"]:
#         print("-", msg.content)
