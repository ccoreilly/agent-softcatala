# GitHub Pages Deployment Setup

This repository has been configured to automatically deploy the frontend to GitHub Pages on every merge to the main branch.

## What was set up:

### 1. GitHub Actions Workflow
- Created `.github/workflows/deploy.yml`
- Builds the React frontend using Node.js 18
- Deploys to GitHub Pages only on pushes to main branch
- Uses proper GitHub Pages permissions and security settings

### 2. Package.json Configuration
- Added `homepage` field pointing to `https://ccoreilly.github.io/agent-softcatala`
- This ensures React Router and asset paths work correctly on GitHub Pages

### 3. Build Configuration
- React's `%PUBLIC_URL%` is automatically handled by Create React App
- No additional build configuration needed

## How to enable GitHub Pages:

1. Go to your repository settings: https://github.com/ccoreilly/agent-softcatala/settings/pages
2. Under "Source", select "GitHub Actions"
3. The workflow will automatically deploy on the next push to main

## Requirements:

Before deployment will work, you need to fix the current TypeScript compilation errors in the frontend code. The build currently fails due to type compatibility issues between `ChatAgentAdapter` and `ChatModelAdapter`.

## Deployment URL:

Once enabled and the build issues are resolved, the frontend will be available at:
https://ccoreilly.github.io/agent-softcatala

## Notes:

- Only changes pushed to the `main` branch will trigger deployment
- The workflow builds the frontend and creates a production-optimized bundle
- GitHub Pages serves static files, so this is perfect for React applications
- The deployment uses GitHub's built-in Pages deployment action for maximum security and reliability