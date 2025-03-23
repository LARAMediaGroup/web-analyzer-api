# Web Analyzer Deployment Guide

This guide provides step-by-step instructions for deploying the Web Analyzer service and WordPress plugin.

## Prerequisites

- Access to WordPress admin dashboard on thevou.com
- Access to the Render dashboard
- API credentials for the Web Analyzer service

## 1. API Service Deployment (Render)

The Web Analyzer API service is already deployed at: `https://web-analyzer-api.onrender.com`

### Verify API Service

1. Test the health endpoint:
   ```
   curl -i -H "X-API-Key: your_api_key" https://web-analyzer-api.onrender.com/health
   ```

2. If response shows `{"status": "ok", ...}`, the service is running correctly.

### Update API Configuration (if needed)

1. Log in to the Render dashboard
2. Navigate to the Web Analyzer service
3. Go to Environment
4. Verify or update the following environment variables:
   - `ALLOWED_ORIGINS`: Make sure it includes `https://thevou.com` and `https://www.thevou.com`
   - `DEBUG`: Should be `False` in production
   - `LOG_LEVEL`: Set to `INFO` or `WARNING`
   - `MAX_WORKERS`: Recommended value of `4` for production
   - `SECRET_KEY`: Should be a strong random value

## 2. WordPress Plugin Installation

### Upload the Plugin

1. Log in to the WordPress admin dashboard
2. Navigate to Plugins > Add New > Upload Plugin
3. Select the `thevou-web-analyzer-1.2.0.zip` file
4. Click "Install Now"
5. After installation completes, click "Activate Plugin"

### Configure the Plugin

1. Navigate to Web Analyzer > Settings in the WordPress admin menu
2. Enter the following settings:
   - API URL: `https://web-analyzer-api.onrender.com` (no trailing slash)
   - API Key: `thevou_production_key_12345` (replace with the actual API key)
   - Site ID: `thevou`
3. Click "Save Settings"

### Test the Connection

1. In the Web Analyzer settings page, scroll down to the "Connection Test" section
2. Click the "Test Connection" button
3. You should see a success message
4. If you encounter issues, use the "Run Detailed Test" button in the Debug Information section to diagnose

## 3. Bulk Processing (Optional)

After initial setup, you can run bulk processing to analyze existing content:

1. In the Web Analyzer settings, go to the "Bulk Processing" section
2. Select the post type to analyze (typically "Posts")
3. Set the limit (recommended: start with 10 for testing)
4. Click "Start Analysis"
5. Monitor the progress and review the report when completed

## 4. Post-Installation Verification

### Test in Block Editor

1. Create a new post or edit an existing one
2. Add some fashion-related content
3. Open the Web Analyzer sidebar (from the top-right menu icon)
4. Click "Analyze Content"
5. Verify that link suggestions appear
6. Test inserting links using the different methods

### Test in Classic Editor (if used)

1. Create or edit a post in Classic Editor
2. Add fashion-related content
3. Look for the Web Analyzer meta box
4. Test the analysis and link insertion functionality

## 5. Troubleshooting

If you encounter issues during installation or testing:

1. Check the plugin's Debug Information section for detailed diagnostics
2. Verify the API credentials are correct
3. Check for JavaScript errors in the browser console
4. Look at the API logs on Render for any backend issues
5. Test the API endpoints directly using curl or Postman

## 6. Monitoring and Maintenance

- Set up regular checks of the API health endpoint
- Monitor Render dashboard for any service issues
- Keep the plugin updated with any new versions
- Check the logs periodically for any errors or warnings

## Support

For any assistance, contact the development team at:
- Email: support@thevou.com
- Documentation: https://thevou.com/web-analyzer-docs