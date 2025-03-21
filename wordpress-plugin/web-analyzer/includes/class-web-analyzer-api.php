<?php
/**
 * Handles communication with the Web Analyzer API.
 *
 * @since      1.0.0
 * @package    Web_Analyzer
 * @subpackage Web_Analyzer/includes
 */

class Web_Analyzer_API {

    /**
     * The ID of this plugin.
     *
     * @since    1.0.0
     * @access   private
     * @var      string    $plugin_name    The ID of this plugin.
     */
    private $plugin_name;

    /**
     * The version of this plugin.
     *
     * @since    1.0.0
     * @access   private
     * @var      string    $version    The current version of this plugin.
     */
    private $version;

    /**
     * Initialize the class and set its properties.
     *
     * @since    1.0.0
     * @param    string    $plugin_name       The name of this plugin.
     * @param    string    $version           The version of this plugin.
     */
    public function __construct($plugin_name, $version) {
        $this->plugin_name = $plugin_name;
        $this->version = $version;
    }
    
    /**
     * Register the REST API endpoints.
     *
     * @since    1.0.0
     */
    public function register_routes() {
        // Content analysis endpoint
        register_rest_route('web-analyzer/v1', '/analyze', array(
            'methods' => 'POST',
            'callback' => array($this, 'analyze_content'),
            'permission_callback' => array($this, 'check_permissions'),
            'args' => array(
                'post_id' => array(
                    'required' => true,
                    'validate_callback' => function($param) {
                        return is_numeric($param);
                    }
                ),
            ),
        ));
        
        // Get suggestions endpoint
        register_rest_route('web-analyzer/v1', '/suggestions/(?P<post_id>\d+)', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_suggestions'),
            'permission_callback' => array($this, 'check_permissions'),
            'args' => array(
                'post_id' => array(
                    'validate_callback' => function($param) {
                        return is_numeric($param);
                    }
                ),
            ),
        ));
        
        // Bulk analysis endpoint
        register_rest_route('web-analyzer/v1', '/bulk/analyze', array(
            'methods' => 'POST',
            'callback' => array($this, 'start_bulk_analysis'),
            'permission_callback' => array($this, 'check_permissions'),
            'args' => array(
                'post_type' => array(
                    'required' => false,
                    'default' => 'post',
                    'validate_callback' => function($param) {
                        return is_string($param);
                    }
                ),
                'limit' => array(
                    'required' => false,
                    'default' => 10,
                    'validate_callback' => function($param) {
                        return is_numeric($param);
                    }
                ),
                'categories' => array(
                    'required' => false,
                    'validate_callback' => function($param) {
                        return is_string($param) || is_numeric($param);
                    }
                ),
            ),
        ));
        
