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
        
        // Pass data to script
        wp_localize_script($this->plugin_name . '-admin', 'webAnalyzerAdmin', array(
            'apiNonce' => wp_create_nonce('wp_rest'),
            'apiUrl' => get_rest_url(null, 'web-analyzer/v1'),
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('web_analyzer_nonce')
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
            
            // Debug strings
            'runningTest' => __('Running detailed test...', 'web-analyzer'),
            'checkingEnvironment' => __('Checking server environment...', 'web-analyzer'),
            'testStepSuccess' => __('Passed', 'web-analyzer'),
            'testStepFailed' => __('Failed', 'web-analyzer'),
            'testStepWarning' => __('Warning', 'web-analyzer'),
            'testStepInProgress' => __('Testing...', 'web-analyzer'),
            'troubleshooting' => __('Troubleshooting suggestions', 'web-analyzer'),
            
            // Bulk processing strings
            'startingAnalysis' => __('Starting bulk analysis...', 'web-analyzer'),
            'processing' => __('Processing content...', 'web-analyzer'),
            'stoppingJob' => __('Stopping job...', 'web-analyzer'),
            'jobStopped' => __('Job stopped', 'web-analyzer'),
            'jobComplete' => __('Job complete', 'web-analyzer'),
            'jobError' => __('Job failed', 'web-analyzer')
        ));
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