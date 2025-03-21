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
            'apiUrl' => get_rest_url(null, 'web-analyzer/v1')
        ));
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