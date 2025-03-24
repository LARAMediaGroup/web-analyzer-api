<?php
/**
 * Plugin Name: Web Analyzer for Internal Linking
 * Plugin URI: https://laramediagroup.com/web-analyzer
 * Description: Analyze content and suggest relevant internal links based on fashion topics
 * Version: 1.3.5
 * Author: LARA Media Group
 * Author URI: https://laramediagroup.com
 * Text Domain: web-analyzer
 * Domain Path: /languages
 * License: GPL v2 or later
 */

// If this file is called directly, abort.
if (!defined('WPINC')) {
    die;
}

// Define plugin constants
define('WEB_ANALYZER_VERSION', '1.3.5');
define('WEB_ANALYZER_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('WEB_ANALYZER_PLUGIN_URL', plugin_dir_url(__FILE__));

/**
 * The code that runs during plugin activation.
 */
function activate_web_analyzer() {
    require_once WEB_ANALYZER_PLUGIN_DIR . 'includes/class-web-analyzer-activator.php';
    Web_Analyzer_Activator::activate();
}

/**
 * The code that runs during plugin deactivation.
 */
function deactivate_web_analyzer() {
    require_once WEB_ANALYZER_PLUGIN_DIR . 'includes/class-web-analyzer-deactivator.php';
    Web_Analyzer_Deactivator::deactivate();
}

register_activation_hook(__FILE__, 'activate_web_analyzer');
register_deactivation_hook(__FILE__, 'deactivate_web_analyzer');

/**
 * The core plugin class that is used to define internationalization,
 * admin-specific hooks, and public-facing site hooks.
 */
require_once WEB_ANALYZER_PLUGIN_DIR . 'includes/class-web-analyzer.php';

/**
 * Begins execution of the plugin.
 */
function run_web_analyzer() {
    $plugin = new Web_Analyzer();
    $plugin->run();
}
run_web_analyzer();