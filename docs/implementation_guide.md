# Web Analyzer Service Implementation Guide

This guide explains how to implement and deploy the updated Web Analyzer service with the new knowledge database functionality.

## System Overview

The Web Analyzer service now uses a knowledge database approach to provide better internal linking suggestions:

1. **Knowledge Database**: Stores analyzed content with extracted entities, topics, and other semantic information
2. **Two-Phase Operation**:
   - First, build a knowledge database of existing content
   - Then, generate link suggestions based on the knowledge database

## Deployment Steps

### 1. API Service Deployment (Render)

1. Log in to your Render account
2. Navigate to the Web Analyzer service dashboard
3. Deploy the updated code by pushing to the connected GitHub repository
4. The deployment will automatically create the necessary data directories

### 2. WordPress Plugin Update

1. Upload the updated web-analyzer plugin (version 1.2.1) to your WordPress site
2. Navigate to Plugins > Installed Plugins
3. Deactivate the old version (if active)
4. Delete the old version
5. Install the new version and activate it

## Configuration Steps

### 1. API Service Configuration

The service will automatically create the knowledge database directories and structure when needed. No additional configuration is required beyond the existing setup.

### 2. WordPress Plugin Configuration

1. Navigate to Web Analyzer > Settings
2. Verify your API connection details (URL, API Key, Site ID)
3. Test the connection using the "Test Connection" button
4. Configure the Knowledge Database mode:
   - Use "Build Knowledge Database" mode initially
   - Process at least 100 posts to build a robust knowledge database
   - Switch to "Generate Link Suggestions" mode after building the database

## Building the Knowledge Database

1. In the WordPress admin, go to Web Analyzer > Settings
2. Select "Knowledge Database Mode" = "Build Knowledge Database"
3. Configure batch settings (post type, limit)
4. Click "Start Processing"
5. Monitor progress in the status panel
6. Repeat with multiple batches if needed until the database status shows "Ready for Analysis"

## Generating Link Suggestions

After building the knowledge database:

1. Change "Knowledge Database Mode" to "Generate Link Suggestions"
2. Process content in batches to generate suggestions
3. Link suggestions will appear in the post editor

## Troubleshooting

### API Connection Issues

1. Use the "Run Detailed Test" button to diagnose API connection problems
2. Check the server environment with "Check Server Environment"
3. Verify API URL, Key, and Site ID are correct
4. Ensure the API service is running on Render

### Knowledge Database Issues

1. Check the Knowledge Database Status panel
2. If the database is not ready, continue building it with more content
3. Verify at least 100 items have been processed

### Link Suggestion Issues

1. Ensure the knowledge database is ready for analysis
2. Check if content is being processed correctly
3. Use the debug functions to verify API responses

## Regular Maintenance

1. Periodically run the "Build Knowledge Database" mode to add new content
2. Monitor the knowledge database status to ensure it remains effective
3. Check analytics to see which link suggestions are being used

## Technical Details

The knowledge database uses SQLite for storage and maintains the following data:
- Content metadata (ID, title, URL)
- Extracted entities by type (clothing items, styles, body shapes, colors)
- Topics and subtopics
- Relationship information between content pieces

The database is designed to automatically clean up older entries when reaching capacity limits.