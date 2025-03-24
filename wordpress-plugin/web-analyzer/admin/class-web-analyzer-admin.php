<?php
/**
 * The admin-specific functionality of the plugin.
 *
 * @since      1.0.0
 * @package    Web_Analyzer
 * @subpackage Web_Analyzer/admin
 */

class Web_Analyzer_Admin {

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
     * Register the stylesheets for the admin area.
     *
     * @since    1.0.0
     */
    public function enqueue_styles() {
        wp_enqueue_style(
            $this->plugin_name . '-admin',
            plugin_dir_url(__FILE__) . 'css/web-analyzer-admin.css',
            array(),
            $this->version,
            'all'
        );
        
        // Add debugging styles
        wp_enqueue_style(
            $this->plugin_name . '-debug',
            plugin_dir_url(__FILE__) . 'css/web-analyzer-debug.css',
            array($this->plugin_name . '-admin'),
            $this->version,
            'all'
        );
    }

    /**
     * Register the JavaScript for the admin area.
     *
     * @since    1.0.0
     */
    public function enqueue_scripts() {
        wp_enqueue_script(
            $this->plugin_name . '-admin',
            plugin_dir_url(__FILE__) . 'js/web-analyzer-admin.js',
            array('jquery'),
            $this->version,
            false
        );
        
        // Add debugging script
        wp_enqueue_script(
            $this->plugin_name . '-debug',
            plugin_dir_url(__FILE__) . 'js/web-analyzer-debug.js',
            array('jquery', $this->plugin_name . '-admin'),
            $this->version,
            false
        );
        
        // Pass data to script
        wp_localize_script($this->plugin_name . '-admin', 'webAnalyzerAdmin', array(
            'apiNonce' => wp_create_nonce('wp_rest'),
            'apiUrl' => get_rest_url(null, 'web-analyzer/v1'),
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('web_analyzer_nonce'),
            'debug' => true,
            'pluginVersion' => $this->version,
            'pluginName' => $this->plugin_name,
            'renderApiUrl' => get_option('web_analyzer_api_url', ''),
            'supportUrl' => 'https://laramediagroup.com/contact-us/'
        ));
        
        // Add localization data that was missing
        wp_localize_script($this->plugin_name . '-admin', 'webAnalyzerL10n', array(
            // Connection test strings
            'testing' => __('Testing connection...', 'web-analyzer'),
            'testConnection' => __('Test Connection', 'web-analyzer'),
            'connectionSuccess' => __('Connection successful!', 'web-analyzer'),
            'connectionError' => __('Connection failed', 'web-analyzer'),
            'connectionTimeout' => __('Connection timed out', 'web-analyzer'),
            'authError' => __('Authentication failed', 'web-analyzer'),
            'invalidResponse' => __('Invalid response from API', 'web-analyzer'),
            'missingUrl' => __('Please enter the API URL', 'web-analyzer'),
            'missingKey' => __('Please enter your API key', 'web-analyzer'),
            
            // Analysis strings
            'analyzing' => __('Analyzing...', 'web-analyzer'),
            'analyzeContent' => __('Analyze Content', 'web-analyzer'),
            'analysisError' => __('Analysis failed', 'web-analyzer'),
            'noSuggestions' => __('No link suggestions available yet.', 'web-analyzer'),
            'analyzingContent' => __('Analyzing your content...', 'web-analyzer'),
            'analysisSent' => __('Analysis request sent', 'web-analyzer'),
            'analysisReceived' => __('Analysis results received', 'web-analyzer'),
            'processingSuggestions' => __('Processing suggestions...', 'web-analyzer'),
            'insertingLink' => __('Inserting link...', 'web-analyzer'),
            
            // Debug strings
            'runningTest' => __('Running detailed test...', 'web-analyzer'),
            'checkingEnvironment' => __('Checking server environment...', 'web-analyzer'),
            'testStepSuccess' => __('Passed', 'web-analyzer'),
            'testStepFailed' => __('Failed', 'web-analyzer'),
            'testStepWarning' => __('Warning', 'web-analyzer'),
            'testStepInProgress' => __('Testing...', 'web-analyzer'),
            'troubleshooting' => __('Troubleshooting suggestions', 'web-analyzer'),
            'debugEnabled' => __('Debug logging enabled', 'web-analyzer'),
            'debugDisabled' => __('Debug logging disabled', 'web-analyzer'),
            'logCleared' => __('Debug log cleared', 'web-analyzer'),
            'logExported' => __('Debug log exported', 'web-analyzer'),
            'systemChecks' => __('Running system checks...', 'web-analyzer'),
            'apiTests' => __('Testing API connection...', 'web-analyzer'),
            
            // Bulk processing strings
            'startingAnalysis' => __('Starting bulk analysis...', 'web-analyzer'),
            'startAnalysis' => __('Start Analysis', 'web-analyzer'),
            'startProcessing' => __('Start Processing', 'web-analyzer'),
            'processing' => __('Processing content...', 'web-analyzer'),
            'stoppingJob' => __('Stopping job...', 'web-analyzer'),
            'jobStopped' => __('Job stopped', 'web-analyzer'),
            'jobComplete' => __('Job complete', 'web-analyzer'),
            'jobError' => __('Job failed', 'web-analyzer'),
            'processingItem' => __('Processing item', 'web-analyzer'),
            'batchComplete' => __('Batch complete', 'web-analyzer'),
            
            // Knowledge database strings
            'buildingDatabase' => __('Building knowledge database...', 'web-analyzer'),
            'generatingSuggestions' => __('Generating link suggestions...', 'web-analyzer'),
            'knowledgeReady' => __('Knowledge database ready', 'web-analyzer'),
            'knowledgeNotReady' => __('Knowledge database not ready', 'web-analyzer'),
            'refreshingStatus' => __('Refreshing status...', 'web-analyzer'),
            'databaseStatus' => __('Database Status', 'web-analyzer')
        ));
    }
    
