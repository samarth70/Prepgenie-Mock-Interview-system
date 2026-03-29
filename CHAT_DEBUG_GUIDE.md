# Chat Debugging Guide

## ✅ Improvements Applied

### **Enhanced Error Logging**:
- ✅ API call attempts logged (1/3, 2/3, 3/3)
- ✅ Success/failure clearly marked
- ✅ Detailed error messages
- ✅ Rate limit detection
- ✅ Fallback responses instead of errors

---

## 🔍 **How to Debug Chat Issues**

### **Step 1: Check Backend Console**

When you send a chat message, look for these logs:

```
📝 Chat request received: kewwords?...
🎯 Calling AI model for chat...
🔄 API call attempt 1/3
✅ API call successful
📝 Chat API Success: True
📝 Raw result: Here are some keywords...
```

**OR if it fails:**

```
📝 Chat request received: kewwords?...
🎯 Calling AI model for chat...
🔄 API call attempt 1/3
❌ API error on attempt 1: [error details]
🔄 API call attempt 2/3
❌ API error on attempt 2: [error details]
🔄 API call attempt 3/3
❌ API error on attempt 3: [error details]
📝 Chat API Success: False
❌ Chat failed: Service error: [error]
```

---

## 📊 **Common Issues & Solutions**

### **Issue 1: Model Not Available**

**Console shows:**
```
❌ AI model not configured
```

**Solution:**
- Check if `GOOGLE_API_KEY` is set in `backend/.env`
- Verify API key is valid at https://makersuite.google.com/app/apikey

---

### **Issue 2: API Quota Exceeded**

**Console shows:**
```
⏰ Rate limit hit, waiting...
❌ API error: quota exceeded
```

**Solution:**
- Wait a few minutes before trying again
- Check your API quota at https://makersuite.google.com
- Consider upgrading your API plan

---

### **Issue 3: Invalid API Key**

**Console shows:**
```
❌ API error: 403 Permission denied
```

**Solution:**
- Verify API key in `backend/.env`
- Make sure API key has no extra spaces or quotes
- Regenerate API key if needed

---

### **Issue 4: Model Not Found**

**Console shows:**
```
❌ API error: 404 models/gemini-2.0-flash-exp is not found
```

**Solution:**
The system should automatically fallback to:
1. gemini-1.5-flash
2. gemini-pro

Check console for:
```
⚠️ Gemini 2.0 not available: [error]
✅ Using Gemini 1.5 Flash
```

---

## 🛠️ **Quick Fixes**

### **Fix 1: Restart Backend**

```bash
cd backend
uvicorn main:app --reload
```

### **Fix 2: Check API Key**

```bash
# In backend/.env
GOOGLE_API_KEY=AIzaSy...your_key_here
```

### **Fix 3: Test Model Directly**

```python
import google.generativeai as genai

genai.configure(api_key="your_key")
model = genai.GenerativeModel("gemini-2.0-flash-exp")
response = model.generate_content("Hello")
print(response.text)
```

---

## ✅ **Expected Flow**

### **Successful Chat:**

1. **Frontend**: User types "keywords?"
2. **Backend Console**:
   ```
   📝 Chat request received: keywords?...
   🎯 Calling AI model for chat...
   🔄 API call attempt 1/3
   ✅ API call successful
   📝 Chat API Success: True
   📝 Raw result: Based on your resume...
   ```
3. **Frontend**: Shows AI response

### **Failed Chat (with fallback):**

1. **Frontend**: User types "keywords?"
2. **Backend Console**:
   ```
   📝 Chat request received: keywords?...
   🎯 Calling AI model for chat...
   🔄 API call attempt 1/3
   ❌ API error: [details]
   🔄 API call attempt 2/3
   ❌ API error: [details]
   🔄 API call attempt 3/3
   ❌ API error: [details]
   📝 Chat API Success: False
   ❌ Chat failed: Service error: [details]
   ```
3. **Frontend**: Shows fallback message:
   ```
   "I apologize, but I'm experiencing technical difficulties 
   at the moment. Please try again."
   ```

---

## 🎯 **Test It Now**

1. **Open** http://localhost:3002/chat
2. **Upload** resume
3. **Type** a question
4. **Watch** backend console for logs
5. **Check** for emoji indicators:
   - 📝 Request received
   - 🎯 Calling model
   - 🔄 Attempt X/3
   - ✅ Success OR ❌ Error
   - 📝 Result preview

---

## 📝 **What to Share if Issues Persist**

If chat still fails, share:

1. **Backend console logs** (full error message)
2. **API key status** (is it set?)
3. **Model being used** (which model is active?)
4. **Error type** (403, 404, 429, etc.)

Example:
```
❌ API error on attempt 1: 403 Permission denied
```

This tells us it's an API key issue, not a model issue.

---

**Backend is now running with detailed error logging! Check console when you send a chat message.** 🔍✨
