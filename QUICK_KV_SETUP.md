# Quick Vercel KV Setup (5 minutes)

## Step 1: Create KV Database (2 min)

1. Go to https://vercel.com/dashboard
2. Click your project → **Storage** tab
3. **Create Database** → **KV (Redis)**
4. Name: `edhrandomizer-kv`
5. Click **Create**

## Step 2: Connect to Project (1 min)

1. Click **Connect to Project**
2. Select your project
3. Environment: **Production** (+ Preview optional)
4. Click **Connect**

✅ This auto-adds `KV_REST_API_URL` and `KV_REST_API_TOKEN` environment variables

## Step 3: Done! (auto-deploys)

The code is already pushed to GitHub. Vercel will:
- Auto-detect the changes
- Install `redis` package
- Deploy with KV enabled

## Verify It Works

After ~2 minutes, check function logs:
1. **Deployments** → Latest → **Functions** → `api/sessions`
2. Look for: `✅ Vercel KV enabled for pack code storage`

## What This Fixes

**Before:** Pack codes lost after 5-15 min (function restart)  
**After:** Pack codes persist for **24 hours** minimum

**Memory Management:**
- If memory gets full (unlikely), Redis auto-removes oldest unused pack codes
- LRU eviction policy (Least Recently Used)
- Active pack codes always stay available

## Cost

**FREE** - Your usage is <1% of free tier limits
- 256 MB storage = ~128,000 pack codes
- You'll generate ~50/day = 7+ years before full
- Auto-cleanup if somehow full

---

That's it! Pack codes are now persistent. 🎉
