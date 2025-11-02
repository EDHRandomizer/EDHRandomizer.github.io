# Vercel KV Setup Guide

This guide walks you through setting up Vercel KV (Redis) for persistent pack code storage.

## Why Vercel KV?

- **Persistent storage**: Pack codes survive serverless function restarts
- **Automatic expiration**: Redis TTL handles cleanup automatically
- **Free tier**: 256 MB storage, 10k commands/day (plenty for this use case)
- **Built-in to Vercel**: No separate service needed

## Setup Steps

### 1. Enable Vercel KV in Dashboard

1. Go to https://vercel.com/dashboard
2. Select your project (`edhrandomizer-api`)
3. Go to **Storage** tab
4. Click **Create Database**
5. Choose **KV (Redis)**
6. Name it: `edhrandomizer-kv`
7. Select **Create**

### 2. Connect KV to Your Project

After creating the database:

1. Click **Connect to Project**
2. Select `edhrandomizer-api` (or your project name)
3. Choose environment: **Production** (check both Production and Preview if you want)
4. Click **Connect**

This automatically adds these environment variables to your project:
- `KV_REST_API_URL`
- `KV_REST_API_TOKEN`
- `KV_REST_API_READ_ONLY_TOKEN`
- `KV_URL`

### 3. Verify Environment Variables

1. In your project, go to **Settings** → **Environment Variables**
2. Confirm you see:
   - ✅ `KV_REST_API_URL`
   - ✅ `KV_REST_API_TOKEN`

### 4. Deploy Updated Code

The code is already updated to use Vercel KV! Just push to GitHub:

```bash
git push origin main
```

Vercel will automatically:
1. Detect the changes
2. Install `redis>=5.0.0` from `requirements-api.txt`
3. Use the KV environment variables
4. Deploy the updated API

### 5. Verify It's Working

After deployment, check the function logs:

1. Go to **Deployments** tab
2. Click on the latest deployment
3. Go to **Functions** → `api/sessions`
4. Check logs for:
   - ✅ `Vercel KV enabled for pack code storage`
   - ✅ `Stored pack code {CODE} in Vercel KV`

If you see warnings instead:
- ⚠️ `Vercel KV not configured` - Environment variables missing
- ⚠️ `redis package not installed` - Check `requirements-api.txt`

## How It Works

### Pack Code Storage
```python
# When generating pack codes (after all players lock commanders)
store_pack_code(code, {
    'commanderUrl': url,
    'config': pack_config,
    'powerups': powerup_list
})
# → Stored in Redis with 2-hour TTL
```

### Pack Code Retrieval
```python
# When TTS requests a pack code
pack_data = get_pack_code(code)
# → Retrieved from Redis
# → Returns: {commanderUrl, config, powerups}
```

### Automatic Expiration
- Pack codes auto-expire after 2 hours (configurable in `PACK_CODE_TTL`)
- No manual cleanup needed
- Redis handles it automatically

## Fallback Behavior

If Vercel KV is not available (missing env vars or package):
- ✅ API still works
- ⚠️ Pack codes stored in-memory only
- ⚠️ Lost when function restarts (5-15 minutes of inactivity)

## Troubleshooting

### "Pack code not found" errors after 10+ minutes

**Cause**: Vercel KV not configured, using in-memory fallback  
**Fix**: Follow setup steps above

### Function logs show KV errors

**Cause**: Wrong environment variables or network issue  
**Fix**: Verify env vars in Vercel dashboard, redeploy

### Want to test locally?

Install redis-py:
```bash
pip install redis>=5.0.0
```

Set environment variables:
```bash
export KV_REST_API_URL="your-redis-url"
export KV_REST_API_TOKEN="your-token"
```

## Cost Estimate

**Free Tier Limits:**
- 256 MB storage (≈ 250,000 pack codes)
- 10,000 commands/day (≈ 5,000 pack code retrievals/day)
- 100 MB bandwidth/month

**Your Usage:**
- ~10-50 pack codes/day
- ~100-500 retrievals/day
- **Well within free tier** ✅

## Next Steps

After setup:
1. ✅ Create game session
2. ✅ Roll powerups
3. ✅ Lock commanders
4. ✅ Generate pack codes
5. ✅ Paste pack code in TTS (works for 2+ hours!)

Pack codes now persist reliably! 🎉
