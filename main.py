# AI Book Publication
# design the workflow for AI book publication
import asyncio
import streamlit as st
import os
from book_workflow import BookPublicationWorkflow
from chroma_manager import ChromaManager
from utils.config import Config
from PIL import Image
import json
from utils.config import Config, WorkflowState
from scraper import ContentScraper
import uuid
from langgraph.types import Command


# Page configuration
st.set_page_config(
    page_title="Automated Book Publication System",
    page_icon="📚",
    layout="wide",
)

# Initialize session state if not initialized
if "workflow" not in st.session_state:
    # this session state focuses on BookPublication workflow
    # so it contains the workflow object and its initial state
    st.session_state.workflow = BookPublicationWorkflow()

if "workflow_state" not in st.session_state:
    st.session_state.workflow_state = None

if "current_state" not in st.session_state:
    st.session_state.current_state = None 

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None # Explicitly initialize as None


if "storage" not in st.session_state:
    # stores the storage object used to store the content and version control and all utility functions
    # stores chroma manager object to manage the content storage and retrieval
    st.session_state.storage = ChromaManager()

# Initialize a new thread ID for a fresh start
if not st.session_state.thread_id:
    st.session_state.thread_id = str(uuid.uuid4())
    


def main():
    st.title("📚 Automated Book Publication System")
    st.markdown("---")

    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Workflow", "Content Management", "Search & Retrieval"]
    )
    
    if page == "Workflow":
        workflow_page()
    elif page == "Content Management":
        content_management_page()
    elif page == "Search & Retrieval":
        search_retrieval_page()

async def scrape_and_process_content(scraper: ContentScraper, initial_state: WorkflowState)-> WorkflowState:
    await scraper.setup_directories()
    print(f"Initial State: {initial_state}")
    current_state = await scraper.scrape_content(initial_state)

    return current_state


# --- Helper Function to Get Current Workflow State from Checkpointer ---
def get_current_workflow_state() -> WorkflowState:
    """Retrieves the current state of the LangGraph workflow from the checkpointer."""
    if st.session_state.thread_id:
        try:
            # LangGraph's app.get_state requires the configurable dict
            # Make sure this is called on the compiled app
            checkpoint = st.session_state.workflow.app.get_state(
                config={"configurable": {"thread_id": st.session_state.thread_id}}
            )
            # The checkpoint object has a .values attribute which contains the state dictionary
            return checkpoint.values
        except Exception as e:
            st.error(f"Error retrieving workflow state: {e}")
            return None
    return None



def workflow_page():
    st.header("AI Book Publication Workflow")

    # URL Input
    url = st.text_input(
        "Enter URL to scrape: ",
        value = Config.DEFAULT_URL,
        help = "Enter the URL of the content you want to process"
    )

    # Start the workflow
    col1, col2 = st.columns(2)

    with col1:
        if st.button("Start workflow", type="primary"):
            if url:
                # initialize scraper with base url
                scraper = ContentScraper(url)

                # # Initialize a new thread ID for a fresh start
                # st.session_state.thread_id = str(uuid.uuid4())
                st.session_state.workflow_state = None # Clear previous state for a new run
                #st.session_state.workflow_config = {"configurable": {"thread_id": st.session_state.thread_id}}

                # initialize the workflow
                initial_state : WorkflowState = {
                    "original_content": "",
                    "instructions": "",
                    "current_content": "",
                    "messages": [],
                    "writer_output": "",
                    "reviewer_feedback": "NO FEEDBACK",
                    "manager_decision": "NO DECISION",
                    "human_feedback": "NO FEEDBACK",
                    "iteration_count": 0,
                    "status": "initialized",
                    "metadata": {},
                    "quality_report": ""
                }
                
                print(f"1. Scraping content... {type(initial_state)}")

                # Staep 1. start scraping state
                # as streamlit doesnt support async function call we need to use asyncio.run() to run the async function
                st.session_state.current_state = asyncio.run(scrape_and_process_content(scraper, initial_state))
                #print(f"Current State: {st.session_state.current_state}") # debug print to check state st.session_state.current_state)
                print("Scraping complete!!")

                if st.session_state.current_state is not None:
                    st.success("Workflow started successfully !!!")
                    try:
                        # display_workflow_state()
                        if st.session_state.current_state["status"]=="scraped":
                            
                            # Step 2. start workflow
                            #if st.session_state.workflow is None:
                            #st.session_state.workflow = BookPublicationWorkflow()
                            print("Starting workflow...")

                            # Generate unique thread ID for this workflow instance, so that
                            # streamlit can track or point that theread to acquire the current state
                            # as the checkpoint is captured in the same thread


                            # if st.session_state.current_state: 
                            #     display_workflow_state()
                            #print(st.session_state.current_state)
                            result = st.session_state.workflow.app.invoke(
                                st.session_state.current_state,
                                config={"configurable": {"thread_id": st.session_state.thread_id}})
                            
                            print(f"Workflow result: {result.get('status', 'unknown')}")

                            st.write(f"Quality Report: {result.get('quality_report', 'unknown')}")
                            #st.session_state.workflow_state = result 
                            
                            #st.session_state.current_state = st.session_state.workflow.app.state
                            #st.session_state.workflow.start_workflow(st.session_state.current_state)
                            #st.session_state.current_state = st.session_state.workflow.current_state
                            
                    except Exception as e:
                        st.error(f"Error occurred during workflow execution: {e}")
                    
                else:
                    st.error("Failed to scrape content, Failed to start the workflow.")
                    return

    with col2:
        if st.button("🔄 Reset Workflow"):
            st.session_state.current_state = None
            st.rerun()
    
    # so while the workflow is running everytime before displaying the workflow_state it retrieving current langgraph state to the st workflow state variable
    if st.session_state.thread_id:
        st.session_state.workflow_state = get_current_workflow_state()
    
    # check about the status of the workflow
    # if st.session_state.workflow_state.get("status") == "awaiting_human_feedback":
    #     st.info("🔄 Workflow paused - waiting for human feedback")
    # else:
    #     st.success("✅ Workflow completed successfully!")
    # Display current state
    if st.session_state.workflow_state:
        display_workflow_state()


