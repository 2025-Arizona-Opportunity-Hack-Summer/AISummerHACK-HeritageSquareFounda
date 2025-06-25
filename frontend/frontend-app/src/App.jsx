import { useState, useEffect, useRef } from 'react'
import './App.css'
import React from 'react';

function App() {
  const [query, setQuery] = useState('');
  const textAreaRef = useRef(null);

  const [discussion, setDiscussions] = useState([]);
  const discussionEndRef = useRef(null);
  
  // automatically scroll to most recent query and response
  const scrollToBottom = () => {
    discussionEndRef.current?.scrollIntoView({ 
      behavior: 'smooth', 
      block: 'end'
    });
  };

  // call scrollToBottom whenever discussion array updated
  useEffect(() => {
    scrollToBottom();
  }, [discussion]);
  
  // send query and get/display response and query in discussion
  const getQueryResponse = async (query) => {
    // move query into discussion
    const ogDiscussion = discussion;
    setDiscussions([...discussion, {id: discussion.length, query: query, response: "generating..."}])
    setQuery("");

    // send query and get response back
    try {
      await fetch(`/api/query?q=${encodeURIComponent(query)}`).then(res => res.json()).then(data => {
        setDiscussions([...ogDiscussion, {id: discussion.length, query: query, response: data.response}])
        console.log(data.response);
      });
    }
    catch {
      console.log("server error");
    }
  }

  // adjust query text area to expand based on query length
  useEffect(() => {
    const textarea = textAreaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';

      const lineHeight = parseFloat(getComputedStyle(textarea).lineHeight);
      const maxHeight = lineHeight * 6;

      textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden';
      textarea.style.height = Math.min(textarea.scrollHeight, maxHeight) + 'px';
    }
  }, [query]);

  return (
    <>
    <div>
      <ul>
        {discussion.length == 0 ? null : discussion.map(exchange => (
          <React.Fragment key={exchange.id}>
          <li className="query">
            {exchange.query}{' '}
          </li>
          <li className="response">
            {exchange.response}{' '}
          </li>
          </React.Fragment>
        ))}
      </ul>
      <div id="discussionEnd" ref={discussionEndRef}></div>
    </div>

    <div className="bottomBar">
      <textarea ref={textAreaRef} type="text" value={query} placeholder="Query" onChange={(e) => setQuery(e.target.value)}/>
      <br></br>
      <br></br>
      <button onClick={() => getQueryResponse(query)}>
          Enter query
      </button>
    </div>
    </>
  )
}

export default App