    /**
     * Test API connection and return detailed results.
     * AJAX endpoint for the debug functionality.
     *
     * @since    1.2.0
     */
    public function test_api_connection() {
        // Verify nonce
        check_ajax_referer('web_analyzer_nonce', 'nonce');
        
        // Check if user has permissions
        if (!current_user_can('manage_options')) {
            wp_send_json_error(['message' => 'Permission denied']);
            return;
        }
        
        // Get API settings
        $api_url = get_option('web_analyzer_api_url', '');
        $api_key = get_option('web_analyzer_api_key', '');
        $site_id = get_option('web_analyzer_site_id', '');
        
        $results = array(
            'success' => false,
            'steps' => array(),
            'errors' => array()
        );
        
        // Step 1: Validate URL
        $results['steps']['url_validation'] = $this->validate_api_url($api_url);
        
        // If URL validation failed, return early
        if (!$results['steps']['url_validation']['success']) {
            $results['errors'][] = 'API URL validation failed';
            wp_send_json_error($results);
            return;
        }
        
        // Step 2: Check API key
        $results['steps']['api_key'] = $this->validate_api_key($api_key);
        
        // If API key validation failed, return early
        if (!$results['steps']['api_key']['success']) {
            $results['errors'][] = 'API key validation failed';
            wp_send_json_error($results);
            return;
        }
        
        // Step 3: Test health endpoint
        $results['steps']['health_check'] = $this->test_api_health($api_url, $api_key);
        
        // If health check failed, return early
        if (!$results['steps']['health_check']['success']) {
            $results['errors'][] = 'API health check failed';
            wp_send_json_error($results);
            return;
        }
        
        // Step 4: Test site configuration
        $results['steps']['site_config'] = $this->test_site_config($api_url, $api_key, $site_id);
        
        // Determine overall success
        $results['success'] = !empty($results['steps']['site_config']['success']);
        
        if (!$results['success']) {
            $results['errors'][] = 'Site configuration test failed';
            wp_send_json_error($results);
        } else {
            wp_send_json_success($results);
        }
    }
    
    /**
     * Validate API URL format.
     *
     * @since    1.2.0
     * @param    string    $url    The URL to validate.
     * @return   array             Validation results.
     */
    private function validate_api_url($url) {
        $result = array(
            'success' => false,
            'message' => '',
            'data' => null
        );
        
        if (empty($url)) {
            $result['message'] = 'API URL is empty';
            return $result;
        }
        
        // Check if URL has a valid format
        if (filter_var($url, FILTER_VALIDATE_URL) === false) {
            $result['message'] = 'API URL is not a valid URL format';
            return $result;
        }
        
        // Check if URL has https protocol
        if (parse_url($url, PHP_URL_SCHEME) !== 'https') {
            $result['message'] = 'API URL should use HTTPS protocol for security';
            return $result;
        }
        
        // Remove trailing slash if present
        if (substr($url, -1) === '/') {
            $result['message'] = 'API URL should not have a trailing slash';
            return $result;
        }
        
        $result['success'] = true;
        $result['message'] = 'API URL is valid';
        $result['data'] = $url;
        
        return $result;
    }
    
