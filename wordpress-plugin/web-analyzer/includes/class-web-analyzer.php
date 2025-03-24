<?php
/**
 * The core plugin class.
 *
 * This is used to define internationalization, admin-specific hooks, and
 * public-facing site hooks.
 *
 * @since      1.0.0
 * @package    Web_Analyzer
 * @subpackage Web_Analyzer/includes
 */

class Web_Analyzer {

    /**
     * The loader that's responsible for maintaining and registering all hooks that power
     * the plugin.
     *
     * @since    1.0.0
     * @access   protected
     * @var      Web_Analyzer_Loader    $loader    Maintains and registers all hooks for the plugin.
     */
    protected $loader;

    /**
     * The unique identifier of this plugin.
     *
     * @since    1.0.0
     * @access   protected
     * @var      string    $plugin_name    The string used to uniquely identify this plugin.
     */
    protected $plugin_name;

    /**
     * The current version of the plugin.
     *
     * @since    1.0.0
     * @access   protected
     * @var      string    $version    The current version of the plugin.
     */
    protected $version;

    /**
     * Define the core functionality of the plugin.
     *
     * @since    1.0.0
     */
    public function __construct() {
        $this->version = WEB_ANALYZER_VERSION;
        $this->plugin_name = 'web-analyzer';

        $this->load_dependencies();
        $this->set_locale();
        $this->define_admin_hooks();
        $this->define_public_hooks();
        $this->define_api_hooks();
        $this->define_editor_hooks();
    }

    /**
     * Load the required dependencies for this plugin.
     *
     * @since    1.0.0
     * @access   private
     */
    private function load_dependencies() {
        /**
         * The class responsible for orchestrating the actions and filters of the
         * core plugin.
         */
        require_once plugin_dir_path(dirname(__FILE__)) . 'includes/class-web-analyzer-loader.php';

        /**
         * The class responsible for defining internationalization functionality
         * of the plugin.
         */
        require_once plugin_dir_path(dirname(__FILE__)) . 'includes/class-web-analyzer-i18n.php';

        /**
         * The class responsible for defining all actions that occur in the admin area.
         */
        require_once plugin_dir_path(dirname(__FILE__)) . 'admin/class-web-analyzer-admin.php';

        /**
         * The class responsible for defining all actions that occur in the public-facing
         * side of the site.
         */
        require_once plugin_dir_path(dirname(__FILE__)) . 'public/class-web-analyzer-public.php';
        
        /**
         * The class responsible for API communications.
         */
        require_once plugin_dir_path(dirname(__FILE__)) . 'includes/class-web-analyzer-api.php';
        
        /**
         * The class responsible for editor integration.
         */
        require_once plugin_dir_path(dirname(__FILE__)) . 'includes/class-web-analyzer-editor.php';

        $this->loader = new Web_Analyzer_Loader();
    }

    /**
     * Define the locale for this plugin for internationalization.
     *
     * @since    1.0.0
     * @access   private
     */
    private function set_locale() {
        $plugin_i18n = new Web_Analyzer_i18n();
        $this->loader->add_action('plugins_loaded', $plugin_i18n, 'load_plugin_textdomain');
    }

    /**
     * Register all of the hooks related to the admin area functionality
     * of the plugin.
     *
     * @since    1.0.0
     * @access   private
     */
    private function define_admin_hooks() {
        $plugin_admin = new Web_Analyzer_Admin($this->get_plugin_name(), $this->get_version());

        $this->loader->add_action('admin_enqueue_scripts', $plugin_admin, 'enqueue_styles');
        $this->loader->add_action('admin_enqueue_scripts', $plugin_admin, 'enqueue_scripts');
        
        // Add menu items
        $this->loader->add_action('admin_menu', $plugin_admin, 'add_plugin_admin_menu');
        
        // Add settings link on plugin page
        $this->loader->add_filter('plugin_action_links_' . plugin_basename(plugin_dir_path(dirname(__FILE__)) . $this->plugin_name . '.php'), 
            $plugin_admin, 'add_action_links');
            
        // Save settings
        $this->loader->add_action('admin_init', $plugin_admin, 'register_settings');
        
        // Register AJAX handlers
        $this->loader->add_action('wp_ajax_web_analyzer_check_environment', $plugin_admin, 'check_environment');
        $this->loader->add_action('wp_ajax_web_analyzer_test_api_connection', $plugin_admin, 'test_api_connection');
        $this->loader->add_action('wp_ajax_web_analyzer_debug_log', $plugin_admin, 'log_debug_message');
    }

    /**
     * Register all of the hooks related to the public-facing functionality
     * of the plugin.
     *
     * @since    1.0.0
     * @access   private
     */
    private function define_public_hooks() {
        $plugin_public = new Web_Analyzer_Public($this->get_plugin_name(), $this->get_version());

        $this->loader->add_action('wp_enqueue_scripts', $plugin_public, 'enqueue_styles');
        $this->loader->add_action('wp_enqueue_scripts', $plugin_public, 'enqueue_scripts');
        
        // Track link clicks for analytics
        $this->loader->add_action('wp_ajax_web_analyzer_track_click', $plugin_public, 'track_link_click');
        $this->loader->add_action('wp_ajax_nopriv_web_analyzer_track_click', $plugin_public, 'track_link_click');
    }
    
    /**
     * Register all of the hooks related to the API functionality
     * of the plugin.
     *
     * @since    1.0.0
     * @access   private
     */
    private function define_api_hooks() {
        $plugin_api = new Web_Analyzer_API($this->get_plugin_name(), $this->get_version());
        
        // Register REST API endpoints
        $this->loader->add_action('rest_api_init', $plugin_api, 'register_routes');
        
        // Schedule cleanup
        $this->loader->add_action('web_analyzer_weekly_cleanup', $plugin_api, 'cleanup_old_data');
    }
    
    /**
     * Register all of the hooks related to the editor integration
     * of the plugin.
     *
     * @since    1.0.0
     * @access   private
     */
    private function define_editor_hooks() {
        $plugin_editor = new Web_Analyzer_Editor($this->get_plugin_name(), $this->get_version());
        
        // Classic Editor integration
        $this->loader->add_action('add_meta_boxes', $plugin_editor, 'add_meta_box');
        
        // Gutenberg Editor integration
        $this->loader->add_action('enqueue_block_editor_assets', $plugin_editor, 'enqueue_block_editor_assets');
        
        // Save suggestions when post is updated
        $this->loader->add_action('save_post', $plugin_editor, 'save_post_suggestions', 10, 3);
    }

    /**
     * Run the loader to execute all of the hooks with WordPress.
     *
     * @since    1.0.0
     */
    public function run() {
        $this->loader->run();
    }

    /**
     * The name of the plugin used to uniquely identify it within the context of
     * WordPress and to define internationalization functionality.
     *
     * @since     1.0.0
     * @return    string    The name of the plugin.
     */
    public function get_plugin_name() {
        return $this->plugin_name;
    }

    /**
     * The reference to the class that orchestrates the hooks with the plugin.
     *
     * @since     1.0.0
     * @return    Web_Analyzer_Loader    Orchestrates the hooks of the plugin.
     */
    public function get_loader() {
        return $this->loader;
    }

    /**
     * Retrieve the version number of the plugin.
     *
     * @since     1.0.0
     * @return    string    The version number of the plugin.
     */
    public function get_version() {
        return $this->version;
    }
}