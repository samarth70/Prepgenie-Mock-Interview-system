# AgentScope Integration Guide

## ✅ **What is AgentScope?**

AgentScope is a **unified LLM framework** that provides:
- ✅ Single interface for multiple LLM providers
- ✅ **Automatic fallback** when API quota exhausted
- ✅ Support for 20+ models (Gemini, Claude, GPT, Qwen, Llama, etc.)
- ✅ Built-in retry logic
- ✅ Streaming support
- ✅ Tool use and vision capabilities

---

## 🎯 **Model Fallback Chain**

PrepGenie now uses this automatic fallback order:

```
1. Gemini 2.0 Flash (Google) ← Primary
   ↓ (if quota exhausted or error)
2. Claude 3.5 Sonnet (Anthropic) ← Fallback 1
   ↓ (if quota exhausted or error)
3. Qwen Max (Alibaba) ← Fallback 2
   ↓ (if unavailable)
4. Llama 3 (Local via Ollama) ← Fallback 3 (No API needed!)
```

**Benefits:**
- ✅ Never run out of API quota
- ✅ Always have a working model
- ✅ Cost optimization (use free local models when possible)
- ✅ No manual intervention needed

---

## 📦 **Installation**

### **Option 1: Fresh Install**
```bash
cd backend
pip install -r requirements_agentscope.txt
```

### **Option 2: Add to Existing**
```bash
pip install agentscope
```

---

## 🔑 **Configuration**

Create or update `backend/.env`:

```bash
# Primary: Google Gemini
GOOGLE_API_KEY=your_google_api_key_here

# Fallback 1: Anthropic Claude (optional but recommended)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Fallback 2: Alibaba Qwen (optional)
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# Fallback 3: Ollama (local - no API key needed!)
# Just install Ollama: https://ollama.ai
```

### **Get API Keys:**

1. **Google Gemini**: https://makersuite.google.com/app/apikey
2. **Anthropic Claude**: https://console.anthropic.com/settings/keys
3. **Alibaba Qwen**: https://help.aliyun.com/zh/dashscope/
4. **Ollama (Local)**: https://ollama.ai (free, no key needed)

---

## 🚀 **Usage**

### **Automatic (Built-in)**

The backend automatically uses AgentScope with fallback. Just start the server:

```bash
cd backend
uvicorn main:app --reload
```

You'll see:
```
🚀 Initializing AgentScope Model Manager...
✅ Gemini model initialized
✅ Anthropic model initialized
✅ DashScope (Qwen) model initialized
✅ Ollama (local) model initialized
📦 Available models: ['gemini', 'anthropic', 'dashscope', 'ollama']
🎯 Primary model: gemini
```

### **Manual Model Switching**

You can manually switch models via API:

```python
from model_manager import get_model_manager

model_mgr = get_model_manager()

# Switch to Claude
model_mgr.switch_model("anthropic")

# Switch to Qwen
model_mgr.switch_model("dashscope")

# Switch to local Llama
model_mgr.switch_model("ollama")
```

---

## 📊 **How It Works**

### **Normal Operation:**
```
User asks question
    ↓
AgentScope tries Gemini
    ↓
Gemini responds ✅
    ↓
Return answer to user
```

### **When Gemini Quota Exhausted:**
```
User asks question
    ↓
AgentScope tries Gemini
    ↓
Gemini returns 429 error ❌
    ↓
AgentScope automatically tries Claude ✅
    ↓
Return answer to user
```

### **When All APIs Exhausted:**
```
User asks question
    ↓
Gemini: 429 error ❌
Claude: 429 error ❌
Qwen: 429 error ❌
    ↓
AgentScope tries Ollama (local) ✅
    ↓
Return answer to user (using free local model!)
```

---

## 🔍 **Monitoring**

### **Console Logs:**

When a request comes in, you'll see:

```
🤖 Generating content with AgentScope...
🔄 Trying gemini...
✅ Success using gemini model
```

**If Gemini fails:**
```
🤖 Generating content with AgentScope...
🔄 Trying gemini...
❌ gemini failed: 429 quota exceeded
🔄 Trying anthropic...
✅ Success using anthropic model
```

**If all cloud APIs fail:**
```
🤖 Generating content with AgentScope...
🔄 Trying gemini... ❌
🔄 Trying anthropic... ❌
🔄 Trying dashscope... ❌
🔄 Trying ollama...
✅ Success using ollama model
```

