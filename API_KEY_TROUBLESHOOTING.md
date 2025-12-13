# API Key Troubleshooting Guide

## Summary

Your OpenAI API key has been verified and is working correctly. If you're still getting 403 errors, they may be coming from:

1. **A different API service** (not OpenAI)
2. **A specific operation** that requires different permissions
3. **Rate limiting or quota issues** for specific models
4. **Organization/account restrictions**

## Quick Diagnostic Tools

### 1. Check API Key Configuration
```bash
python check_api_key.py
```

### 2. Test OpenAI API Key
```bash
python test_openai_key.py
```

## Common 403 Error Causes

### OpenAI-Specific Issues

1. **Model Access Restrictions**
   - Some models may require special access
   - Check model availability: https://platform.openai.com/account/limits
   - Try using `gpt-4o-mini` instead of `gpt-4o`

2. **Organization Restrictions**
   - Your organization may have restrictions on certain models
   - Check with your OpenAI account administrator

3. **Quota/Credits**
   - Insufficient credits for specific models
   - Check billing: https://platform.openai.com/account/billing

4. **API Key Permissions**
   - Some keys may have restricted permissions
   - Verify at: https://platform.openai.com/api-keys

### Other API Services

If the error is from a different API service:

1. **Check which script is failing**
   - Look at the error traceback to identify the script
   - Check if it's using a different API (Anthropic, Cohere, etc.)

2. **Verify API key for that service**
   - Each service has its own API key
   - Check environment variables for other API keys

## Solutions

### Solution 1: Verify API Key
```bash
# Run the test script
python test_openai_key.py
```

### Solution 2: Check Account Status
1. Visit: https://platform.openai.com/account/billing
2. Verify you have sufficient credits
3. Check usage limits

### Solution 3: Try Different Model
If using `gpt-4o`, try `gpt-4o-mini`:
```env
OPENAI_MODEL=gpt-4o-mini
```

### Solution 4: Regenerate API Key
1. Go to: https://platform.openai.com/api-keys
2. Create a new API key
3. Update your `.env` file
4. Restart your terminal/IDE

### Solution 5: Check Script-Specific Issues
- Identify which script is failing
- Check if it uses a different API service
- Verify all required API keys are set

## Getting More Information

To get more details about the error:

1. **Check the full error traceback**
   - Look for the script name and line number
   - Identify which API is being called

2. **Check logs**
   - Look for detailed error messages
   - Check for rate limit warnings

3. **Test individual components**
   - Test LLM calls separately
   - Test embedding calls separately
   - Test specific scripts individually

## Next Steps

1. **Identify the failing script**
   - Which command/script produced the 403 error?
   - What operation were you trying to perform?

2. **Check error details**
   - Full error message
   - Stack trace
   - Which API endpoint was called

3. **Try the solutions above**
   - Start with Solution 1 (verify API key)
   - Then try Solution 2 (check account status)
   - Finally try Solution 3 (different model)

## Support Resources

- OpenAI Status: https://status.openai.com/
- OpenAI Documentation: https://platform.openai.com/docs
- OpenAI Community: https://community.openai.com/
- Account Dashboard: https://platform.openai.com/account
