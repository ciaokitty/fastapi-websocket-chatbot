from typing import Annotated
from fastapi import FastAPI, File, UploadFile, status, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

import os
from pathlib import Path
import uuid
import shutil

from typing import Dict, Set
import json
import sys
import aiofiles

from sqlalchemy.orm import sessionmaker
from models import engine, Document
from rag import RAGHandler

MAX_FILE_SIZE = 30 * 1024 * 1024  # 30MB in bytes
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Add custom exception classes
class FileUploadError(Exception):
    def __init__(self, filename: str, message: str):
        self.filename = filename
        self.message = message
        super().__init__(self.message)

class FileSizeError(FileUploadError):
    pass

class FileTypeError(FileUploadError):
    pass

# Add connection manager class
class ConnectionManager:
    def __init__(self):
        # Store active connections and their associated document IDs
        self.active_connections: Dict[str, WebSocket] = {}
        # Store session IDs that are allowed to connect (users who have uploaded docs)
        self.authorized_sessions: Set[str] = set()

    async def connect(self, websocket: WebSocket, session_id: str):
        print(f"Attempting to connect session: {session_id}")  # Debug print
        print(f"Authorized sessions: {self.authorized_sessions}")  # Debug print
        
        if session_id not in self.authorized_sessions:
            print(f"Session {session_id} not authorized")  # Debug print
            await websocket.close(code=1008, reason="Upload documents first")
            return False
            
        await websocket.accept()
        self.active_connections[session_id] = websocket
        print(f"Session {session_id} connected successfully")  # Debug print
        return True

    async def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(message)

    def authorize_session(self, session_id: str):
        self.authorized_sessions.add(session_id)

manager = ConnectionManager()

# Add these near the top with your other global variables
db_session = sessionmaker(bind=engine)
rag_handler = RAGHandler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Clean up uploads directory on startup
    if UPLOAD_DIR.exists():
        shutil.rmtree(UPLOAD_DIR)
    UPLOAD_DIR.mkdir(exist_ok=True)
    
    # Clear the database
    with db_session() as session:
        session.query(Document).delete()
        session.commit()
    
    yield
    
    # Cleanup on shutdown (optional)
    if UPLOAD_DIR.exists():
        shutil.rmtree(UPLOAD_DIR)

# Update FastAPI initialization to use lifespan
app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:5173",
    "http://localhost:8501",
    # Add WebSocket origins
    "ws://localhost:8000",
    "ws://localhost:5173",
    "*"  # For development only - remove in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Add these settings for WebSocket support
    allow_origin_regex=".*",
    expose_headers=["*"]
)



@app.post("/uploadfiles/")
async def create_upload_files(
    files: Annotated[list[UploadFile], File(description="Multiple files as UploadFile")],
    status_code=status.HTTP_201_CREATED,
):
    saved_files = []
    errors = []
    
    for file in files:
        try:
            if not file.filename:
                raise FileUploadError(file.filename, "Filename is missing")

            # Read file content
            try:
                contents = await file.read()
            except Exception as e:
                raise FileUploadError(file.filename, f"Failed to read file: {str(e)}")

            # Check file size
            file_size = len(contents)
            if file_size > MAX_FILE_SIZE:
                raise FileSizeError(
                    file.filename,
                    f"File size {file_size / (1024 * 1024):.2f}MB exceeds the limit of 30MB"
                )
            
            # Check file extension and MIME type
            if not file.filename.endswith('.pdf') or file.content_type != 'application/pdf':
                raise FileTypeError(
                    file.filename,
                    f"Invalid file type. Only PDF files are allowed (got {file.content_type})"
                )
            
            # Generate and save file with unique name
            original_name = Path(file.filename).stem
            file_extension = Path(file.filename).suffix
            unique_filename = f"{original_name}_{uuid.uuid4()}{file_extension}"
            file_path = UPLOAD_DIR / unique_filename
            
            try:
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(contents)
            except IOError as e:
                raise FileUploadError(file.filename, f"Failed to save file: {str(e)}")
            
            saved_files.append({
                "original_name": file.filename,
                "saved_name": unique_filename
            })
                
        except (FileUploadError, FileSizeError, FileTypeError) as e:
            errors.append({
                "filename": e.filename,
                "error": e.message
            })
        except Exception as e:
            errors.append({
                "filename": getattr(file, 'filename', 'Unknown'),
                "error": f"Unexpected error: {str(e)}"
            })
            
    response = {"files": saved_files}
    if errors:
        response["errors"] = errors
        
    if not saved_files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "No files were successfully uploaded",
                "errors": errors
            }
        )
        
    if saved_files:
        # Generate a session ID for this upload
        session_id = str(uuid.uuid4())
        # Authorize this session for WebSocket connections
        manager.authorize_session(session_id)
        # Add session_id to the response
        response["session_id"] = session_id

    # After successful upload, save to database
    with db_session() as session:
        for file_info in saved_files:
            doc = Document(
                id=str(uuid.uuid4()),
                filename=file_info["original_name"],
                saved_name=file_info["saved_name"]
            )
            session.add(doc)
        session.commit()

    return response


@app.get("/")
async def main():
    content = """
<body>
<form action="/uploadfiles/" enctype="multipart/form-data" method="post">
<input name="files" type="file" multiple>
<input type="submit">
</form>
</body>
    """
    return HTMLResponse(content=content)


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    try:
        print(f"WebSocket connection attempt from session: {session_id}")
        is_connected = await manager.connect(websocket, session_id)
        
        if not is_connected:
            print(f"Connection rejected for session: {session_id}")
            return

        print(f"WebSocket connected for session: {session_id}")
        
        # Load documents for this session
        with db_session() as session:
            documents = session.query(Document).all()
            if not documents:
                print(f"No documents found for session: {session_id}")
                await manager.send_message("No documents found for this session", session_id)
                return
                
            pdf_paths = [os.path.join(UPLOAD_DIR, doc.saved_name) for doc in documents]
            print(f"Loading PDFs: {pdf_paths}")
            
            try:
                await rag_handler.load_and_process_pdfs(pdf_paths)
                await manager.send_message("PDFs loaded successfully. You can now ask questions.", session_id)
            except Exception as e:
                print(f"Error loading PDFs: {str(e)}")
                await manager.send_message(f"Error loading PDFs: {str(e)}", session_id)
                return
        
        while True:
            question = await websocket.receive_text()
            print(f"Received question: {question}")
            response = await rag_handler.get_answer(question)
            print(f"Sending response: {response}")
            await manager.send_message(response, session_id)
            
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for session: {session_id}")
        await manager.disconnect(session_id)
    except Exception as e:
        print(f"Error in websocket handler: {str(e)}")
        print(f"Full error details: {sys.exc_info()}")
        await manager.disconnect(session_id)

# Add this new endpoint for REST API access
@app.post("/ask")
async def ask_question(question: str, session_id: str):
    if session_id not in manager.authorized_sessions:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Upload documents first"
        )
    
    # Load documents if not already loaded
    with db_session() as session:
        documents = session.query(Document).all()
        pdf_paths = [os.path.join(UPLOAD_DIR, doc.saved_name) for doc in documents]
        rag_handler.load_and_process_pdfs(pdf_paths)
    
    response = await rag_handler.get_answer(question)
    return {"answer": response}