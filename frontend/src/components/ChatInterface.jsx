
import React, { useState, useEffect, useRef } from 'react';
import { flushSync } from 'react-dom';
import { Send, User, Bot, Loader2, Image as ImageIcon, X, Mic, MicOff, FileText, Scale, Search, Briefcase, Shield, Users, Mail } from 'lucide-react';

import { LegalAnalysisCard, ContractReviewCard, LegalResearchCard, CaseManagementCard, ComplianceCard, LegalCorrespondenceCard, AssessmentCard, SmartFollowupCard, GeneralCard } from './ResponseCards';

import './ChatInterface.css';

// Bootstrap guidance - clean single-prompt cards, no multi-question interrogation
const BOOTSTRAP_GUIDANCE = {
  'contract': {
    title: '📄 Contract Analysis & Review',
    summary: 'Analyse contracts, NDAs, and agreements with risk assessment.',
    prompt: 'Upload a contract, NDA, or agreement to begin — or describe the contract situation below.',
    examples: [
      "Review this NDA for a potential partnership. Focus on the non-compete clause.",
      "Analyse this service agreement. Check liability limitations and termination provisions.",
      "Review this employment contract for unfavorable IP assignment terms."
    ]
  },
  'research': {
    title: '🔍 Legal Research',
    summary: 'Search case law, statutes, and legal precedents.',
    prompt: 'What legal question do you need researched? Describe the issue, jurisdiction, and any relevant facts.',
    examples: [
      "Research case law on breach of fiduciary duty in Delaware corporate law.",
      "Find precedents for non-compete enforceability in California.",
      "Research the statute of limitations for contract claims in New York."
    ]
  },
  'case': {
    title: '📋 Case Management',
    summary: 'Track deadlines, manage case workflow, and monitor filings.',
    prompt: 'Describe the case you want to manage — or upload case documents to extract key details automatically.',
    examples: [
      "Create a case timeline for Smith v. Jones. Discovery deadline is March 15.",
      "Track upcoming deadlines for the pending merger transaction.",
      "Update case status and list pending tasks for the IP infringement matter."
    ]
  },
  'compliance': {
    title: '🛡️ Compliance Review',
    summary: 'Audit regulatory compliance and assess risk.',
    prompt: 'Upload a policy or contract — or describe the compliance requirement you need assessed.',
    examples: [
      "Audit our data processing practices for GDPR compliance.",
      "Review our financial reporting controls for SOX compliance.",
      "Assess regulatory compliance for our new product launch in the EU."
    ]
  },
  'intake': {
    title: '📝 Case Intake',
    summary: 'Onboard new clients and create case profiles.',
    prompt: 'Briefly describe the new client and their legal matter to create a case profile.',
    examples: [
      "New client ABC Corporation — commercial lease dispute.",
      "Client John Smith — employment discrimination claim.",
      "New client XYZ Inc. — contract negotiation with vendor."
    ]
  },
  'correspondence': {
    title: '✉️ Legal Correspondence',
    summary: 'Draft client letters, legal notices, and demand letters.',
    prompt: 'Describe the letter or notice you need drafted — who it is to, from, and the key message.',
    examples: [
      "Draft a demand letter for unpaid invoices.",
      "Prepare a legal notice for breach of contract to XYZ Ltd.",
      "Draft a cease-and-desist letter for trademark infringement."
    ]
  },
  'legal': {
    title: '⚖️ Legal Analysis',
    summary: 'Get legal opinions and case strategy.',
    prompt: 'Upload a document for analysis — or describe the legal situation and the specific advice you need.',
    examples: [
      "Assess our liability in a slip-and-fall incident at our retail location.",
      "Evaluate the strength of our non-compete enforcement against a former employee.",
      "Provide a strategic assessment for defending a breach of contract claim."
    ]
  }
};

