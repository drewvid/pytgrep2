---
trigger: always_on
---

# Google GenAI SDK Usage

When implementing GenAI features or writing code examples that interact with Google's Gemini models, you **MUST** use the new `google-genai` SDK interface and **MUST NOT** use the deprecated legacy `google-generativeai` package.

## Correct Usage Pattern

### 1. Imports
Import `genai` directly from the `google` namespace:
```python
from google import genai
from google.genai import types
```

Do **NOT** use `import google.generativeai as genai`.

### 2. Client Initialization
Create a client instance:
```python
client = genai.Client(api_key="your_api_key")
```

Do **NOT** use `genai.configure(...)` or `genai.GenerativeModel(...)`.

### 3. Calling the API
Call the model through the client's `models` service:
```python
response = client.models.generate_content(
    model=gemini-3.1-flash-lite',
    contents='Your prompt here'
)
print(response.text)
```
