from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

class RAGHandler:
    def __init__(self):
        self.vectorstore = None
        self.initialize_llm()
    
    def initialize_llm(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0,
            max_tokens=None,
            timeout=None,
            google_api_key=GOOGLE_API_KEY
        )
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=GOOGLE_API_KEY
        )
    
    async def load_and_process_pdfs(self, pdf_paths):
        try:
            # Run the synchronous PDF loading in a thread pool
            documents = []
            for path in pdf_paths:
                # Use run_in_executor for CPU-bound operations
                loader = PyPDFLoader(path)
                docs = await asyncio.get_event_loop().run_in_executor(None, loader.load)
                documents.extend(docs)
            
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000)
            docs = await asyncio.get_event_loop().run_in_executor(
                None, 
                text_splitter.split_documents, 
                documents
            )
            
            # Create vector store
            self.vectorstore = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: FAISS.from_documents(documents=docs, embedding=self.embeddings)
            )
            
            return True
            
        except Exception as e:
            print(f"Error in load_and_process_pdfs: {str(e)}")
            raise
    
    async def get_answer(self, query: str) -> str:
        try:
            if not self.vectorstore:
                return "No documents have been loaded yet."
            
            system_prompt = (
                "You are a question-answering assistant. Use the retrieved context to answer the user's question. "
                "If unsure, say you don't know. Keep your response concise, using up to three sentences."
                "\n\n"
                "{context}"
            )
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}"),
            ])
            
            retriever = self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 10})
            question_answer_chain = create_stuff_documents_chain(self.llm, prompt)
            rag_chain = create_retrieval_chain(retriever, question_answer_chain)
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: rag_chain.invoke({"input": query})
            )
            return response["answer"]
            
        except Exception as e:
            print(f"Error in get_answer: {str(e)}")
            return f"Error processing your question: {str(e)}"