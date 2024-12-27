import React, { useState, useEffect, useRef } from 'react';

function Chat() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [sessionId, setSessionId] = useState(null);
    const [websckt, setWebsckt] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isAiResponding, setIsAiResponding] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // WebSocket connection effect
    useEffect(() => {
        if (!sessionId) return;

        // Add protocol check and error handling
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//localhost:8000/ws/${sessionId}`;
        console.log('Attempting to connect to:', wsUrl);
        
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('WebSocket Connected');
            setMessages(prev => [...prev, {
                text: 'PDFs loaded successfully! You can now ask questions.',
                sender: 'system'
            }]);
        };

        ws.onmessage = (event) => {
            try {
                // Skip the initial connection message from the server if it matches
                if (event.data.includes("PDFs loaded successfully")) {
                    return;
                }
                
                const sanitizedData = event.data.replace(/<[^>]*>?/gm, '');
                setMessages(prev => [...prev, { 
                    text: sanitizedData, 
                    sender: 'ai' 
                }]);
                setIsAiResponding(false);
            } catch (error) {
                console.error('Error processing WebSocket message:', error);
                setIsAiResponding(false);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setMessages(prev => [...prev, {
                text: 'Error connecting to chat server',
                sender: 'system'
            }]);
        };

        ws.onclose = () => {
            console.log('WebSocket Disconnected');
            setMessages(prev => [...prev, {
                text: 'Disconnected from chat server',
                sender: 'system'
            }]);
        };

        setWebsckt(ws);

        // Cleanup on unmount
        return () => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        };
    }, [sessionId]);

    const handleFileUpload = async (e) => {
        const files = e.target.files;
        if (!files.length) return;

        setIsLoading(true);
        const formData = new FormData();

        for (let file of files) {
            formData.append('files', file);
        }

        try {
            const response = await fetch('http://localhost:8000/uploadfiles/', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();
            console.log('Upload response:', data);

            if (data.session_id) {
                setSessionId(data.session_id);
            } else {
                throw new Error('No session ID returned from server');
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            setMessages(prev => [...prev, {
                text: `Error: ${error.message}`,
                sender: 'system'
            }]);
        } finally {
            setIsLoading(false);
        }
    };

    const sendMessage = (e) => {
        e.preventDefault();
        if (!input.trim() || !websckt || websckt.readyState !== WebSocket.OPEN) return;

        // Add user message to chat
        setMessages(prev => [...prev, { 
            text: input, 
            sender: 'user' 
        }]);

        // Show loading state
        setIsAiResponding(true);

        // Send message through WebSocket
        websckt.send(input);
        setInput('');
    };

    // Reusable CSS classes
    const userBubbleClass = 'bg-blue-500 text-white rounded-br-none';
    const aiBubbleClass = 'bg-gray-200 text-gray-800 rounded-bl-none';
    const systemBubbleClass = 'bg-yellow-100 text-gray-800 rounded-lg';
    const commonBubbleClass = 'max-w-[70%] p-3 rounded-lg shadow-md text-sm';

    return (
        <div className="h-screen w-screen flex items-center justify-center bg-gray-100">
            <div className="w-full h-full max-w-[1200px] flex flex-col bg-white">
                {/* Header */}
                <div className="bg-green-500 p-4 flex justify-between items-center text-white">
                    <h1 className="text-lg font-bold">PDF Chat Assistant</h1>
                    <div>
                        <input
                            type="file"
                            onChange={handleFileUpload}
                            multiple
                            accept=".pdf"
                            className="hidden"
                            id="file-upload"
                            disabled={isLoading}
                        />
                        <label
                            htmlFor="file-upload"
                            className={`bg-white px-4 py-2 rounded cursor-pointer hover:bg-gray-100 
                                ${isLoading ? 'text-gray-400' : 'text-green-600'}`}
                        >
                            {isLoading ? 'Processing...' : 'Upload PDFs'}
                        </label>
                    </div>
                </div>

                {/* Chat Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
                    {messages.map((message, index) => (
                        <div
                            key={index}
                            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`${commonBubbleClass} 
                                    ${message.sender === 'user' ? userBubbleClass : 
                                      message.sender === 'ai' ? aiBubbleClass : 
                                      systemBubbleClass}`}
                            >
                                {message.text}
                            </div>
                        </div>
                    ))}
                    {isAiResponding && (
                        <div className="flex justify-start">
                            <div className={`${commonBubbleClass} ${aiBubbleClass}`}>
                                <div className="flex items-center space-x-2">
                                    <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                    <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                    <div className="w-2 h-2 bg-gray-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Form */}
                <form onSubmit={sendMessage} className="p-4 border-t bg-white">
                    <div className="flex space-x-4">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={sessionId ? "Ask a question about your PDFs..." : "Upload PDFs to start chatting"}
                            className="flex-1 p-2 border rounded-lg focus:outline-none focus:border-green-500 text-sm"
                            disabled={!sessionId || isLoading}
                        />
                        <button
                            type="submit"
                            disabled={!sessionId || isLoading}
                            className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 
                                disabled:bg-gray-300 disabled:cursor-not-allowed"
                        >
                            {isLoading ? 'Processing...' : 'Send'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default Chat;
