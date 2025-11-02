# URGENT: Fix "Session Not Found" - Set Up Vercel KV

## The Problem
Sessions are being created but immediately lost, causing "Session not found" errors. This is because:
- Sessions are currently stored in memory only
- Vercel serverless functions are stateless - each API call is a fresh instance
- Session created in one function call doesn't exist in the next call

## The Solution: Enable Vercel KV

### Step 1: Create KV Database (2 minutes)

1. **Go to Vercel Dashboard**: https://vercel.com/dashboard
2. **Navigate to Storage**:
   - Click on your project (`edhrandomizer-api`)
   - Click "Storage" tab at the top
3. **Create KV Database**:
   - Click "Create Database"
   - Select "KV (Redis)"
   - Name it: `edhrandomizer-sessions`
   - Click "Create"

### Step 2: Connect to Project (1 minute)

1. **Connect Database**:
   - After creation, click "Connect Project"
   - Select `edhrandomizer-api`
   - Click "Connect"

2. **Verify Environment Variables**:
   - Go to Project Settings → Environment Variables
   - You should see two new variables:
     - `KV_REST_API_URL`
     - `KV_REST_API_TOKEN`

### Step 3: Redeploy (30 seconds)

1. **Trigger Redeploy**:
   ```bash
   git commit --allow-empty -m "Trigger redeploy with KV env vars"
   git push
   ```

OR just wait - the push I just made will deploy with the new env vars!

### Step 4: Verify It Works

After deployment completes (~1 minute):
1. Refresh your game page
2. Create a new session
3. Try to lock a commander
4. Should work now! ✅

## How to Check If KV is Working

Check Vercel deployment logs:
```
✅ Vercel KV enabled for pack code storage  <- Good!
```

vs

```
⚠️ Vercel KV not configured - using in-memory storage  <- Need to set up KV
   KV_REST_API_URL: NOT SET
   KV_REST_API_TOKEN: NOT SET
```

## What KV Gives You

- ✅ **Persistent sessions** across function calls
- ✅ **2-hour session TTL** (auto-expiration)
- ✅ **24-hour pack code storage**
- ✅ **256MB free tier** (plenty for game sessions)
- ✅ **Automatic LRU eviction** when memory full
- ✅ **No code changes needed** - it's already implemented!

## Without KV (Current State)

- ❌ Sessions lost between API calls
- ❌ "Session not found" errors
- ❌ Can't lock commanders
- ❌ Multiplayer doesn't work
- ❌ Pack codes don't persist

## Troubleshooting

**Q: I set up KV but still see errors**
- Wait for deployment to complete (check Vercel dashboard)
- Hard refresh browser (Ctrl+Shift+R)
- Check deployment logs for "✅ Vercel KV enabled"

**Q: Can I test locally without KV?**
- Yes, but only single-session testing
- In-memory storage works within one serverless function call
- Create session → immediately use it (same request cycle)

**Q: How much does KV cost?**
- Free tier: 256MB storage, 3 million commands/month
- More than enough for this project
- No credit card required for free tier