const BOOTSTRAP_COMMANDS = {
  contract: {
    id: 'contract',
    caption: '📄 Contract Analysis',
    command: 'I want to analyze a contract or agreement.',
    isBootstrap: true,
    forceAgent: 'ContractAnalysisAgent'
  },
  research: {
    id: 'research',
    caption: '🔍 Legal Research',
    command: 'I need to research case law, statutes, or legal precedents.',
    isBootstrap: true,
    forceAgent: 'LegalResearchAgent'
  },
  case: {
    id: 'case',
    caption: '📋 Case Management',
    command: 'I need help managing case deadlines and workflow.',
    isBootstrap: true,
    forceAgent: 'CaseManagementAgent'
  },
  compliance: {
    id: 'compliance',
    caption: '�️ Compliance Review',
    command: 'I need a compliance audit or regulatory assessment.',
    isBootstrap: true,
    forceAgent: 'ComplianceAgent'
  },
  intake: {
    id: 'intake',
    caption: '� Case Intake',
    command: 'I want to start a new client intake and case profile.',
    isBootstrap: true,
    forceAgent: 'CaseIntakeAgent'
  },
  correspondence: {
    id: 'correspondence',
    caption: '✉️ Legal Correspondence',
    command: 'I need to draft a legal letter or notice.',
    isBootstrap: true,
    forceAgent: 'LegalCorrespondenceAgent'
  },
  legal: {
    id: 'legal',
    caption: '⚖️ Legal Analysis',
    command: 'I need a legal opinion or case strategy advice.',
    isBootstrap: true,
    forceAgent: 'LawyerAgent'
  }
};

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:3334';
const TRANSCRIBE_URL = `${BACKEND_URL}/audio/transcribe`;

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `<div style="margin:0;">
        <span>Welcome to <strong>LexEdge Legal AI</strong>. I am your legal assistant. How can I help you today?</span>
      </div>`,
      agent: 'LexEdge',
      suggestions: [
        BOOTSTRAP_COMMANDS.contract,
        BOOTSTRAP_COMMANDS.research,
        BOOTSTRAP_COMMANDS.case,
        BOOTSTRAP_COMMANDS.compliance,
        BOOTSTRAP_COMMANDS.intake,
        BOOTSTRAP_COMMANDS.correspondence,
        BOOTSTRAP_COMMANDS.legal
      ]
    }
  ]);
  const [input, setInput] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);  // keeps file metadata
  const [imagePreview, setImagePreview] = useState(null);    // kept for legacy display
  const [selectedFileData, setSelectedFileData] = useState(null); // { b64, mime_type, filename }
  const [showImageOptions, setShowImageOptions] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isProcessingFile, setIsProcessingFile] = useState(false);
  const [documentPages, setDocumentPages] = useState([]);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [recordingMimeType, setRecordingMimeType] = useState('audio/webm');
  const [isAwaitingResponse, setIsAwaitingResponse] = useState(false);
  const [activeAgent, setActiveAgent] = useState(null); // Force agent for bootstrap commands
  const fileInputRef = useRef(null);
  const inputRef = useRef(null);
  const isUnmounting = useRef(false);
  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const mediaStreamRef = useRef(null);
  const recordingTimerRef = useRef(null);

  // Voice Agent Refs
  const voiceSocketRef = useRef(null);
  const audioContextRef = useRef(null);
  const audioWorkletNodeRef = useRef(null);
  const audioPlayerNodeRef = useRef(null);
  const isVoiceActive = useRef(false);
  const [voiceStatus, setVoiceStatus] = useState('idle'); // idle, connecting, listening, speaking

  useEffect(() => {
    isUnmounting.current = false;
    connectWebSocket();
    return () => {
      isUnmounting.current = true;
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => track.stop());
        mediaStreamRef.current = null;
      }
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }

      // Cleanup Voice Session
      stopVoiceSession();
    };
  }, []);


  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const connectWebSocket = () => {
    if (isUnmounting.current) return;

    if (socketRef.current && (socketRef.current.readyState === WebSocket.OPEN || socketRef.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    setIsConnecting(true);
    const wsUrl = BACKEND_URL.replace('http', 'ws');
    const ws = new WebSocket(`${wsUrl}/ws?session_id=demo_session&tenant_id=default`);

    ws.onopen = () => {
      if (isUnmounting.current) {
        ws.close();
        return;
      }
      console.log('Connected to WebSocket');
      setIsConnected(true);
      setIsConnecting(false);
    };

    ws.onmessage = (event) => {
      if (isUnmounting.current) return;
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'response') {
          setIsAwaitingResponse(false);
          setMessages(prev => prev.filter(m => m.type !== 'ack'));

          // Normalize suggestions
          const suggestions = data.action_suggestions?.suggestions || data.suggestions || [];
          const newContent = data.formatted_response || data.response;

          // SPECIAL HANDLING FOR STAGE 2 UPDATES (Suggestions without new content)
          // If we receive suggestions but NO content (or empty string), 
          // we attach them to the LAST assistant message instead of creating a new bubble.
          if ((!newContent || newContent.trim() === "") && suggestions.length > 0) {
            console.log("Received async suggestions update:", suggestions);

            setMessages(prev => {
              // Polyfill-like behavior for findLastIndex
              let lastIdx = -1;
              for (let i = prev.length - 1; i >= 0; i--) {
                if (prev[i].role === 'assistant') {
                  lastIdx = i;
                  break;
                }
              }

              if (lastIdx !== -1) {
                console.log("Merging suggestions into message index:", lastIdx);
                // Clone the array
                const updated = [...prev];
                // Update the last message with new suggestions
                updated[lastIdx] = {
                  ...updated[lastIdx],
                  suggestions: suggestions
                };
                return updated;
              }
              // If no previous assistant message, fallback to default behavior
              return [...prev, {
                role: 'assistant',
                content: "",
                agent: data.agent,
                suggestions: suggestions
              }];
            });
          } else {
            // STANDARD BEHAVIOR: New Message
            setMessages(prev => [...prev, {
              role: 'assistant',
              content: newContent,
              agent: data.agent,
              suggestions: suggestions
            }]);
          }
        } else if (data.type === 'ack') {
          setMessages(prev => {
            const filtered = prev.filter(m => m.type !== 'ack');
            return [...filtered, {
              role: 'system',
              content: data.message,
              type: 'ack'
            }];
          });
        } else if (data.type === 'processing_cancelled') {
          setIsAwaitingResponse(false);
          setMessages(prev => prev.filter(m => m.type !== 'ack'));
        }
      } catch (e) {
        console.error('Error parsing message:', e);
      }
    };

    ws.onclose = () => {
      if (isUnmounting.current) return;
      console.log('WebSocket disconnected');
      setIsConnected(false);
      setIsConnecting(false);
      setIsAwaitingResponse(false);
      setTimeout(() => {
        if (!isUnmounting.current && (!socketRef.current || socketRef.current.readyState === WebSocket.CLOSED)) {
          connectWebSocket();
        }
      }, 3000);
    };

    ws.onerror = (error) => {
      if (isUnmounting.current) return;
      console.error('WebSocket error:', error);
      setIsConnected(false);
      setIsConnecting(false);
      setIsAwaitingResponse(false);
    };

    socketRef.current = ws;
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  // Read a file as Base64
  const readFileAsBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result); // data URI: "data:<mime>;base64,..."
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const handleFileSelect = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const fileType = file.type;
    const fileName = file.name.toLowerCase();

    const isPDF = fileType === 'application/pdf' || fileName.endsWith('.pdf');
    const isDOCX = fileType === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' || fileName.endsWith('.docx');
    const isDOC = fileType === 'application/msword' || fileName.endsWith('.doc');
    const isTXT = fileType === 'text/plain' || fileName.endsWith('.txt');

    if (!isPDF && !isDOCX && !isDOC && !isTXT) {
      alert('Unsupported file type. Please upload a PDF, Word document (.doc/.docx), or text file (.txt).');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    setIsProcessingFile(true);
    try {
      const dataUri = await readFileAsBase64(file);
      const mimeType = fileType || 'application/octet-stream';

      setSelectedImage(file);          // keep file object for metadata
      setSelectedFileData({ b64: dataUri, mime_type: mimeType, filename: file.name });
      setImagePreview(null);           // no visual preview for documents
      setDocumentPages([]);

      // If a role/agent is already active, auto-dispatch for analysis immediately
      if (activeAgent) {
        const filename = file.name;
        const autoQuery = `Please analyse the attached document: ${filename}`;
        const userMsg = { role: 'user', content: `📄 Analysing: ${filename}` };
        setMessages(prev => [...prev, userMsg]);
        setIsAwaitingResponse(true);
        const payload = {
          type: 'query',
          query: autoQuery,
          user_id: 'demo_user',
          data: { image_b64: dataUri, mime_type: mimeType, filename },
          force_agent: activeAgent,
          timestamp: Date.now()
        };
        // Wait a tick so socket is ready, then send
        setTimeout(() => {
          if (socketRef.current) socketRef.current.send(JSON.stringify(payload));
        }, 50);
        // Clear state
        setSelectedImage(null);
        setSelectedFileData(null);
        setShowImageOptions(false);
        if (fileInputRef.current) fileInputRef.current.value = '';
      } else {
        setShowImageOptions(true);     // show 'document ready' panel for manual dispatch
      }

      console.log(`[FILE] Loaded ${file.name} (${mimeType}), b64 length: ${dataUri.length}`);
    } catch (err) {
      console.error('Error reading file:', err);
      alert('Failed to read the file. Please try again.');
    } finally {
      setIsProcessingFile(false);
    }
  };

  const startRecording = async () => {
    if (isRecording || isTranscribing) return;
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        alert('Audio recording is not supported in this browser.');
        return;
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      const supportedTypes = [
        'audio/webm;codecs=opus',
        'audio/ogg;codecs=opus',
        'audio/webm',
        'audio/ogg'
      ];
      const mimeType = supportedTypes.find(type => MediaRecorder.isTypeSupported(type)) || 'audio/webm';
      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      setRecordingMimeType(mimeType);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType });
        await transcribeAudio(audioBlob);
        if (mediaStreamRef.current) {
          mediaStreamRef.current.getTracks().forEach(track => track.stop());
          mediaStreamRef.current = null;
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingSeconds(0);
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
      }
      recordingTimerRef.current = setInterval(() => {
        setRecordingSeconds(prev => prev + 1);
      }, 1000);
    } catch (err) {
      console.error('Microphone access denied:', err);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsTranscribing(true);
      if (recordingTimerRef.current) {
        clearInterval(recordingTimerRef.current);
        recordingTimerRef.current = null;
      }
    }
  };

  const transcribeAudio = async (audioBlob) => {
    try {
      const formData = new FormData();
      const mimeType = recordingMimeType || audioBlob.type || 'audio/webm';
      const extension = mimeType.includes('ogg') ? 'ogg' : mimeType.includes('wav') ? 'wav' : 'webm';
      formData.append('file', audioBlob, `recording.${extension}`);

      const response = await fetch(TRANSCRIBE_URL, {
        method: 'POST',
        body: formData,
        headers: {
          Accept: 'application/json'
        }
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Transcription failed (${response.status}): ${errorText}`);
      }

      const data = await response.json();
      console.log('Transcription response:', data);
      if (data.status === 'success' && data.transcript) {
        const transcript = data.transcript;
        console.log('Sending transcript to chat:', transcript);

        // Add user message to chat UI
        const userMsg = {
          role: 'user',
          content: `🎤 ${transcript}`, // Add microphone emoji to valid transcript
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, userMsg]);

        // Send to WebSocket if connected
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
          setIsAwaitingResponse(true);
          const payload = {
            type: 'query',
            query: transcript,
            session_id: 'demo_session',
            user_id: 'demo_user',
            data: null,
            force_agent: activeAgent, // Pass forced agent
            timestamp: Date.now()
          };
          socketRef.current.send(JSON.stringify(payload));
          console.log('Sent transcript to WebSocket with agent:', activeAgent);
        }
        return;
      } else {
        console.log('Transcription returned but no transcript or status not success:', data);
        if (data.transcript === "") {
          alert('No speech detected. Please try again.');
        }
      }
    } catch (err) {
      console.error('Transcription failed:', err);
      alert('Transcription failed. Please try again.');
    } finally {
      setIsTranscribing(false);
    }
  };

  const formatRecordingTime = (seconds) => {
    const mins = String(Math.floor(seconds / 60)).padStart(2, '0');
    const secs = String(seconds % 60).padStart(2, '0');
    return `${mins}:${secs}`;
  };

  // --- Voice Agent Logic ---

  const convertFloat32ToPCM = (inputData) => {
    const pcm16 = new Int16Array(inputData.length);
    for (let i = 0; i < inputData.length; i++) {
      pcm16[i] = inputData[i] * 0x7fff;
    }
    return pcm16.buffer;
  };

  const startVoiceSession = async () => {
    if (isVoiceActive.current) return;

    try {
      setVoiceStatus('connecting');

      // 1. Setup Audio Context & Worklets
      const audioContext = new AudioContext({ sampleRate: 24000 }); // ADK often uses 16k or 24k, let's match response
      audioContextRef.current = audioContext;

      // Load Worklets
      await audioContext.audioWorklet.addModule('/worklets/pcm-recorder-processor.js');
      await audioContext.audioWorklet.addModule('/worklets/pcm-player-processor.js');

      // 2. Setup Microphone (Recorder)
      const stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, sampleRate: 16000 } });
      const source = audioContext.createMediaStreamSource(stream);
      const recorderNode = new AudioWorkletNode(audioContext, 'pcm-recorder-processor');

      recorderNode.port.onmessage = (event) => {
        if (voiceSocketRef.current && voiceSocketRef.current.readyState === WebSocket.OPEN) {
          // Convert float32 to int16 PCM
          const pcmData = convertFloat32ToPCM(event.data);
          // Send as binary
          voiceSocketRef.current.send(pcmData);
        }
      };

      source.connect(recorderNode);
      // Keep references to clean up
      audioWorkletNodeRef.current = { source, node: recorderNode, stream };

      // 3. Setup Player
      const playerNode = new AudioWorkletNode(audioContext, 'pcm-player-processor');
      playerNode.connect(audioContext.destination);
      audioPlayerNodeRef.current = playerNode;

      // 4. Connect WebSocket
      const userId = 'demo_user'; // Consistent with other parts
      const sessionId = 'voice-' + Math.random().toString(36).substring(7);

      const wsUrl = `ws://${window.location.host.split(':')[0]}:3334/ws/voice?user_id=${userId}&session_id=${sessionId}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("Voice WebSocket Open");
        setVoiceStatus('listening');
        isVoiceActive.current = true;

        // Send initial bootstrap command
        const bootstrapMsg = JSON.stringify({
          type: "text",
          text: "Context: You are the LexEdge Legal AI. Please introduce yourself and ask how you can assist with the legal matter."
        });
        ws.send(bootstrapMsg);
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.outputTranscription && data.outputTranscription.text) {
          setVoiceStatus('speaking');
        }

        // Play audio if present
        if (data.content && data.content.parts) {
          data.content.parts.forEach(part => {
            if (part.inlineData && part.inlineData.data) {
              // Decode Base64
              const binaryString = window.atob(part.inlineData.data);
              const len = binaryString.length;
              const bytes = new Uint8Array(len);
              for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
              }
              // Send to player worklet
              if (audioPlayerNodeRef.current) {
                audioPlayerNodeRef.current.port.postMessage(bytes.buffer);
              }
            }
          });
        }

        if (data.turnComplete) {
          setVoiceStatus('listening');
        }
      };

      ws.onclose = () => {
        console.log("Voice WebSocket Closed");
        stopVoiceSession();
      };

      voiceSocketRef.current = ws;

    } catch (e) {
      console.error("Failed to start voice session:", e);
      alert("Could not start voice session. Check console.");
      setVoiceStatus('idle');
    }
  };

  const stopVoiceSession = () => {
    isVoiceActive.current = false;
    setVoiceStatus('idle');

    if (voiceSocketRef.current) {
      voiceSocketRef.current.close();
      voiceSocketRef.current = null;
    }

    if (audioWorkletNodeRef.current) {
      const { stream, node } = audioWorkletNodeRef.current;
      stream.getTracks().forEach(t => t.stop());
      node.disconnect();
      audioWorkletNodeRef.current = null;
    }

    if (audioPlayerNodeRef.current) {
      audioPlayerNodeRef.current.disconnect();
      audioPlayerNodeRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
  };

  const removeImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    setSelectedFileData(null);
    setShowImageOptions(false);
    setDocumentPages([]);
    setCurrentPageIndex(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Navigate multi-page documents
  const goToPage = (index) => {
    if (index >= 0 && index < documentPages.length) {
      setCurrentPageIndex(index);
      setImagePreview(documentPages[index]);
    }
  };

  const handleDocumentAnalysis = () => {
    if (!selectedImage || !isConnected) return;

    const filename = selectedFileData?.filename || selectedImage.name || 'document';
    const command = `Please analyse the attached document: ${filename}`;

    const userMsg = {
      role: 'user',
      content: `📄 Document Analysis — ${filename}`,
    };
    setMessages(prev => [...prev, userMsg]);

    if (socketRef.current) {
      setIsAwaitingResponse(true);
      const payload = {
        type: 'query',
        query: command,
        user_id: 'demo_user',
        data: selectedFileData ? {
          image_b64: selectedFileData.b64,
          mime_type: selectedFileData.mime_type,
          filename: selectedFileData.filename
        } : null,
        force_agent: activeAgent,
        timestamp: Date.now()
      };
      socketRef.current.send(JSON.stringify(payload));
    }

    removeImage();
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if ((!input.trim() && !selectedImage) || !isConnected || isTranscribing) return;

    const currentInput = input;
    const currentImage = imagePreview;

    const userMsg = {
      role: 'user',
      content: currentInput || "Please analyse the uploaded document.",
      image: currentImage
    };
    setMessages(prev => [...prev, userMsg]);

    if (socketRef.current) {
      setIsAwaitingResponse(true);

      // Build message_data — prefer raw file bytes (selectedFileData) over PNG preview
      let messageData = null;
      if (selectedFileData) {
        // Document upload: send raw bytes for server-side text extraction
        messageData = {
          image_b64: selectedFileData.b64,
          mime_type: selectedFileData.mime_type,
          filename: selectedFileData.filename
        };
      } else if (currentImage) {
        // Fallback for any remaining image path
        messageData = {
          image_b64: currentImage,
          mime_type: selectedImage?.type || 'image/png'
        };
      }

      const payload = {
        type: 'query',
        query: currentInput,
        user_id: 'demo_user',
        data: messageData,
        force_agent: activeAgent,
        timestamp: Date.now()
      };
      console.log('Sending with force_agent:', activeAgent, 'data mime:', messageData?.mime_type);
      socketRef.current.send(JSON.stringify(payload));
    }

    setInput('');
    removeImage();
  };

  const getAgentAvatar = (agentName) => {
    if (!agentName) return 'http://localhost:3334/static/agents/dr_generic.png';
    const name = agentName.toLowerCase();

    // Legal Agent Mappings
    if (name.includes('lawyer') || name.includes('counsel') || name.includes('lead')) return 'http://localhost:3334/static/agents/dr_insight.png';
    if (name.includes('research')) return 'http://localhost:3334/static/agents/dr_insight.png';
    if (name.includes('doc') || name.includes('contract')) return 'http://localhost:3334/static/agents/dr_lens.png';
    if (name.includes('case') || name.includes('manage')) return 'http://localhost:3334/static/agents/dr_synapse.png';
    if (name.includes('intake') || name.includes('router')) return 'http://localhost:3334/static/agents/dr_neuron.png';
    if (name.includes('compliance')) return 'http://localhost:3334/static/agents/dr_beat.png';
    if (name.includes('coach') || name.includes('prompt')) return 'http://localhost:3334/static/agents/dr_breath.png';
    if (name.includes('lexedge') || name.includes('legal')) return 'http://localhost:3334/static/agents/dr_generic.png';

    return 'http://localhost:3334/static/agents/dr_generic.png';
  };

  const handleSuggestionClick = (suggestion) => {
    if (!isConnected) return;

    // Check if this is a bootstrap command that needs guidance
    if (suggestion.isBootstrap && BOOTSTRAP_GUIDANCE[suggestion.id]) {
      const guidance = BOOTSTRAP_GUIDANCE[suggestion.id];

      // Set the forced agent for subsequent queries
      // Set the forced agent for subsequent queries
      if (suggestion.forceAgent) {
        setActiveAgent(suggestion.forceAgent);
        console.log('Set active agent to:', suggestion.forceAgent);
      }

      // VOICE BOOTSTRAP HANDLING
      if (suggestion.isVoice) {
        const guidanceMsg = {
          role: 'assistant',
          content: `
              <div style="margin:0;">
                <div style="background: linear-gradient(135deg, #4f46e5 0%, #818cf8 100%); border-radius: 12px; padding: 20px; color: white; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                   <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                      <div style="background: rgba(255,255,255,0.2); padding: 8px; border-radius: 50%;">
                         <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                           <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
                           <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                         </svg>
                      </div>
                      <h3 style="margin: 0; font-size: 1.2rem; font-weight: 600;">${guidance.title}</h3>
                   </div>
                   <p style="margin: 0 0 20px 0; line-height: 1.5; opacity: 0.9;">${guidance.summary}</p>
                   
                   ${suggestion.id === 'onboarding' ? `
                     <button id="btn-start-voice-${Date.now()}" class="voice-start-btn" style="
                        background: white; 
                        color: #4f46e5; 
                        border: none; 
                        padding: 12px 24px; 
                        border-radius: 30px; 
                        font-weight: 600; 
                        cursor: pointer; 
                        display: flex; 
                        align-items: center; 
                        gap: 8px;
                        transition: transform 0.2s;
                     ">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M12 2a3 3 0 0 1 3 3v7a3 3 0 0 1-6 0V5a3 3 0 0 1 3-3z"></path>
                          <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
                        </svg>
                        Start Voice Session
                     </button>
                   ` : ''}
                </div>
              </div>
            `,
          agent: 'LexEdge AI',
          isGuidance: true,
          bootstrapId: suggestion.id,
          isVoiceGuidance: true
        };

        setMessages(prev => [...prev, { role: 'user', content: suggestion.caption }, guidanceMsg]);

        // Hack to attach event listener after render because of dangerouslySetInnerHTML
        setTimeout(() => {
          const btns = document.getElementsByClassName('voice-start-btn');
          for (let btn of btns) {
            btn.onclick = (e) => {
              e.target.innerHTML = 'Connecting...';
              e.target.disabled = true;
              startVoiceSession();
            };
          }
        }, 100);

        return;
      }

      // Add user's selection as a message
      const userMsg = {
        role: 'user',
        content: suggestion.caption,
      };

      // Build a clean, single-line guidance card — no interrogation
      // (guidance already declared above from BOOTSTRAP_GUIDANCE lookup)
      const guidanceMsg = {
        role: 'assistant',
        content: `<div style="margin:0;">
          <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 12px; padding: 16px 18px; border-left: 4px solid #0284c7;">
            <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
              <span style="font-size:1.2rem;">${guidance.title.split(' ')[0]}</span>
              <strong style="color:#0369a1; font-size:1rem;">${guidance.title.replace(/^\S+\s/, '')}</strong>
            </div>
            <p style="margin:0 0 14px 0; color:#475569; font-size:0.9rem; line-height:1.5;">${guidance.prompt}</p>
            <div style="
              display:flex;
              align-items:center;
              gap:14px;
              background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
              border-radius:10px;
              padding:14px 16px;
              box-shadow: 0 4px 12px rgba(2,132,199,0.35);
              animation: lexUploadPulse 2s ease-in-out infinite;
            ">
              <div style="
                background:rgba(255,255,255,0.2);
                border-radius:50%;
                width:42px;
                height:42px;
                display:flex;
                align-items:center;
                justify-content:center;
                flex-shrink:0;
                font-size:1.4rem;
              ">📎</div>
              <div>
                <div style="color:#fff; font-weight:700; font-size:0.95rem; margin-bottom:3px;">Upload a Document to Begin</div>
                <div style="color:rgba(255,255,255,0.85); font-size:0.8rem; line-height:1.4;">Click the <strong style="color:#fff;">📎 icon</strong> in the bottom-left of the input bar. Your document will be analysed instantly in <strong style="color:#fff;">${guidance.title.replace(/^\S+\s/, '')}</strong> mode — no extra steps needed.</div>
              </div>
            </div>
          </div>
          <style>
            @keyframes lexUploadPulse {
              0%, 100% { box-shadow: 0 4px 12px rgba(2,132,199,0.35); }
              50% { box-shadow: 0 4px 22px rgba(2,132,199,0.65); }
            }
          </style>
        </div>`,
        agent: 'LexEdge AI',
        isGuidance: true,
        examples: guidance.examples || [],
        bootstrapId: suggestion.id
      };

      setMessages(prev => [...prev, userMsg, guidanceMsg]);
      setInput('');
      return;
    }

    // Regular suggestion - send to backend
    const userMsg = {
      role: 'user',
      content: suggestion.caption || suggestion.command,
    };
    setMessages(prev => [...prev, userMsg]);

    // Send to backend
    if (socketRef.current) {
      setIsAwaitingResponse(true);
      const payload = {
        type: 'query',
        query: suggestion.command,
        user_id: 'demo_user',
        timestamp: Date.now()
      };
      socketRef.current.send(JSON.stringify(payload));
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>LexEdge Legal AI</h1>
        <div className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? 'Online' : isConnecting ? 'Connecting...' : 'Offline'}
        </div>
      </div>

      <div className="messages-area">
        {messages.map((msg, index) => (
          <div key={index} className="message-wrapper">
            <div className={`message ${msg.role}`} data-type={msg.type}>
              <div className="message-icon">
                {msg.role === 'user' ? (
                  <User size={20} />
                ) : msg.role === 'assistant' ? (
                  <img
                    src={getAgentAvatar(msg.agent)}
                    alt={msg.agent || "AI"}
                    className="agent-avatar"
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = 'http://localhost:3334/static/agents/dr_generic.png';
                    }}
                  />
                ) : (
                  <Bot size={20} />
                )}
              </div>
              <div className="message-content">
                {msg.agent && <div className="agent-badge">{msg.agent}</div>}
                {msg.image && (
                  <div className="message-image">
                    <img src={msg.image} alt="Document preview" />
                  </div>
                )}

                {/* Dynamic Content Rendering */}
                {(() => {
                  // Try to parse content if it's a JSON string
                  let content = msg.content;
                  if (typeof content === 'string' && (content.startsWith('{') || content.trim().startsWith('{'))) {
                    try {
                      content = JSON.parse(content);
                    } catch (e) {
                      // Not JSON, keep as string
                    }
                  }

                  if (typeof content === 'object' && content !== null && content.response_type) {
                    // It's a structured response!
                    const T = content.response_type.toLowerCase();
                    if (T === 'assessment') {
                      return <AssessmentCard data={content} />;
                    } else if (T === 'legal_analysis') {
                      return <LegalAnalysisCard data={content} />;
                    } else if (T === 'contract_review') {
                      return <ContractReviewCard data={content} />;
                    } else if (T === 'legal_research') {
                      return <LegalResearchCard data={content} />;
                    } else if (T === 'case_management') {
                      return <CaseManagementCard data={content} />;
                    } else if (T === 'compliance') {
                      return <ComplianceCard data={content} />;
                    } else if (T === 'legal_correspondence') {
                      return <LegalCorrespondenceCard data={content} />;
                    } else if (T === 'smart_followup') {
                      return <SmartFollowupCard data={content} onSuggestionClick={handleSuggestionClick} />;
                    } else if (T === 'general') {
                      return <GeneralCard data={content} />;
                    }
                    // Fallback for unknown types
                    return <GeneralCard data={{ content: JSON.stringify(content) }} />;
                  }

                  // Legacy HTML rendering
                  return <div dangerouslySetInnerHTML={{ __html: msg.content }} />;
                })()}
              </div>
            </div>

            {/* Render clickable examples for guidance messages */}
            {msg.role === 'assistant' && msg.isGuidance && msg.examples && msg.examples.length > 0 && (
              <div className="examples-container" style={{ marginLeft: '52px', marginTop: '12px' }}>
                <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '8px', fontWeight: '600' }}>
                  💡 Try an example:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {msg.examples.map((example, eIndex) => (
                    <button
                      key={eIndex}
                      className="example-button"
                      onClick={() => {
                        // Add as user message and send to backend
                        const userMsg = {
                          role: 'user',
                          content: example,
                        };
                        setMessages(prev => [...prev, userMsg]);

                        // Send to backend with forced agent
                        if (socketRef.current) {
                          setIsAwaitingResponse(true);
                          const payload = {
                            type: 'query',
                            query: example,
                            user_id: 'demo_user',
                            force_agent: activeAgent,
                            timestamp: Date.now()
                          };
                          console.log('Sending example with force_agent:', activeAgent);
                          socketRef.current.send(JSON.stringify(payload));
                        }
                      }}
                      style={{
                        textAlign: 'left',
                        padding: '10px 14px',
                        borderRadius: '8px',
                        border: '1px solid #e2e8f0',
                        background: '#f8fafc',
                        cursor: 'pointer',
                        fontSize: '0.85rem',
                        color: '#334155',
                        lineHeight: '1.4',
                        transition: 'all 0.15s ease'
                      }}
                      onMouseOver={(e) => {
                        e.target.style.background = '#e0f2fe';
                        e.target.style.borderColor = '#93c5fd';
                      }}
                      onMouseOut={(e) => {
                        e.target.style.background = '#f8fafc';
                        e.target.style.borderColor = '#e2e8f0';
                      }}
                    >
                      "{example}"
                    </button>
                  ))}
                </div>
              </div>
            )}

            {msg.role === 'assistant' && msg.suggestions && msg.suggestions.length > 0 && (
              (() => {
                // Check if this is the most recent assistant message
                const isLastAssistantMessage = messages
                  .slice(index + 1)
                  .every(m => m.role !== 'assistant');

                if (isLastAssistantMessage) {
                  const hasBootstrap = msg.suggestions.some(s => s.isBootstrap);
                  if (hasBootstrap) {
                    return (
                      <div className="bootstrap-grid">
                        {msg.suggestions.map((suggestion, sIndex) => {
                          const meta = BOOTSTRAP_GUIDANCE[suggestion.id];
                          return (
                            <button
                              key={sIndex}
                              className="bootstrap-card"
                              onClick={() => handleSuggestionClick(suggestion)}
                            >
                              <div className="bootstrap-title">{meta?.title || suggestion.caption}</div>
                              <div className="bootstrap-summary">{meta?.summary}</div>
                              <div className="bootstrap-cta">Select</div>
                            </button>
                          );
                        })}
                      </div>
                    );
                  }
                  return (
                    <div className="suggestions-container">
                      {msg.suggestions.map((suggestion, sIndex) => (
                        <button
                          key={sIndex}
                          className="suggestion-button"
                          onClick={() => handleSuggestionClick(suggestion)}
                        >
                          {suggestion.caption || suggestion.command}
                        </button>
                      ))}
                    </div>
                  );
                }
                return null;
              })()
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-container">
        {isAwaitingResponse && (
          <div className="response-waiting">
            <div className="response-loader" />
            <div>
              <div className="response-title">Processing request</div>
              <div className="response-subtitle">LexEdge AI is analysing your request…</div>
            </div>
          </div>
        )}
        {isRecording && (
          <div className="recording-indicator">
            <div className="recording-dot" />
            <div className="recording-wave">
              <span />
              <span />
              <span />
              <span />
            </div>
            <div className="recording-text">
              Recording… {formatRecordingTime(recordingSeconds)}
            </div>
            <button
              type="button"
              className="recording-stop-button"
              onClick={stopRecording}
            >
              Stop
            </button>
          </div>
        )}
        {isTranscribing && (
          <div className="processing-indicator">
            <Loader2 size={20} className="spin" />
            <span>Transcribing audio...</span>
          </div>
        )}
        {isProcessingFile && (
          <div className="processing-indicator">
            <Loader2 size={20} className="spin" />
            <span>Converting document to images...</span>
          </div>
        )}

        {showImageOptions && selectedImage && (
          <div className="image-preview-bar">
            <div className="preview-container" style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '10px 14px' }}>
              <FileText size={28} style={{ color: '#0284c7', flexShrink: 0 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#1e293b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {selectedFileData?.filename || selectedImage.name}
                </div>
                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>
                  {selectedFileData?.mime_type || selectedImage.type} · {selectedImage.size ? (selectedImage.size / 1024).toFixed(1) + ' KB' : ''}
                </div>
              </div>
              <button className="remove-image" onClick={removeImage} title="Remove document">
                <X size={14} />
              </button>
            </div>
            <div className="image-analysis-options">
              <span className="options-label">Document ready for analysis:</span>
              <div className="analysis-buttons">
                <button
                  className="analysis-type-btn radiology"
                  onClick={handleDocumentAnalysis}
                  disabled={!isConnected}
                >
                  📄 Analyse Document
                  <span className="btn-subtitle">Extract &amp; review document content</span>
                </button>
              </div>
            </div>
          </div>
        )}

        <form className="input-area" onSubmit={handleSend}>
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept=".pdf,.doc,.docx,.txt,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
            style={{ display: 'none' }}
          />
          <button
            type="button"
            className="icon-button"
            onClick={() => fileInputRef.current?.click()}
            disabled={!isConnected}
          >
            <ImageIcon size={20} />
          </button>
          <button
            type="button"
            className={`icon-button ${isRecording ? 'recording' : ''}`}
            onClick={isRecording ? stopRecording : startRecording}
            disabled={!isConnected || isTranscribing}
            title={isRecording ? 'Stop recording' : 'Start recording'}
          >
            {isRecording ? <MicOff size={20} /> : <Mic size={20} />}
          </button>

          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isConnected ? (isRecording ? 'Recording… click mic to stop' : activeAgent ? 'Type your question or upload a document ↑' : 'Ask a legal question or select a mode above…') : 'Connecting…'}
            disabled={!isConnected || isTranscribing}
          />
          <select
            className="bootstrap-select"
            defaultValue=""
            onChange={(e) => {
              const value = e.target.value;
              if (!value) return;
              const selection = BOOTSTRAP_COMMANDS[value];
              if (selection) {
                handleSuggestionClick(selection);
              }
              e.target.value = "";
            }}
            disabled={!isConnected || isTranscribing}
          >
            <option value="" disabled>⚡ Quick actions</option>
            <option value="contract">📄 Contract Analysis</option>
            <option value="research">🔍 Legal Research</option>
            <option value="case">📋 Case Management</option>
            <option value="compliance">🛡️ Compliance Review</option>
            <option value="intake">📝 Case Intake</option>
            <option value="correspondence">✉️ Legal Correspondence</option>
            <option value="legal">⚖️ Legal Analysis</option>
          </select>
          <button type="submit" disabled={!isConnected || (!input.trim() && !selectedImage) || isTranscribing}>
            <Send size={20} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface;
