# WordPress Integration Guide

## API Key Setup

### 1. Generate Secure API Keys

For each WordPress site that will connect to the API, generate a secure API key:

```bash
# Example of generating a secure 32-character key
openssl rand -base64 32
```

### 2. Configure API Service

Add the API key to the `site_credentials.json` file on the API server:

```json
{
  "thevou": {
    "api_key": "YOUR_GENERATED_SECURE_KEY",
    "name": "The VOU Fashion Blog",
    "url": "https://thevou.com",
    "rate_limit": 200
  }
}
```

### 3. WordPress Plugin Configuration

When installing the WordPress plugin on thevou.com, you'll need to configure it with:

- API Endpoint URL (e.g., `https://api.yourservice.com`)
- API Key (the same key you added to `site_credentials.json`)
- Site ID (e.g., "thevou")

The plugin will store these securely in the WordPress options table.

## Security Considerations

### API Key Storage

1. **On the API server**: Store keys in a secure configuration that's not included in version control
2. **In WordPress**: Store the API key using WordPress's encrypted options

### Transport Security

1. Always use HTTPS for all API communications
2. Use proper SSL certificate validation
3. Consider implementing request signing for additional security

### Access Controls

1. Implement WordPress role-based access controls to determine which users can:
   - View link suggestions
   - Configure the plugin
   - Apply suggested links to content

## WordPress Plugin Features

The plugin should include:

1. **Configuration page** in the WordPress admin
2. **Editor integration** for real-time link suggestions
3. **Bulk analysis** for processing existing content
4. **Analytics dashboard** to track link usage and performance

## Testing Before Production

Before going live with thevou.com:

1. Test the integration in a staging environment
2. Verify API key authentication works correctly
3. Test rate limiting to ensure it's appropriate for the site's traffic
4. Validate caching behavior to ensure optimal performance

## Deployment Workflow

1. Deploy the API service to the production server
2. Configure thevou.com's API credentials on the server
3. Install the WordPress plugin on thevou.com
4. Configure the plugin with the endpoint URL and API key
5. Test the integration with a single post
6. Roll out to all content gradually