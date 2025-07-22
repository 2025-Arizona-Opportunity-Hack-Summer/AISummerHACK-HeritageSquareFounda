import { useState, useEffect, useRef } from 'react'
import './App.css'
import React from 'react';

function App() {
  const [isMobile, setIsMobilte] = useState(false);
  const [msg, setMsg] = useState('');

  // variables for chat ui
  const [query, setQuery] = useState('');
  const textAreaRef = useRef(null);

  const [discussion, setDiscussions] = useState([]);
  const discussionEndRef = useRef(null);

  // variables for uploading files
  const [uploadingFiles, setUploadingFiles] = useState(false);
  const [files, setFiles] = useState([]);
  const inputRefs = useRef({});
  const inputIdCounter = useRef(0);

  // check screen size and set isMobile
  useEffect(() => {
    const handleResize = () => {
      setIsMobilte(window.innerWidth < 768);
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    return () => {
      window.removeEventListener('resize', handleResize);
    }
  }, []);
  

  /*
    Functions for chat ui
  */

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
    setMsg('')
    // move query into discussion
    const ogDiscussion = discussion;
    setDiscussions([...discussion, {id: discussion.length, query: query, response: "generating..."}])
    setQuery("");

    // send query and get response back (can be changed to use POST method)
    try {
      const response = await fetch(`/api/query?q=${encodeURIComponent(query)}`, {
        method: 'GET'
      });
      if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      
      setDiscussions([...ogDiscussion, {id: discussion.length, query: query, response: data.response}])
      console.log(data.response);
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
  }, [query, uploadingFiles]);


  /*
    Function for organizing files
  */
  const organizeFiles = async () => {
    setMsg('');
    // trigger file organization
    try {
      const response = await fetch(`/api/categorize`, {
        method: 'POST'
      });
      if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log(data.response);
      setMsg('Completed organizing files.');
    }
    catch (err) {
      console.log("Organizing failed:", err);
      setMsg('Failed to organize files.');
    }
  }

  /*
    Functions for uploading files
  */

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
      <label htmlFor="input-file">Choose Files</label>
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

  const uploadFiles = async () => {
    const formData = new FormData();

    files.forEach((fileObj, index) => {
      formData.append(`file${index}`, fileObj.file);
    })

    console.log("data being sent:");
    for (let pair of formData.entries()) {
      console.log(pair[0]+ ':', pair[1]);
    }

    // upload files to api
    try {
      const response = await fetch(`/api/upload`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log(data.response);
      setMsg('Uploaded files.');
    }
    catch (err) {
      console.log("Upload failed:", err);
      setMsg('Failed to upload files.');
    }
  }

  return (
    <>
    {/* discussion thread */}
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

    {/* main ui interface */}
    {!isMobile?
    /* for desktop */
    <div id="desktop">
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
          <button onClick={() => uploadFiles()}>Upload</button>
          <button onClick={() => {setUploadingFiles(!uploadingFiles); setFiles([]); setMsg('')}}>Cancel</button>
        </div>
      : null}

      <div id={"constantVisibility"}>
        <textarea ref={textAreaRef} type="text" value={query} placeholder="Prompt" onChange={(e) => setQuery(e.target.value)}/>

        {msg != ''?
        <p className="msg">{msg}</p>
        : null}

        <div className="buttonContainer">
          <button className="enter-btn" onClick={() => getQueryResponse(query)}>
              Enter Prompt
          </button>
          <div className="buttonSubContainer">
            <button onClick={() => organizeFiles()}>Organize Files</button>
            <button onClick={() => {setUploadingFiles(!uploadingFiles); setMsg('')}}>Upload Files</button>
          </div>
        </div>
      </div>
    </div>
    </div>
    : 
    <div id="mobile">
    <div className="bottomBar">
      {!uploadingFiles? 
      <div id={"constantVisibility"}>
        <textarea ref={textAreaRef} type="text" value={query} placeholder="Prompt" onChange={(e) => setQuery(e.target.value)}/>

        <div className="buttonContainer">
          <button className="enter-btn" onClick={() => getQueryResponse(query)}>
              Enter Prompt
          </button>

          {msg != ''?
          <p className="msg">{msg}</p>
          : null}

          <div className="buttonSubContainer">
            <button onClick={() => organizeFiles()}>Organize Files</button>
            <button onClick={() => {setUploadingFiles(!uploadingFiles); setMsg('')}}>Upload Files</button>
          </div>

        </div>
      </div>
      : 
      <div id={"constantVisibility"}>
        <div className="buttonContainer">

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

            <button onClick={() => uploadFiles()}>Upload</button>
            <button onClick={() => {setUploadingFiles(!uploadingFiles); setFiles([]); setMsg('')}}>Cancel</button>
          </div>

          <div className="buttonSubContainer">
            <button onClick={() => organizeFiles()}>Organize Files</button>
            <button onClick={() => {setUploadingFiles(!uploadingFiles); setMsg('')}}>Upload Files</button>
          </div>

        </div>
      </div>
      }
    </div>
    </div>
    }
    </>
  )
}

export default App
