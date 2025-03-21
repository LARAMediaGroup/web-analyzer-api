<?php
/**
 * The public-facing functionality of the plugin.
 *
 * @since      1.0.0
 * @package    Web_Analyzer
 * @subpackage Web_Analyzer/public
 */

class Web_Analyzer_Public {

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
     * Register the stylesheets for the public-facing side of the site.
     *
     * @since    1.0.0
     */
    public function enqueue_styles() {
        wp_enqueue_style(
            $this->plugin_name,
            plugin_dir_url(__FILE__) . 'css/web-analyzer-public.css',
            array(),
            $this->version,
            'all'
        );
    }

    /**
     * Register the JavaScript for the public-facing side of the site.
     *
     * @since    1.0.0
     */
    public function enqueue_scripts() {
        wp_enqueue_script(
            $this->plugin_name,
            plugin_dir_url(__FILE__) . 'js/web-analyzer-public.js',
            array('jquery'),
            $this->version,
            false
        );
        
        wp_localize_script($this->plugin_name, 'webAnalyzerData', array(
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('web_analyzer_track_click')
        ));
    }
    
    /**
     * Track link clicks for analytics.
     *
     * @since    1.0.0
     */
    public function track_link_click() {
        // Check nonce
        if (!isset($_POST['nonce']) || !wp_verify_nonce($_POST['nonce'], 'web_analyzer_track_click')) {
            wp_send_json_error('Invalid nonce');
            return;
        }
        
        // Check required data
        if (!isset($_POST['suggestion_id']) || !is_numeric($_POST['suggestion_id'])) {
            wp_send_json_error('Invalid suggestion ID');
            return;
        }
        
        $suggestion_id = intval($_POST['suggestion_id']);
        
        // Update analytics
        global $wpdb;
        $table_name = $wpdb->prefix . 'web_analyzer_analytics';
        
        // Check if entry exists
        $analytics = $wpdb->get_row(
            $wpdb->prepare(
                "SELECT * FROM $table_name WHERE suggestion_id = %d",
                $suggestion_id
            )
        );
        
        if ($analytics) {
            // Update existing entry
            $wpdb->update(
                $table_name,
                array(
                    'clicks' => $analytics->clicks + 1,
                    'last_clicked' => current_time('mysql'),
                    'last_updated' => current_time('mysql')
                ),
                array('suggestion_id' => $suggestion_id)
            );
        } else {
            // Create new entry
            $wpdb->insert(
                $table_name,
                array(
                    'suggestion_id' => $suggestion_id,
                    'clicks' => 1,
                    'impressions' => 1,
                    'last_clicked' => current_time('mysql'),
                    'last_updated' => current_time('mysql')
                )
            );
        }
        
        wp_send_json_success(array('tracked' => true));
    }
}