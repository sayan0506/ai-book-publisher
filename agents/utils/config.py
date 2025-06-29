# utils/config.py
import os
from dotenv import load_dotenv
# define workflowstate
from typing import Dict, List, Optional, TypedDict, Annotated
import operator


# define state schema for our workflow(state signature or schema that will be boradcasted)
# across various nodes of langgraph workflow
class WorkflowState(TypedDict):
	original_content: str
	instructions: str 
	current_content: str
	messages: Annotated[List, operator.add]
	writer_output: str
	reviewer_feedback: str
	manager_decision: str
	human_feedback: str
	iteration_count: int
	status: str
	metadata: dict
	quality_report: str


load_dotenv()

class Config:
	"""Configuration class for the application."""
	CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
	GCS_BUCKET_NAME = "script_ref_v2"

	SCREENSHOTS_PATH = os.getenv("SCREENSHOTS_PATH", "./screenshots")
	
    # GCP settings
	PROJECT_ID = "bootcampai-460711"
	LOCATION = "us-central1"
	
    ## vertex AI model infos
	MODEL_NAME = "gemini-2.0-flash"

    # Default URLs 
	DEFAULT_URL = "https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1"
	
    # AI Settings
	GEMINI_OUTPUT_TOKEN_LIMIT = 8192
	MAX_TOKENS = 4000
	TEMPERATURE = 0.7
	
    # Workflow settings
	MAX_ITERATIONS = 5
	
	CHROMA_DB_PATH = "./chroma_db"