def display_workflow_state():
    state = st.session_state.workflow_state
    
    #st.subheader(f"Current Status: {state['status'].title()}")

    # # Progress indicator 
    # progress_steps = ["scraped",""]

    # Display contents in tabs
    tabs = st.tabs([
        "📄 OriginSal Content",
        "🌀 Spun Content",
        "🧐 Review",
        "🧠 Manager Decision",
        "🧍 Human Feedback"
    ])


    with tabs[0]:
        st.write(state.get('original_content',"No original content available."))
            
    with tabs[1]:
       st.write(state.get('current_content',"No spun content available."))
         
    with tabs[2]:
        st.write(state.get('reviewer_feedback',"No reviewer feedback available."))

    with tabs[3]:
        st.write(state.get('manager_decision',"No manager decision available."))

    with tabs[4]:
        st.write(state.get('human_feedback', "No human feedback available."))

    print("Displaying workflow state")
    print(f"Current State: {st.session_state.workflow_state['status']}") # debug print to check state st.session_state.current_state)
    # Human feedback section
    #if st.session_state.workflow_state["status"]=="awaiting_human_feedback":
    if "human_review" in st.session_state.workflow_state["status"]:

        st.session_state.workflow_state["status"] = "awaiting_human_feedback"
        print("Displaying human feedback")
        st.subheader("Human Feedback")

        col1, col2 = st.columns([2,1])

        with col1:
            feedback = st.text_area(
                "Provide feedback for improvement:",
                placeholder="Enter specific instructions for the next iteration...",
                height=100
            )

        with col2:
            st.markdown("**Interation:** "+ str(st.session_state.workflow_state['iteration_count']))
            #st.markdown("**Max Interations:** "+ str[state[]])
        
        # Action buttons
        #col1, col2, col3 = st.columns(3)
        col_actions = st.columns(3)

        with col_actions[0]:
            if st.button("✅ Approve & Finalize", type="primary"):
                st.session_state.workflow_state["human_feedback"] =  "Human feedback: " + feedback 
                st.session_state.workflow_state["status"] = "approved"
                
                try:
                    print(f"Finalizing workflow status : {st.session_state.workflow_state['status']}")
                    print(f"Feedback: {st.session_state.workflow_state['human_feedback']}")
                    # resume workflow where it was paused
                    # the Command(resume) helps to resume the workflow from where it was interrupted
                    # and we pas the thread id to identify the correct thread to resume
                    print(f"Type of {type(st.session_state.workflow_state)}")
                    # update langgraph state
                    st.session_state.workflow.app.update_state(
                        config = {"configurable": {"thread_id": st.session_state.thread_id}},
                        values = st.session_state.workflow_state)
                    
                    # resume the workflow
                    result = st.session_state.workflow.app.invoke(Command(resume=f"Feedback: {st.session_state.workflow_state['human_feedback']}"),
                                                                config={"configurable": {"thread_id": st.session_state.thread_id}})
                    # result = st.session_state.workflow.app.invoke(st.session_state.workflow_state,
                    #                                             config={"configurable": {"thread_id": st.session_state.thread_id}})
                    st.session_state.workflow_state = result 
                    
                    st.write(f"Quality Report: {result.get('quality_report', 'unknown')}")
                    #print(f"Finalized result: {st.session_state.workflow.app.state.get('quality_report', 'unknown')}")

                except Exception as e:
                    st.error(f"Error finalizing workflow: {e}")

        with col_actions[1]:
            if st.button("❌ Reject & Restart", type="secondary"):
                st.session_state.workflow_state["human_feedback"] =  "Human feedback: " + feedback
                st.session_state.workflow_state["status"] = "rejected"

                try:
                    st.session_state.workflow.app.update_state(
                        config = {"configurable": {"thread_id": st.session_state.thread_id}},
                        values = st.session_state.workflow_state
                    )

                    # resume the workflow
                    result = st.session_state.workflow.app.invoke(Command(resume=f"Feedback for rejection: {st.session_state.workflow_state['human_feedback']}"),
                                                                    config={"configurable": {"thread_id": st.session_state.thread_id}})
                    
                    st.session_state.workflow_state = result 
                    print(f"Finalized result: {st.session_state.workflow.app.state.get('quality_report', 'unknown')}")
                    
                    st.write(f"Quality Report: {result.get('quality_report', 'unknown')}")
                    st.write(f"Feedback for rejection: {st.session_state.workflow_state['human_feedback']}")


                except Exception as e:
                    st.error(f"Error finalizing workflow: {e}")

        with col_actions[2]:
            if st.button("🔄 Request Revision", type="secondary"):
                st.session_state.workflow_state["human_feedback"] =  "Human feedback: " + feedback
                st.session_state.workflow_state["status"] = "revision_needed"

                print("Requesting revision...")
                try:
                    # update the workflowstate
                    st.session_state.workflow.app.update_state(
                        config = {"configurable": {"thread_id": st.session_state.thread_id}},
                        values = st.session_state.workflow_state
                    )

                    # resume the workflow
                    result = st.session_state.workflow.app.invoke(Command(resume=f"Feedback for revision: {st.session_state.workflow_state['human_feedback']}"),
                                                                    config={"configurable": {"thread_id": st.session_state.thread_id}})
                    
                    st.session_state.workflow_state = result 

                    st.write(f"Quality Report: {st.session_state.workflow.app.state.get('quality_report', 'unknown')}")
                    #st.write(f"Feedback for revision: {st.session_state.workflow_state['human_feedback']}")
                    print(f"Quality Report: {result.get('quality_report', 'unknown')}")

                except Exception as e:
                    st.error(f"Error finalizing workflow: {e}")
        