    /**
     * Validate API key format.
     *
     * @since    1.2.0
     * @param    string    $api_key    The API key to validate.
     * @return   array                 Validation results.
     */
    private function validate_api_key($api_key) {
        $result = array(
            'success' => false,
            'message' => '',
            'data' => null
        );
        
        if (empty($api_key)) {
            $result['message'] = 'API key is empty';
            return $result;
        }
        
        // Basic format check - API keys should be reasonably complex
        // This is just a basic check, actual validation happens on the API side
        if (strlen($api_key) < 8) {
            $result['message'] = 'API key seems too short (should be at least 8 characters)';
            return $result;
        }
        
        $result['success'] = true;
        $result['message'] = 'API key format is valid';
        $result['data'] = 'API key is provided (hidden for security)';
        
        return $result;
    }
    
    /**
     * Test the API health endpoint.
     *
     * @since    1.2.0
     * @param    string    $api_url    The API URL.
     * @param    string    $api_key    The API key.
     * @return   array                 Test results.
     */
    private function test_api_health($api_url, $api_key) {
        $result = array(
            'success' => false,
            'message' => '',
            'data' => null
        );
        
        $response = wp_remote_get(
            $api_url . '/health',
            array(
                'timeout' => 15,
                'headers' => array(
                    'X-API-Key' => $api_key
                )
            )
        );
        
        // Check for errors
        if (is_wp_error($response)) {
            $result['message'] = 'Error connecting to API: ' . $response->get_error_message();
            return $result;
        }
        
        // Check response code
        $status_code = wp_remote_retrieve_response_code($response);
        if ($status_code !== 200) {
            $result['message'] = 'API health check failed with status code: ' . $status_code;
            $result['data'] = array(
                'status_code' => $status_code,
                'response' => wp_remote_retrieve_body($response)
            );
            return $result;
        }
        
        // Parse response body
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        if (!$data || !isset($data['status'])) {
            $result['message'] = 'Invalid response from API health endpoint';
            $result['data'] = $body;
            return $result;
        }
        
        if ($data['status'] !== 'ok') {
            $result['message'] = 'API health check returned non-ok status: ' . $data['status'];
            $result['data'] = $data;
            return $result;
        }
        
        $result['success'] = true;
        $result['message'] = 'API health check successful';
        $result['data'] = $data;
        
        return $result;
    }
    
    /**
     * Test site configuration with the API.
     *
     * @since    1.2.0
     * @param    string    $api_url    The API URL.
     * @param    string    $api_key    The API key.
     * @param    string    $site_id    The site ID.
     * @return   array                 Test results.
     */
    private function test_site_config($api_url, $api_key, $site_id) {
        $result = array(
            'success' => false,
            'message' => '',
            'data' => null
        );
        
        if (empty($site_id)) {
            $result['message'] = 'Site ID is empty';
            return $result;
        }
        
        // Test with a minimal content request
        $test_data = array(
            'content' => 'This is a test content.',
            'title' => 'Test Title',
            'site_id' => $site_id,
            'url' => get_site_url()
        );
        
        $response = wp_remote_post(
            $api_url . '/analyze/content',
            array(
                'timeout' => 30,
                'headers' => array(
                    'X-API-Key' => $api_key,
                    'Content-Type' => 'application/json'
                ),
                'body' => json_encode($test_data)
            )
        );
        
        // Check for errors
        if (is_wp_error($response)) {
            $result['message'] = 'Error connecting to API: ' . $response->get_error_message();
            return $result;
        }
        
        // Check response code
        $status_code = wp_remote_retrieve_response_code($response);
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        // A 400 error with content validation is actually a good sign
        // It means authentication worked but found issues with the test content
        if ($status_code === 400 && $data && isset($data['detail']) && strpos($data['detail'], 'content') !== false) {
            $result['success'] = true;
            $result['message'] = 'API accepted the request but reported content validation issues (expected for test data)';
            $result['data'] = array(
                'status_code' => $status_code,
                'response' => $data
            );
            return $result;
        }
        
        // A 200 response is also good
        if ($status_code === 200) {
            $result['success'] = true;
            $result['message'] = 'API accepted the site configuration and processed the request';
            $result['data'] = array(
                'status_code' => $status_code,
                'response' => $data
            );
            return $result;
        }
        
        // Any other response is an error
        $result['message'] = 'Site configuration test failed with status code: ' . $status_code;
        $result['data'] = array(
            'status_code' => $status_code,
            'response' => $data
        );
        
        return $result;
    }
    
