<?php
/**
 * Direct API Access for Web Analyzer
 * 
 * This file provides a simple way to directly interact with the Web Analyzer API
 * without going through the WordPress REST API which appears to be having issues.
 * 
 * Usage:
 * 1. Upload this file to your WordPress plugins/web-analyzer directory
 * 2. Access it via: https://your-site.com/wp-content/plugins/web-analyzer/direct-api.php
 */

// Load WordPress environment
define('WP_USE_THEMES', false);
require_once('../../../../wp-load.php');

// Basic security check - make sure user is logged in and has proper capabilities
if (!current_user_can('edit_posts')) {
    http_response_code(403);
    echo json_encode(['error' => 'Unauthorized access']);
    exit;
}

// Process only AJAX requests
if (!isset($_SERVER['HTTP_X_REQUESTED_WITH']) || strtolower($_SERVER['HTTP_X_REQUESTED_WITH']) !== 'xmlhttprequest') {
    http_response_code(400);
    echo json_encode(['error' => 'Only AJAX requests are allowed']);
    exit;
}

// Get the operation type
$operation = isset($_GET['op']) ? $_GET['op'] : '';

// Process based on operation
header('Content-Type: application/json');

switch ($operation) {
    case 'get_posts':
        // Get posts for processing
        $post_type = isset($_GET['post_type']) ? sanitize_text_field($_GET['post_type']) : 'post';
        $limit = isset($_GET['limit']) ? intval($_GET['limit']) : 10;
        
        // Query posts
        $args = array(
            'post_type' => $post_type,
            'posts_per_page' => $limit,
            'post_status' => 'publish',
        );
        
        $query = new WP_Query($args);
        $posts = array();
        
        if ($query->have_posts()) {
            while ($query->have_posts()) {
                $query->the_post();
                $post_id = get_the_ID();
                $posts[] = array(
                    'id' => $post_id,
                    'title' => get_the_title(),
                    'content' => apply_filters('the_content', get_the_content()),
                    'url' => get_permalink($post_id)
                );
            }
            wp_reset_postdata();
        }
        
        echo json_encode(['success' => true, 'posts' => $posts]);
        break;
        
    case 'api_request':
        // Get API settings - hardcoded for TheVou
        $api_url = 'https://web-analyzer-api.onrender.com';
        $api_key = 'thevou_api_key_2025_03_24';
        $site_id = 'thevou';
        
        if (empty($api_url) || empty($api_key)) {
            echo json_encode(['success' => false, 'error' => 'API not configured']);
            exit;
        }
        
        // Get request data
        $request_data = json_decode(file_get_contents('php://input'), true);
        if (!$request_data) {
            echo json_encode(['success' => false, 'error' => 'Invalid request data']);
            exit;
        }
        
        // Get endpoint
        $endpoint = isset($_GET['endpoint']) ? sanitize_text_field($_GET['endpoint']) : '';
        if (empty($endpoint)) {
            echo json_encode(['success' => false, 'error' => 'No endpoint specified']);
            exit;
        }
        
        // Make API request
        $request_url = rtrim($api_url, '/') . '/' . ltrim($endpoint, '/');
        $method = isset($_GET['method']) ? strtoupper($_GET['method']) : 'GET';
        
        $args = array(
            'timeout' => 30,
            'headers' => array(
                'X-API-Key' => $api_key,
                'Content-Type' => 'application/json'
            )
        );
        
        if ($method === 'POST') {
            $args['body'] = json_encode($request_data);
            $response = wp_remote_post($request_url, $args);
        } else {
            $response = wp_remote_get($request_url, $args);
        }
        
        if (is_wp_error($response)) {
            echo json_encode(['success' => false, 'error' => $response->get_error_message()]);
            exit;
        }
        
        $body = wp_remote_retrieve_body($response);
        $code = wp_remote_retrieve_response_code($response);
        
        if ($code !== 200) {
            echo json_encode(['success' => false, 'error' => 'API Error', 'code' => $code, 'body' => json_decode($body)]);
            exit;
        }
        
        echo $body;
        break;
        
    default:
        echo json_encode(['error' => 'Unknown operation']);
        break;
}