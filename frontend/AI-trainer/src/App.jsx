import { useState } from 'react';
import './App.css';
import ImageUpload from './components/ImageUpload';
import ChatBox from './components/ChatBox';

function App() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [messages, setMessages] = useState([]);

  return (
    <div className="app-container">
      <header>
        <h1>AI Fitness Trainer</h1>
      </header>
      
      <div className="main-content">
        <ImageUpload 
          uploadedImage={uploadedImage}
          setUploadedImage={setUploadedImage}
        />
        
        <ChatBox 
          messages={messages}
          setMessages={setMessages}
          uploadedImage={uploadedImage}
        />
      </div>
    </div>
  );
}

export default App;