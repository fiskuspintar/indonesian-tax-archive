# Indonesian Tax Regulations Archive - Deployment Guide

## Prerequisites

1. **GitHub Account**: Create at https://github.com/signup
2. **Vercel Account**: Sign up at https://vercel.com (use "Continue with GitHub")

## Step 1: Prepare Your Repository

```bash
# Initialize git repository
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Indonesian Tax Regulations Archive"

# Create GitHub repository and push
# (Do this via GitHub web interface or GitHub CLI)
```

## Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `indonesian-tax-archive`
3. Description: "Digital Archive of Indonesian Tax Regulations"
4. Make it Public
5. Do NOT initialize with README (we already have one)
6. Click "Create repository"

## Step 3: Push to GitHub

After creating the repository, GitHub will show you commands. Use:

```bash
git remote add origin https://github.com/YOUR_USERNAME/indonesian-tax-archive.git
git branch -M main
git push -u origin main
```

## Step 4: Deploy to Vercel

### Option A: Vercel Dashboard (Recommended)

1. Go to https://vercel.com/new
2. Import your GitHub repository
3. Configure:
   - Framework Preset: Next.js
   - Root Directory: `web`
   - Build Command: `npm run build`
   - Output Directory: `dist`
4. Click "Deploy"

### Option B: Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd web
vercel --prod
```

## Step 5: Configure Custom Domain (Optional)

1. In Vercel Dashboard, go to your project
2. Click "Settings" → "Domains"
3. Add your custom domain
4. Follow DNS configuration instructions

## Step 6: Data Collection

After deployment, you need to populate the data:

```bash
# Run the complete pipeline
python run_pipeline.py all

# Or step by step:
python run_pipeline.py scrape      # Collect metadata
python run_pipeline.py extract     # Extract text
python run_pipeline.py import      # Import to database
python run_pipeline.py export      # Export for web
python run_pipeline.py build       # Build web app
```

## Step 7: Update Deployment with Data

```bash
# Add generated data
git add web/public/data/
git add data/
git commit -m "Add collected regulation data"
git push origin main

# Vercel will automatically redeploy
```

## Environment Variables (if needed)

Create `.env.local` in `web/` directory:

```
NEXT_PUBLIC_SITE_URL=https://your-domain.vercel.app
```

## Troubleshooting

### Build Failures

1. Check Node.js version: `node --version` (should be 18+)
2. Clear cache: `rm -rf web/.next web/node_modules web/dist`
3. Reinstall: `cd web && npm install`

### Data Not Showing

1. Verify JSON files exist in `web/public/data/`
2. Check file syntax: `python -m json.tool web/public/data/regulations.json`
3. Ensure files are committed and pushed

### Large File Issues

If regulations.json is too large for GitHub:

1. Use Git LFS: `git lfs track "web/public/data/*.json"`
2. Or split into smaller files by type

## Maintenance

### Update Data

```bash
# Re-run scraper for new regulations
python run_pipeline.py scrape
git add .
git commit -m "Update regulation data"
git push
```

### Monitor

- Vercel Analytics: https://vercel.com/analytics
- Uptime: Built-in monitoring in Vercel Dashboard

## Support

- Vercel Docs: https://vercel.com/docs
- Next.js Docs: https://nextjs.org/docs
- Project Issues: Create issue in GitHub repository
