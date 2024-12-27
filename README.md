## Setup Instructions

To set up this project, follow these steps:

1. **Clone the Repository:**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Backend Setup:**

   - **Python Environment:**
     - Ensure you have Python 3.10 or higher installed.
     - Create a virtual environment:
     - I have used uv to create my python virtual environment and to manage the various python dependencies. However you can do the same with the good old venv.
       ```bash
       python -m venv venv
       ```
     - Activate the virtual environment:
       - On Windows:
         ```bash
         .\venv\Scripts\activate
         ```
       - On macOS and Linux:
         ```bash
         source venv/bin/activate
         ```

   - **Install Dependencies:**
     - Install the required Python packages. They are listed in the `pyproje.toml` file
       

   - **Environment Variables:**
     - Create a `.env` file in the backend directory and add necessary environment variables, such as `GOOGLE_API_KEY`.

   - **Run the Backend Server:**
     - Navigate to the backend directory 
       ```bash
        cd backend
        ```
     -  and start the FastAPI server:
        ```bash
        fastapi dev main.py
        ```
        This will require the fastapi[standard] package for fastapi cli. You can alternately start the server via:
        ```bash
        uvicorn backend.main:app --reload
        ```

3. **Frontend Setup:**

   - **Node.js Environment:**
     - Ensure you have Node.js and npm installed. Node.js version I have used is v20.17.0

   - **Install Dependencies:**
     - Navigate to the frontend directory
        ```bash
         cd frontend
         ```
     - and install the required packages:
       ```bash
       npm install
       ```

   - **Run the Frontend Server:**
     - Start the development server:
       ```bash
       npm run dev
       ```

4. **Access the Application:**
   - Open your browser and go to `http://localhost:5173` to access the frontend.
   - The backend server should be running on `http://localhost:8000`.

## Application Structure Overview

- **Frontend:**
  - Built with React and Vite.
  - Main entry point is `frontend/src/main.jsx` (startLine: 1, endLine: 10).
  - Styles are managed using Tailwind CSS, configured in `frontend/tailwind.config.js` (startLine: 1, endLine: 11).
  - The main application component is `frontend/src/App.jsx` (startLine: 1, endLine: 12).
  - Chat functionality is implemented in `frontend/src/components/Chat.jsx` (startLine: 1, endLine: 227).

- **Backend:**
  - Built with FastAPI.
  - Main entry point is `backend/main.py` (startLine: 1, endLine: 120).
  - Handles file uploads and WebSocket connections for real-time chat.
  - Uses SQLAlchemy for database interactions, defined in `backend/models.py` (startLine: 1, endLine: 17).
  - Document processing and retrieval are managed by `backend/rag.py` (startLine: 1, endLine: 92).

- **Database:**
  - SQLite database is used, with models defined in `backend/models.py`.

- **RAG**
  - Implemented with the help of Langchain and Google Gemini Api for generating vector embeddings and RAG.

- **Environment Configuration:**
  - Environment variables are managed using a `.env` file, with dotenv loading them in `backend/rag.py` (startLine: 1, endLine: 13).

This setup will allow you to run the application locally and explore its features.

## Live demo via screencast
https://github.com/ciaokitty/fastapi-websocket-chatbot/raw/refs/heads/main/demo/demo.mp4