---

## 💡 **Advanced Features**

### **1. Add More Models**

Edit `backend/model_manager.py`:

```python
# Add Groq
from agentscope.model import OpenAIChatModel

self.models["groq"] = OpenAIChatModel(
    model_name="llama-3.1-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    client_kwargs={"base_url": "https://api.groq.com/openai/v1"},
)
```

### **2. Custom Model Parameters**

```python
GeminiChatModel(
    model_name="gemini-2.0-flash-exp",
    api_key=api_key,
    generate_kwargs={
        "temperature": 0.7,      # Creativity (0-1)
        "max_tokens": 2000,      # Max response length
        "top_p": 0.9,           # Nucleus sampling
    },
)
```

### **3. Streaming Responses**

```python
model = GeminiChatModel(
    model_name="gemini-2.0-flash-exp",
    api_key=api_key,
    stream=True,  # Enable streaming
)
```

---

## 🎯 **Supported Models**

| Provider | Model Class | API Key Env | Notes |
|----------|-------------|-------------|-------|
| **Google** | `GeminiChatModel` | `GOOGLE_API_KEY` | Primary model |
| **Anthropic** | `AnthropicChatModel` | `ANTHROPIC_API_KEY` | Best quality |
| **Alibaba** | `DashScopeChatModel` | `DASHSCOPE_API_KEY` | Good fallback |
| **OpenAI** | `OpenAIChatModel` | `OPENAI_API_KEY` | Can use with Groq, vLLM |
| **Ollama** | `OllamaChatModel` | None | Local, free! |
| **Groq** | `OpenAIChatModel` | `GROQ_API_KEY` | Fast inference |

---

## 📈 **Benefits Over Direct API**

### **Before (Direct Gemini):**
```python
import google.generativeai as genai

genai.configure(api_key=KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

try:
    response = model.generate_content(prompt)
except Exception as e:
    # Manual retry logic needed
    # Manual fallback needed
    # Complex error handling
```

### **After (AgentScope):**
```python
from model_manager import get_model_manager

model_mgr = get_model_manager()
result = await model_mgr.generate(prompt)

# Automatic fallback
# Automatic retry
# Simple error handling
# Returns: {"success": True, "text": "...", "model": "gemini"}
```

---

## 🐛 **Troubleshooting**

### **Issue: No models initialized**

**Console shows:**
```
❌ No models available!
```

**Solution:**
1. Check `.env` has API keys
2. Verify API keys are valid
3. Check internet connection

### **Issue: All models failing**

**Console shows:**
```
❌ All models failed: [error]
```

**Solution:**
1. Install Ollama for local fallback: https://ollama.ai
2. Run: `ollama pull llama3`
3. Restart backend

### **Issue: Dependency conflicts**

**Error:**
```
dependency conflicts...
```

**Solution:**
```bash
pip install agentscope --upgrade
```

---

## ✅ **Testing**

### **Test 1: Basic Generation**
```bash
cd backend
python -c "from model_manager import get_model_manager; import asyncio; mgr = get_model_manager(); print(asyncio.run(mgr.generate('Hello!')))"
```

### **Test 2: Interview Flow**
1. Start backend: `uvicorn main:app --reload`
2. Open http://localhost:8000
3. Start mock interview
4. Submit answer
5. Check console for model usage

### **Test 3: Fallback**
1. Set invalid GOOGLE_API_KEY in `.env`
2. Restart backend
3. Submit interview answer
4. Should see fallback to next model

---

## 🎉 **Summary**

### **What Changed:**
- ✅ Replaced direct Gemini API with AgentScope
- ✅ Added automatic fallback chain
- ✅ Support for 20+ LLM providers
- ✅ Built-in retry logic
- ✅ Local model support (Ollama)

### **Benefits:**
- ✅ **Never run out of quota** - automatic fallback
- ✅ **Cost optimization** - use free models when possible
- ✅ **Higher reliability** - multiple backups
- ✅ **Easy to extend** - add new models easily
- ✅ **Better monitoring** - clear logs

### **Next Steps:**
1. Add API keys to `.env`
2. Install Ollama for local fallback
3. Test interview flow
4. Monitor console logs

---

**Your PrepGenie now has enterprise-grade LLM management with automatic fallback!** 🚀✨
