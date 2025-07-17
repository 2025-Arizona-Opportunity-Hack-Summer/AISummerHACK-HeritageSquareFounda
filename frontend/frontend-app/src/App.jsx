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
      setDiscussions([...ogDiscussion, {id: discussion.length, query: query, response: "An error has occurred"}]);
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


  /*
    Variable and functions for uploading files
  */
  const [uploadingFiles, setUploadingFiles] = useState(false);
  const [files, setFiles] = useState([]);
  const inputRefs = useRef({});
  const inputIdCounter = useRef(0);

  const handleFileChange = (event, inputId) => {
    const file = event.target.files[0];

    // add file to list
    if (file){
      setFiles((prev) => [...prev, {id: inputId, file: event.target.files[0]}]);
      inputIdCounter.current += 1;
    }
  };

  const renderFileInputs = (nextInputId) => {
    return (
      <>
      <label htmlFor="input-file">Choose File</label>
      <input
        id="input-file"
        key={nextInputId}
        type="file"
        accept=".pdf, .doc, .docx"
        onChange={(event) => handleFileChange(event, nextInputId)}
        ref={(ref) => (inputRefs.current[nextInputId] = ref)}
      />
      </>
    )
  }

  const removeFile = (fileIndex) => {
    setFiles((prev) => prev.filter((fileObj) => fileObj.id !== fileIndex));
    delete inputRefs.current[fileIndex];
  }

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
      {uploadingFiles?
        <div className="fileUploadContainer">
          {renderFileInputs(inputIdCounter.current)}
        
          <div id="fileList">
          {files.toReversed().map((item) => (
            <li key={item.id}>
              <p>{item.file.name}</p>
              <button onClick={() => {removeFile(item.id)}}>X</button>
            </li>
          ))}
          </div>
          <button>Upload Files</button>
          <button onClick={() => {setUploadingFiles(!uploadingFiles); setFiles([]);}}>Cancel</button>
        </div>
      : null}

      <div id={"constantVisibility"}>
        <textarea ref={textAreaRef} type="text" value={query} placeholder="Prompt" onChange={(e) => setQuery(e.target.value)}/>

        <div className="buttonContainer">
          <button id={"enter-btn"} onClick={() => getQueryResponse(query)}>
              Enter prompt
          </button>
          <div className="buttonSubContainer">
            <button>Organize Files</button>
            <button onClick={() => setUploadingFiles(!uploadingFiles)}>Upload Files</button>
          </div>
        </div>
      </div>
    </div>
    </>
  )
}

export default App