    /**
     * Log debug message from JavaScript.
     * AJAX endpoint for the debug functionality.
     *
     * @since    1.2.0
     */
    public function log_debug_message() {
        // Verify nonce
        check_ajax_referer('web_analyzer_nonce', 'nonce');
        
        // Get message data
        $message = isset($_POST['message']) ? sanitize_text_field($_POST['message']) : '';
        $level = isset($_POST['level']) ? sanitize_text_field($_POST['level']) : 'debug';
        $context = isset($_POST['context']) ? $_POST['context'] : array();
        
        if (empty($message)) {
            wp_send_json_error(['message' => 'No message provided']);
            return;
        }
        
        // Log to WordPress debug log if available
        if (defined('WP_DEBUG') && WP_DEBUG === true && defined('WP_DEBUG_LOG') && WP_DEBUG_LOG === true) {
            error_log('[Web Analyzer] [' . strtoupper($level) . '] ' . $message);
        }
        
        // Store in plugin's own log
        $this->write_to_debug_log($message, $level, $context);
        
        wp_send_json_success(['message' => 'Logged message']);
    }
    
    /**
     * Write to the plugin's debug log file.
     *
     * @since    1.2.0
     * @param    string    $message    The message to log.
     * @param    string    $level      The log level (debug, info, warning, error).
     * @param    array     $context    Additional context data.
     */
    private function write_to_debug_log($message, $level = 'debug', $context = array()) {
        // Create logs directory if it doesn't exist
        $logs_dir = WP_CONTENT_DIR . '/web-analyzer-logs';
        if (!file_exists($logs_dir)) {
            wp_mkdir_p($logs_dir);
            
            // Add an .htaccess file to prevent direct access
            $htaccess_content = "# Prevent direct access to log files\n" .
                                "Order deny,allow\n" .
                                "Deny from all";
            file_put_contents($logs_dir . '/.htaccess', $htaccess_content);
        }
        
        // Determine log file path
        $log_file = $logs_dir . '/debug.log';
        
        // Format log entry
        $timestamp = date('Y-m-d H:i:s');
        $level_upper = strtoupper($level);
        $context_str = empty($context) ? '' : ' ' . json_encode($context);
        $log_entry = "[{$timestamp}] [{$level_upper}] {$message}{$context_str}\n";
        
        // Append to log file
        file_put_contents($log_file, $log_entry, FILE_APPEND);
    }
    
    /**
     * Check server environment for compatibility issues.
     * AJAX endpoint for the debug functionality.
     *
     * @since    1.0.0
     */
    public function check_environment() {
        // Verify nonce
        check_ajax_referer('web_analyzer_nonce', 'nonce');
        
        // Check if user has permissions
        if (!current_user_can('manage_options')) {
            wp_send_json_error(['message' => 'Permission denied']);
            return;
        }
        
        // Get PHP version
        $php_version = phpversion();
        $php_min_version = '7.3.0';
        $php_ok = version_compare($php_version, $php_min_version, '>=');
        
        // Get WordPress version
        global $wp_version;
        $wp_min_version = '5.3';
        $wp_ok = version_compare($wp_version, $wp_min_version, '>=');
        
        // Check cURL
        $curl_enabled = function_exists('curl_version');
        
        // Check JSON
        $json_enabled = function_exists('json_encode') && function_exists('json_decode');
        
        // Check memory limit
        $memory_limit = ini_get('memory_limit');
        $memory_limit_bytes = wp_convert_hr_to_bytes($memory_limit);
        $memory_ok = $memory_limit_bytes >= 64 * 1024 * 1024; // 64MB minimum
        
        // Check max execution time
        $max_execution_time = ini_get('max_execution_time');
        $execution_ok = $max_execution_time == 0 || $max_execution_time >= 30; // 0 = unlimited, or at least 30 seconds
        
        // Get active plugins
        $active_plugins = [];
        if (is_multisite()) {
            $plugins = get_site_option('active_sitewide_plugins');
            if (!empty($plugins)) {
                $active_plugins = array_keys($plugins);
            }
        }
        $plugins = get_option('active_plugins');
        if (!empty($plugins)) {
            $active_plugins = array_merge($active_plugins, $plugins);
        }
        
        // Format plugin information
        $formatted_plugins = [];
        foreach ($active_plugins as $plugin) {
            $plugin_data = get_plugin_data(WP_PLUGIN_DIR . '/' . $plugin);
            if (!empty($plugin_data['Name'])) {
                $formatted_plugins[] = $plugin_data['Name'] . ' ' . $plugin_data['Version'];
            }
        }
        
        // Check for potential issues
        $issues = [];
        
        if (!$php_ok) {
            $issues[] = sprintf(
                __('PHP version %s is below the recommended version %s', 'web-analyzer'),
                $php_version,
                $php_min_version
            );
        }
        
        if (!$wp_ok) {
            $issues[] = sprintf(
                __('WordPress version %s is below the recommended version %s', 'web-analyzer'),
                $wp_version,
                $wp_min_version
            );
        }
        
        if (!$curl_enabled) {
            $issues[] = __('cURL extension is not enabled, which is required for API communication', 'web-analyzer');
        }
        
        if (!$json_enabled) {
            $issues[] = __('JSON extension is not enabled, which is required for API communication', 'web-analyzer');
        }
        
        if (!$memory_ok) {
            $issues[] = sprintf(
                __('Memory limit %s is below the recommended minimum of 64MB', 'web-analyzer'),
                $memory_limit
            );
        }
        
        if (!$execution_ok) {
            $issues[] = sprintf(
                __('Max execution time %s seconds is below the recommended minimum of 30 seconds', 'web-analyzer'),
                $max_execution_time
            );
        }
        
        // Return the data
        wp_send_json_success([
            'php_version' => $php_version,
            'wp_version' => $wp_version,
            'curl_enabled' => $curl_enabled,
            'json_enabled' => $json_enabled,
            'memory_limit' => $memory_limit,
            'max_execution_time' => $max_execution_time,
            'active_plugins' => $formatted_plugins,
            'issues' => $issues
        ]);
    }
    
