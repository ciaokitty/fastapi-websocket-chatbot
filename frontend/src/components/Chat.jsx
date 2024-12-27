import React, { useState, useEffect, useRef } from 'react';

function Chat() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [ws, setWs] = useState(null);
    const [sessionId, setSessionId] = useState(null);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        const isAtBottom = messagesEndRef.current && messagesEndRef.current.getBoundingClientRect().bottom <= window.innerHeight;
        if (isAtBottom) {
            scrollToBottom();
        }
    }, [messages]);

    const handleFileUpload = async (e) => {
        const files = e.target.files;
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
                const websocket = new WebSocket(`ws://localhost:8000/ws/${data.session_id}`);

                websocket.onmessage = (event) => {
                    try {
                        const sanitizedData = event.data.replace(/<[^>]*>?/gm, ''); // Basic HTML tag sanitization
                        setMessages((prev) => [...prev, { text: sanitizedData, sender: 'ai' }]);
                    } catch (error) {
                        console.error('Error processing WebSocket message:', error);
                    }
                };

                websocket.onerror = () => {
                    console.error('WebSocket connection failed.');
                };

                setWs(websocket);
            } else {
                console.error('No session_id returned from the server.');
            }
        } catch (error) {
            console.error('Error uploading file:', error);
        }
    };

    const sendMessage = (e) => {
        e.preventDefault();
        if (!input.trim() || !ws) return;

        setMessages((prev) => [...prev, { text: input, sender: 'user' }]);
        ws.send(input);
        setInput('');
    };

    // Reusable CSS classes for message bubbles
    const userBubbleClass = 'bg-blue-500 text-white rounded-br-none';
    const aiBubbleClass = 'bg-gray-200 text-gray-800 rounded-bl-none';
    const commonBubbleClass = 'max-w-[70%] p-3 rounded-lg shadow-md text-sm';

    return (
        <div className="h-screen w-screen flex items-center justify-center bg-gray-100">
            <div className="w-full h-full max-w-[1200px] flex flex-col bg-white">
                {/* Header */}
                <div className="bg-green-500 p-4 flex justify-between items-center text-white">
                    <h1 className="text-lg font-bold">AI Chat</h1>
                    <div>
                        <input
                            type="file"
                            onChange={handleFileUpload}
                            multiple
                            accept=".pdf"
                            className="hidden"
                            id="file-upload"
                        />
                        <label
                            htmlFor="file-upload"
                            className="bg-white text-green-600 px-4 py-2 rounded cursor-pointer hover:bg-gray-100"
                        >
                            Upload PDF
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
                                className={`${commonBubbleClass} ${message.sender === 'user' ? userBubbleClass : aiBubbleClass}`}
                            >
                                {message.text}
                            </div>
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Form */}
                <form onSubmit={sendMessage} className="p-4 border-t bg-white">
                    <div className="flex space-x-4">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Type your message..."
                            className="flex-1 p-2 border rounded-lg focus:outline-none focus:border-green-500 text-sm"
                            disabled={!sessionId}
                        />
                        <button
                            type="submit"
                            disabled={!sessionId}
                            className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 disabled:bg-gray-300"
                        >
                            Send
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default Chat;
