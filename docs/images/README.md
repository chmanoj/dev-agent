# Documentation Images

This directory contains screenshots and images used in the dev-agent documentation.

## Required Screenshots for Azure OpenAI Setup Guide

The following screenshots are referenced in `docs/configuration/azure-openai.md` and should be added:

### Setup Screenshots

1. **azure-portal-home.png**
   - Azure Portal home page
   - Show the main dashboard with "Create a resource" button visible

2. **azure-create-resource.png**
   - Creating a new Azure OpenAI resource
   - Show the search results for "Azure OpenAI" with the Create button

3. **azure-configure-resource.png**
   - Configuring the Azure OpenAI resource
   - Show the form with Subscription, Resource Group, Region, Name, and Pricing Tier fields

4. **azure-deployment-complete.png**
   - Successful deployment notification
   - Show the "Deployment complete" message with "Go to resource" button

### Model Deployment Screenshots

5. **azure-model-deployments.png**
   - Model deployments page in Azure Portal
   - Show the left navigation with "Model deployments" selected

6. **azure-deploy-gpt4.png**
   - Creating a GPT-4 deployment
   - Show the deployment creation form with model selection and configuration

7. **azure-deploy-embeddings.png**
   - Creating an embeddings deployment
   - Show the deployment creation form for text-embedding-ada-002

8. **azure-deployment-list.png**
   - List of successful deployments
   - Show both GPT-4 and embeddings deployments with "Succeeded" status

### API Credentials Screenshots

9. **azure-keys-endpoint.png**
   - Keys and Endpoint page
   - Show the endpoint URL and API keys section (with keys redacted)

10. **azure-api-keys.png**
    - API keys with copy buttons
    - Show KEY 1 and KEY 2 with copy icons (keys should be blurred/redacted)

## Screenshot Guidelines

### Technical Requirements
- **Format**: PNG (preferred) or JPG
- **Resolution**: Minimum 1920x1080 for clarity
- **File Size**: Keep under 500KB per image (use compression if needed)
- **Color**: Full color, high contrast for readability

### Content Guidelines
- **Redact Sensitive Information**: 
  - Blur or redact API keys
  - Redact subscription IDs
  - Redact resource names if they contain sensitive information
- **Highlight Important Elements**:
  - Use red boxes or arrows to highlight key buttons/fields
  - Add annotations if helpful
- **Clean Interface**:
  - Close unnecessary browser tabs
  - Hide personal information from browser
  - Use a clean, professional theme

### Naming Convention
- Use lowercase with hyphens: `azure-portal-home.png`
- Be descriptive: `azure-deploy-gpt4.png` not `screenshot1.png`
- Match the filenames referenced in the documentation exactly

## Taking Screenshots

### Recommended Tools

**macOS**:
- Built-in: `Cmd + Shift + 4` (select area)
- Built-in: `Cmd + Shift + 3` (full screen)
- Preview app for editing and annotation

**Windows**:
- Built-in: `Win + Shift + S` (Snipping Tool)
- Built-in: `Win + PrtScn` (full screen)
- Paint or Paint 3D for editing

**Linux**:
- GNOME Screenshot: `PrtScn` or `Shift + PrtScn`
- Flameshot: Advanced screenshot tool with annotation
- GIMP for editing

### Screenshot Workflow

1. **Prepare Azure Portal**:
   - Log into Azure Portal
   - Navigate to the relevant page
   - Zoom to 100% for clarity
   - Close unnecessary panels

2. **Take Screenshot**:
   - Capture the relevant area
   - Include enough context (navigation, headers)
   - Ensure text is readable

3. **Edit Screenshot**:
   - Redact sensitive information
   - Add highlights or annotations if needed
   - Crop to remove unnecessary areas
   - Resize if too large (max 1920px width)

4. **Optimize File Size**:
   - Use PNG compression tools (e.g., TinyPNG, pngquant)
   - Target 200-500KB per image
   - Maintain readability

5. **Save and Verify**:
   - Save with correct filename
   - Place in `docs/images/` directory
   - Verify image displays correctly in documentation
   - Check on both light and dark themes if applicable

## Updating Screenshots

Screenshots should be updated when:
- Azure Portal UI changes significantly
- New features are added to the setup process
- Screenshots become outdated or unclear
- User feedback indicates confusion

## Alternative: Placeholder Images

If actual screenshots are not available, you can use placeholder images:

```markdown
![Azure Portal Home](https://via.placeholder.com/1200x800/0078D4/FFFFFF?text=Azure+Portal+Home)
```

However, actual screenshots are strongly preferred for production documentation.

## Contributing Screenshots

If you're contributing screenshots:
1. Follow the guidelines above
2. Ensure you have permission to share the screenshots
3. Redact all sensitive information
4. Submit via pull request with screenshots in this directory
5. Update this README if adding new screenshots

## Questions?

If you have questions about documentation images:
- Check the main documentation: `docs/configuration/azure-openai.md`
- Open an issue on GitHub
- Contact the documentation team