def content_management_page():
    st.header("📊 Content Management")

    # Get all stored content
    storage = st.session_state.storage

    st.subheader("Stored Content")

    # simple query to get all documents
    try:
        # get all documents by querying with generic term
        all_content = storage.search_content("content", n_results=50)

        if all_content:
            for i,item in enumerate(all_content):
                if isinstance(item,dict):
                    with st.expander(f"Document {i+1} - {item['results'].get('type','unknown')}"):
                        # this means 2 rows and 1 column
                        col1, col2 = st.columns([2,1])

                        with col1:
                            st.text_area(f"Content {i+1}",item['content'][:500]+ "...")

                        with col2:
                            # in this db results = metadata
                            st.json(item['results'])

        else:
            st.info("No content stored yet. Run the workflow to generate content.")
        
    except Exception as e:
        st.error(f"Error retrieving stored content: {str(e)}")

def search_retrieval_page():
    st.header("🔍 Search & Retrieval")

    # search interface
    search_query = st.text_input("Enter search query:", placeholder = "Search for content")

    if st.button("🔍 Search") and search_query:
        # session state is the global variable or pointer object for st session
        # chromamanager object
        storage = st.session_state.storage

        with st.spinner("Searching..."):
            results = storage.search_content(search_query, n_results = 10)

        if results:
            st.subheader(f"Found {len(results)} results")
            #print(f"Results: {results}")
            #print(f"Results: {type(results)}")
            for i, result in enumerate(results):
                if isinstance(result, dict):
                    with st.expander(f"Result {i+1} (Distance: {result['distance']:.3f})"):
                        st.text_area(f"Content ", result['content'][:1000] + "...", height=200, disabled=True)
                        print(f"Keys {result.keys()}")
                        # in the chromamanager class result is the metadata
                        st.json(result['results'])
        else:
            st.info("No results found")

        # Recent content
        st.subheader("📅 recent Content")
        try:
            recent_content = st.session_state.storage.search_content("recent", n_results=5)
            for i, result in enumerate(recent_content):
                with st.expander(f"Recent {i+1} - {result['metadata'].get('timestamp', 'Unknow time')}"):
                    st.text(result['content'][:300]+"...")
        except Exception as e:
            st.info("No recent content available.")



if __name__ == "__main__":
    main()