    /**
     * Add menu items to the admin menu.
     *
     * @since    1.0.0
     */
    public function add_plugin_admin_menu() {
        add_menu_page(
            __('Web Analyzer Settings', 'web-analyzer'),
            __('Web Analyzer', 'web-analyzer'),
            'manage_options',
            $this->plugin_name,
            array($this, 'display_plugin_admin_page'),
            'dashicons-admin-links',
            65
        );
        
        add_submenu_page(
            $this->plugin_name,
            __('Settings', 'web-analyzer'),
            __('Settings', 'web-analyzer'),
            'manage_options',
            $this->plugin_name,
            array($this, 'display_plugin_admin_page')
        );
        
        add_submenu_page(
            $this->plugin_name,
            __('Analytics', 'web-analyzer'),
            __('Analytics', 'web-analyzer'),
            'manage_options',
            $this->plugin_name . '-analytics',
            array($this, 'display_plugin_analytics_page')
        );
    }
    
    /**
     * Add settings action link to the plugins page.
     *
     * @since    1.0.0
     * @param    array    $links    Action links.
     * @return   array    Action links.
     */
    public function add_action_links($links) {
        $settings_link = array(
            '<a href="' . admin_url('admin.php?page=' . $this->plugin_name) . '">' . __('Settings', 'web-analyzer') . '</a>',
        );
        return array_merge($settings_link, $links);
    }
    
    /**
     * Register the settings for the plugin.
     *
     * @since    1.0.0
     */
    public function register_settings() {
        register_setting($this->plugin_name, 'web_analyzer_api_url');
        register_setting($this->plugin_name, 'web_analyzer_api_key');
        register_setting($this->plugin_name, 'web_analyzer_site_id');
        register_setting($this->plugin_name, 'web_analyzer_enabled');
        register_setting($this->plugin_name, 'web_analyzer_max_suggestions');
        register_setting($this->plugin_name, 'web_analyzer_use_enhanced');
        register_setting($this->plugin_name, 'web_analyzer_bulk_post_type');
        register_setting($this->plugin_name, 'web_analyzer_bulk_limit');
        register_setting($this->plugin_name, 'web_analyzer_last_job_id');
        register_setting($this->plugin_name, 'web_analyzer_knowledge_mode');
    }
    
    /**
     * Render the settings page for this plugin.
     *
     * @since    1.0.0
     */
    public function display_plugin_admin_page() {
        include_once('partials/web-analyzer-admin-display.php');
    }
    
    /**
     * Render the analytics page for this plugin.
     *
     * @since    1.0.0
     */
    public function display_plugin_analytics_page() {
        include_once('partials/web-analyzer-analytics-display.php');
    }
}