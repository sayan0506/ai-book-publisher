# chroma_manager.py
# chroma db manager for AI book publication
import os, sys
import json
import chromadb
#from chromadb.config import Settings
from datetime import datetime
from utils.config import Config 
from typing import List, Dict, Optional
import uuid
from google.cloud import storage
from google.auth.exceptions import DefaultCredentialsError
import logging
# used for temporary file creation
import tempfile

logger = logging.getLogger(__name__)


class ChromaManager:
    def __init__(self):
        self.config = Config()

        # initialize the gcloud client for uploading files to GCS bucket
        try: 
            self.storage_client = storage.Client(
                project=self.config.PROJECT_ID,
            )
            
            self.bucket = self.storage_client.get_bucket(self.config.GCS_BUCKET_NAME)
            logger.info(f"Connected to Google Cloud Storage Bucket {self.bucket.name}")
        
        except DefaultCredentialsError as e:
            logger.warning("GCS credentials not found,  using local storage")
            self.storage_client = None
            self.bucket = None
        
        # setup chromaDB path
        self.chroma_path = self._setup_chroma_path()

        try:
            # store the books on chromadb database
            self.client = chromadb.PersistentClient(path = self.chroma_path)
            # create collection
            self.collection = self.client.get_or_create_collection(
                name="book_content",
                metadata={
                    "description": "Book Content with versions"
                }
            )
            logger.info(f"CheomaDB initialized at {self.chroma_path}")

        except Exception as e:
            logger.error(f"Failed to connect to ChromaDB: {e}")
        

    def _setup_chroma_path(self)->str:
        """
        Setup chroma path with gcloud bucket or local path
        """
        if self.bucket:
            local_path = os.path.join(tempfile.gettempdir(), "chroma_db")
            os.makedirs(local_path, exist_ok=True)

            # download existing chromadb data from GCS if exists
            self._download_chroma_from_gcs(local_path)

            return local_path
        else:
            os.makedirs(self.config.CHROMA_DB_PATH, exist_ok=True)
            return self.config.CHROMA_DB_PATH
    

    def _download_chroma_from_gcs(self, local_path:str):
        """Download chromaDB from gcs, for chroma we need local path,
        so we upload chroma to local path after operation, and before operation
        we download gcs data from bucket to local path"""
        if not self.bucket:
            return
        
        try:
            # check the blobs or folders in the bucket
            blobs = self.bucket.list_blobs(prefix="chroma_db/")

            for blob in blobs:
                # create local file path
                relative_path = blob.name.replace("chroma_db/","")
                if not relative_path or blob.name.endswith("/"): # skip directory makers and use root
                    continue 

                local_file_path = os.path.join(local_path, relative_path)

                # create directories if needed
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

                # download the file
                blob.download_to_filename(local_file_path)
                logger.debug(f"Downloaded {blob.name} to {local_file_path}")

            logger.info("ChromaDB downloaded successfully from GCS")

        except Exception as e:
            logger.error(f"Failed to download ChromaDB from GCS: {e}")


    def _upload_chroma_to_gcs(self):
        """Upload chromaDB to gcs, for chroma wye need local path,
        so we upload chroma to local path after operation, and before operation
        we download gcs data from bucket to local path"""
        if not self.bucket:
            return
        
        try:
            # upload all file in chroma directory
            for root, dirs, files in os.walk(self.chroma_path):
                for file in files:
                    local_file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_file_path, self.chroma_path)
                    gcs_path = f"chroma_db/{relative_path}"

                    blob = self.bucket.blob(gcs_path) 
                    blob.upload_from_filename(local_file_path)
                    logger.debug(f"Uploaded {local_file_path} to {gcs_path}")

                logger.info("ChromaDB uploaded successfully to GCS")
        
        except Exception as e:
            logger.error(f"Failed to upload ChromaDB to GCS: {e}")



    def store_content(self, content: str, metadata: Dict)-> str:
        """
        Store content with metadata and return document ID"""

        doc_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Add timestamp to metadata
        metadata.update(
            {
                "timestamp": timestamp,
                "doc_id": doc_id
            }
        )

        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )

        if self.bucket:
            self._upload_chroma_to_gcs()

        logger.info(f"Content stored with ID: {doc_id}")
        return doc_id
    
    
    def get_content(self, doc_id:str)->Optional[Dict]:
        """Retrieve content by document ID, can return optionally if content exists"""
        results = self.collection.get(ids=[doc_id])

        if results["documents"]:
            return {
                'content': results['documents'][0],
                'metadata': results['metadatas'][0]
            }
        
        return None 
    
    def search_content(self, query: str, n_results: int=5)->List[Dict]:
        """Search content using semantic similarity"""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

        content_list = [0]

        for i, doc in enumerate(results["documents"][0]):
            content_list.append({
                'content':doc,
                'results': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })

        return content_list
    

    def get_version(self, chapter_id:str)->List[Dict]:
        """Get all versions of a specific chapter"""

        results = self.collection.get(
            where={"chapter_id": chapter_id}
        )

        versions = []

        for i, doc in enumerate(results['documents'][0]):
            versions.append({
                'content': doc,
                'metadata': results['metadatas'][0][i]
            }
            )

        # sort by timestamp
        versions.sort(key=lambda x: x['metadata']['timestamp'])

        return versions