        // Job status endpoint
        register_rest_route('web-analyzer/v1', '/bulk/status', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_job_status'),
            'permission_callback' => array($this, 'check_permissions'),
            'args' => array(
                'job_id' => array(
                    'required' => false,
                    'validate_callback' => function($param) {
                        return is_string($param);
                    }
                ),
            ),
        ));
        
        // Job status by ID endpoint
        register_rest_route('web-analyzer/v1', '/bulk/status/(?P<job_id>[a-zA-Z0-9_-]+)', array(
            'methods' => 'GET',
            'callback' => array($this, 'get_job_status'),
            'permission_callback' => array($this, 'check_permissions'),
            'args' => array(
                'job_id' => array(
                    'required' => true,
                    'validate_callback' => function($param) {
                        return is_string($param);
                    }
                ),
            ),
        ));
    }
    
    /**
     * Check if user has permission to access REST API endpoints.
     *
     * @since    1.0.0
     * @return   bool
     */
    public function check_permissions() {
        // Only allow authenticated users with edit_posts capability
        return current_user_can('edit_posts');
    }
    
    /**
     * Analyze content via the API.
     *
     * @since    1.0.0
     * @param    WP_REST_Request    $request    The request.
     * @return   WP_REST_Response
     */
    public function analyze_content($request) {
        $post_id = $request->get_param('post_id');
        $post = get_post($post_id);
        
        if (!$post) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'Post not found'
            ), 404);
        }
        
        // Get the content to analyze
        $content = $post->post_content;
        $title = $post->post_title;
        $url = get_permalink($post_id);
        
        // Check if we should use enhanced analysis
        $use_enhanced = get_option('web_analyzer_use_enhanced', false);
        
        // Make API request
        $suggestions = $this->request_analysis($content, $title, $url, $use_enhanced);
        
        if (is_wp_error($suggestions)) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => $suggestions->get_error_message()
            ), 500);
        }
        
        // Save suggestions to database
        $this->save_suggestions($post_id, $suggestions);
        
        return new WP_REST_Response(array(
            'success' => true,
            'suggestions' => $suggestions,
            'post_id' => $post_id
        ), 200);
    }
    
    /**
     * Start bulk content analysis.
     *
     * @since    1.0.0
     * @param    WP_REST_Request    $request    The request.
     * @return   WP_REST_Response
     */
    public function start_bulk_analysis($request) {
        // Get post parameters
        $post_type = $request->get_param('post_type');
        $limit = $request->get_param('limit');
        $categories = $request->get_param('categories');
        
        // Default to 'post' if no post type specified
        if (!$post_type) {
            $post_type = 'post';
        }
        
        // Set a reasonable default and maximum limit
        if (!$limit || $limit <= 0) {
            $limit = 10;
        } else if ($limit > 100) {
            $limit = 100;
        }
        
        // Query posts
        $args = array(
            'post_type' => $post_type,
            'posts_per_page' => $limit,
            'post_status' => 'publish'
        );
        
        // Add category filter if specified
        if ($categories) {
            $args['cat'] = $categories;
        }
        
        $query = new WP_Query($args);
        
        if (!$query->have_posts()) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => 'No posts found matching the criteria'
            ), 404);
        }
        
        // Prepare posts for bulk processing
        $content_items = array();
        
        foreach ($query->posts as $post) {
            $content_items[] = array(
                'content' => $post->post_content,
                'title' => $post->post_title,
                'url' => get_permalink($post->ID),
                'id' => $post->ID
            );
        }
        
        // Start bulk processing
        $result = $this->request_bulk_processing($content_items);
        
        if (is_wp_error($result)) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => $result->get_error_message()
            ), 500);
        }
        
        // Store job ID for reference
        update_option('web_analyzer_last_job_id', $result['job_id']);
        
        return new WP_REST_Response(array(
            'success' => true,
            'job' => $result,
            'post_count' => count($content_items)
        ), 200);
    }
    
    /**
     * Get status of a bulk processing job.
     *
     * @since    1.0.0
     * @param    WP_REST_Request    $request    The request.
     * @return   WP_REST_Response
     */
    public function get_job_status($request) {
        $job_id = $request->get_param('job_id');
        
        if (!$job_id) {
            // Try to get the last job ID
            $job_id = get_option('web_analyzer_last_job_id');
            
            if (!$job_id) {
                return new WP_REST_Response(array(
                    'success' => false,
                    'message' => 'No job ID specified and no recent job found'
                ), 400);
            }
        }
        
        // Get job status
        $result = $this->request_job_status($job_id);
        
        if (is_wp_error($result)) {
            return new WP_REST_Response(array(
                'success' => false,
                'message' => $result->get_error_message()
            ), 500);
        }
        
        return new WP_REST_Response(array(
            'success' => true,
            'job' => $result
        ), 200);
    }
    
    /**
     * Get suggestions for a post.
     *
     * @since    1.0.0
     * @param    WP_REST_Request    $request    The request.
     * @return   WP_REST_Response
     */
    public function get_suggestions($request) {
        $post_id = $request->get_param('post_id');
        
        global $wpdb;
        $table_name = $wpdb->prefix . 'web_analyzer_suggestions';
        
        $suggestions = $wpdb->get_results(
            $wpdb->prepare(
                "SELECT * FROM $table_name WHERE post_id = %d ORDER BY confidence DESC",
                $post_id
            ),
            ARRAY_A
        );
        
        if (empty($suggestions)) {
            return new WP_REST_Response(array(
                'success' => true,
                'suggestions' => array(),
                'post_id' => $post_id
            ), 200);
        }
        
        return new WP_REST_Response(array(
            'success' => true,
            'suggestions' => $suggestions,
            'post_id' => $post_id
        ), 200);
    }
    
    /**
     * Request analysis from the API.
     *
     * @since    1.0.0
     * @param    string    $content      The content to analyze.
     * @param    string    $title        The title of the content.
     * @param    string    $url          The URL of the content.
     * @param    bool      $use_enhanced Whether to use enhanced analysis.
     * @return   array|WP_Error
     */
    public function request_analysis($content, $title, $url = '', $use_enhanced = false) {
        // Get API settings
        $api_url = get_option('web_analyzer_api_url');
        $api_key = get_option('web_analyzer_api_key');
        $site_id = get_option('web_analyzer_site_id');
        
        if (empty($api_url) || empty($api_key)) {
            return new WP_Error('api_not_configured', 'API not configured. Please set the API URL and API Key in the plugin settings.');
        }
        
        // Prepare the request
        $endpoint = $use_enhanced ? 'analyze/enhanced' : 'analyze/content';
        $request_url = trailingslashit($api_url) . $endpoint;
        
        $args = array(
            'method' => 'POST',
            'timeout' => 45,
            'redirection' => 5,
            'httpversion' => '1.1',
            'headers' => array(
                'Content-Type' => 'application/json',
                'X-API-Key' => $api_key
            ),
            'body' => json_encode(array(
                'content' => $content,
                'title' => $title,
                'url' => $url,
                'site_id' => $site_id
            )),
        );
        
        // Make the request
        $response = wp_remote_post($request_url, $args);
        
        // Check for errors
        if (is_wp_error($response)) {
            return $response;
        }
        
        // Check response code
        $response_code = wp_remote_retrieve_response_code($response);
        if ($response_code != 200) {
            $body = wp_remote_retrieve_body($response);
            $error_message = 'API Error';
            
            if (!empty($body)) {
                $body_json = json_decode($body, true);
                if (isset($body_json['detail'])) {
                    $error_message = $body_json['detail'];
                }
            }
            
            return new WP_Error('api_error', $error_message . ' (Code: ' . $response_code . ')');
        }
        
        // Parse response
        $body = wp_remote_retrieve_body($response);
        $response_data = json_decode($body, true);
        
        if (!isset($response_data['link_suggestions'])) {
            return new WP_Error('api_invalid_response', 'Invalid API response format');
        }
        
        return $response_data['link_suggestions'];
    }
    
    /**
     * Request bulk processing from the API.
     *
     * @since    1.0.0
     * @param    array     $content_items    The content items to process.
     * @return   array|WP_Error
     */
    public function request_bulk_processing($content_items) {
        // Get API settings
        $api_url = get_option('web_analyzer_api_url');
        $api_key = get_option('web_analyzer_api_key');
        $site_id = get_option('web_analyzer_site_id');
        
        if (empty($api_url) || empty($api_key)) {
            return new WP_Error('api_not_configured', 'API not configured. Please set the API URL and API Key in the plugin settings.');
        }
        
        // Prepare the request
        $request_url = trailingslashit($api_url) . 'bulk/process';
        
        $args = array(
            'method' => 'POST',
            'timeout' => 60,
            'redirection' => 5,
            'httpversion' => '1.1',
            'headers' => array(
                'Content-Type' => 'application/json',
                'X-API-Key' => $api_key
            ),
            'body' => json_encode(array(
                'content_items' => $content_items,
                'site_id' => $site_id
            )),
        );
        
        // Make the request
        $response = wp_remote_post($request_url, $args);
        
        // Check for errors
        if (is_wp_error($response)) {
            return $response;
        }
        
        // Check response code
        $response_code = wp_remote_retrieve_response_code($response);
        if ($response_code != 200) {
            $body = wp_remote_retrieve_body($response);
            $error_message = 'API Error';
            
            if (!empty($body)) {
                $body_json = json_decode($body, true);
                if (isset($body_json['detail'])) {
                    $error_message = $body_json['detail'];
                }
            }
            
            return new WP_Error('api_error', $error_message . ' (Code: ' . $response_code . ')');
        }
        
        // Parse response
        $body = wp_remote_retrieve_body($response);
        $response_data = json_decode($body, true);
        
        if (!isset($response_data['job_id'])) {
            return new WP_Error('api_invalid_response', 'Invalid API response format');
        }
        
        return $response_data;
    }
    
    /**
     * Request job status from the API.
     *
     * @since    1.0.0
     * @param    string    $job_id    The job ID.
     * @return   array|WP_Error
     */
    public function request_job_status($job_id) {
        // Get API settings
        $api_url = get_option('web_analyzer_api_url');
        $api_key = get_option('web_analyzer_api_key');
        
        if (empty($api_url) || empty($api_key) || empty($job_id)) {
            return new WP_Error('api_not_configured', 'API not configured or missing job ID.');
        }
        
        // Prepare the request
        $request_url = trailingslashit($api_url) . 'bulk/status/' . $job_id;
        
        $args = array(
            'method' => 'GET',
            'timeout' => 30,
            'redirection' => 5,
            'httpversion' => '1.1',
            'headers' => array(
                'X-API-Key' => $api_key
            )
        );
        
        // Make the request
        $response = wp_remote_get($request_url, $args);
        
        // Check for errors
        if (is_wp_error($response)) {
            return $response;
        }
        
        // Check response code
        $response_code = wp_remote_retrieve_response_code($response);
        if ($response_code != 200) {
            $body = wp_remote_retrieve_body($response);
            $error_message = 'API Error';
            
            if (!empty($body)) {
                $body_json = json_decode($body, true);
                if (isset($body_json['detail'])) {
                    $error_message = $body_json['detail'];
                }
            }
            
            return new WP_Error('api_error', $error_message . ' (Code: ' . $response_code . ')');
        }
        
        // Parse response
        $body = wp_remote_retrieve_body($response);
        $response_data = json_decode($body, true);
        
        if (!isset($response_data['job_id']) || !isset($response_data['status'])) {
            return new WP_Error('api_invalid_response', 'Invalid API response format');
        }
        
        return $response_data;
    }
    
    /**
     * Save suggestions to the database.
     *
     * @since    1.0.0
     * @param    int      $post_id        The post ID.
     * @param    array    $suggestions    The suggestions.
     */
    private function save_suggestions($post_id, $suggestions) {
        global $wpdb;
        $table_name = $wpdb->prefix . 'web_analyzer_suggestions';
        
        // First, remove old suggestions for this post
        $wpdb->delete($table_name, array('post_id' => $post_id));
        
        // Now insert new suggestions
        foreach ($suggestions as $suggestion) {
            $wpdb->insert(
                $table_name,
                array(
                    'post_id' => $post_id,
                    'target_url' => $suggestion['target_url'],
                    'anchor_text' => $suggestion['anchor_text'],
                    'context' => $suggestion['context'],
                    'confidence' => $suggestion['confidence'],
                    'paragraph_index' => $suggestion['paragraph_index'],
                    'created_at' => current_time('mysql')
                )
            );
        }
    }
    
    /**
     * Clean up old data.
     *
     * @since    1.0.0
     */
    public function cleanup_old_data() {
        global $wpdb;
        $table_name = $wpdb->prefix . 'web_analyzer_suggestions';
        $table_name_analytics = $wpdb->prefix . 'web_analyzer_analytics';
        
        // Remove suggestions older than 90 days that were not applied
        $wpdb->query(
            $wpdb->prepare(
                "DELETE FROM $table_name WHERE created_at < %s AND applied = 0",
                date('Y-m-d H:i:s', strtotime('-90 days'))
            )
        );
        
        // Remove analytics with no clicks for suggestions that no longer exist
        $wpdb->query(
            "DELETE a FROM $table_name_analytics a
             LEFT JOIN $table_name s ON a.suggestion_id = s.id
             WHERE s.id IS NULL AND a.clicks = 0"
        );
    }
}