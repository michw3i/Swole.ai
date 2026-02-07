import { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import './App.css'
import supabase from './supabaseClient'
import ImageUpload from './components/ImageUpload'
import ChatBox from './components/ChatBox'
import SignIn from './pages/SignIn'

function Main() {
  const [uploadedImage, setUploadedImage] = useState(null)
  const [messages, setMessages] = useState([])
  const navigate = useNavigate()

  const handleSignOut = async () => {
    await supabase.auth.signOut()
    navigate('/signin')
  }

  return (
    <div className="app-container">
      <header>
        <img src="/swole_ai_logo_embedded.svg" alt="Swole.ai" className="app-logo" />
        <h1>Swole.ai</h1>
        <button className="btn-signout" onClick={handleSignOut}>Sign out</button>
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
  )
}

export default function App() {
  const [session, setSession] = useState(undefined)

  useEffect(() => {
    if (!supabase) {
      setSession(null)
      return
    }

    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
    }).catch(() => {
      setSession(null)
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
    })

    return () => subscription.unsubscribe()
  }, [])

  if (session === undefined) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', color: '#777' }}>
        Loading...
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/signin" element={session ? <Navigate to="/" /> : <SignIn />} />
      <Route path="/*" element={session ? <Main /> : <Navigate to="/signin" />} />
    </Routes>
  )
}
