<?php
/**
 * Provide a admin area view for the plugin
 *
 * This file is used to markup the admin-facing aspects of the plugin.
 *
 * @since      1.0.0
 * @package    Web_Analyzer
 * @subpackage Web_Analyzer/admin/partials
 */

// Ensure this file is being included by a parent file
if (!defined('WPINC')) {
    die;
}
?>

<div class="wrap">
    <h1><?php echo esc_html(get_admin_page_title()); ?></h1>
    
    <div class="web-analyzer-admin-header">
        <div class="web-analyzer-header-info">
            <h2><?php _e('Web Analyzer for Internal Linking', 'web-analyzer'); ?></h2>
            <p><?php _e('Configure your connection to the Web Analyzer API for intelligent internal linking suggestions.', 'web-analyzer'); ?></p>
        </div>
    </div>
    
    <div class="web-analyzer-admin-content">
        <div class="web-analyzer-settings-container">
            <form method="post" action="options.php">
                <?php
                settings_fields($this->plugin_name);
                do_settings_sections($this->plugin_name);
                ?>
                
                <div class="web-analyzer-settings-section">
                    <h2><?php _e('API Configuration', 'web-analyzer'); ?></h2>
                    <p><?php _e('Enter your Web Analyzer API credentials to connect to the service.', 'web-analyzer'); ?></p>
                    
                    <table class="form-table">
                        <tbody>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_api_url"><?php _e('API URL', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <input type="url" id="web_analyzer_api_url" name="web_analyzer_api_url" 
                                           class="regular-text" 
                                           value="<?php echo esc_attr(get_option('web_analyzer_api_url')); ?>" 
                                           placeholder="https://api.example.com" />
                                    <p class="description">
                                        <?php _e('The URL of the Web Analyzer API.', 'web-analyzer'); ?>
                                    </p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_api_key"><?php _e('API Key', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <input type="password" id="web_analyzer_api_key" name="web_analyzer_api_key" 
                                           class="regular-text" 
                                           value="<?php echo esc_attr(get_option('web_analyzer_api_key')); ?>" />
                                    <p class="description">
                                        <?php _e('Your API key for authentication.', 'web-analyzer'); ?>
                                    </p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_site_id"><?php _e('Site ID', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <input type="text" id="web_analyzer_site_id" name="web_analyzer_site_id" 
                                           class="regular-text" 
                                           value="<?php echo esc_attr(get_option('web_analyzer_site_id')); ?>" 
                                           placeholder="thevou" />
                                    <p class="description">
                                        <?php _e('Your site identifier.', 'web-analyzer'); ?>
                                    </p>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div class="web-analyzer-settings-section">
                    <h2><?php _e('Plugin Settings', 'web-analyzer'); ?></h2>
                    <p><?php _e('Configure how the Web Analyzer works with your content.', 'web-analyzer'); ?></p>
                    
                    <table class="form-table">
                        <tbody>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_enabled"><?php _e('Enable Automatic Analysis', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <input type="checkbox" id="web_analyzer_enabled" name="web_analyzer_enabled" 
                                           value="1" <?php checked(get_option('web_analyzer_enabled', true)); ?> />
                                    <p class="description">
                                        <?php _e('Automatically analyze content when saving posts.', 'web-analyzer'); ?>
                                    </p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_use_enhanced"><?php _e('Use Enhanced Analysis', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <input type="checkbox" id="web_analyzer_use_enhanced" name="web_analyzer_use_enhanced" 
                                           value="1" <?php checked(get_option('web_analyzer_use_enhanced', false)); ?> />
                                    <p class="description">
                                        <?php _e('Use advanced analysis with improved entity recognition and semantic understanding.', 'web-analyzer'); ?>
                                    </p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_max_suggestions"><?php _e('Maximum Suggestions', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <input type="number" id="web_analyzer_max_suggestions" name="web_analyzer_max_suggestions" 
                                           class="small-text" 
                                           value="<?php echo esc_attr(get_option('web_analyzer_max_suggestions', 5)); ?>" 
                                           min="1" max="20" />
                                    <p class="description">
                                        <?php _e('Maximum number of link suggestions to show in the editor.', 'web-analyzer'); ?>
                                    </p>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div class="web-analyzer-settings-section">
                    <h2><?php _e('Bulk Processing', 'web-analyzer'); ?></h2>
                    <p><?php _e('Analyze multiple posts at once to generate link suggestions.', 'web-analyzer'); ?></p>
                    
                    <table class="form-table">
                        <tbody>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_bulk_post_type"><?php _e('Post Type', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <select id="web_analyzer_bulk_post_type" name="web_analyzer_bulk_post_type">
                                        <?php
                                        $post_types = get_post_types(array('public' => true), 'objects');
                                        $selected_post_type = get_option('web_analyzer_bulk_post_type', 'post');
                                        
                                        foreach ($post_types as $post_type) {
                                            echo '<option value="' . esc_attr($post_type->name) . '" ' . selected($selected_post_type, $post_type->name, false) . '>' . esc_html($post_type->label) . '</option>';
                                        }
                                        ?>
                                    </select>
                                    <p class="description">
                                        <?php _e('Post type to analyze in bulk.', 'web-analyzer'); ?>
                                    </p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row">
                                    <label for="web_analyzer_bulk_limit"><?php _e('Limit', 'web-analyzer'); ?></label>
                                </th>
                                <td>
                                    <input type="number" id="web_analyzer_bulk_limit" name="web_analyzer_bulk_limit" 
                                           class="small-text" 
                                           value="<?php echo esc_attr(get_option('web_analyzer_bulk_limit', 10)); ?>" 
                                           min="1" max="100" />
                                    <p class="description">
                                        <?php _e('Maximum number of posts to analyze in a single batch (1-100).', 'web-analyzer'); ?>
                                    </p>
                                </td>
                            </tr>
                            <tr>
                                <th scope="row">
                                    <?php _e('Start Bulk Analysis', 'web-analyzer'); ?>
                                </th>
                                <td>
                                    <button type="button" id="web-analyzer-start-bulk" class="button button-primary">
                                        <?php _e('Start Analysis', 'web-analyzer'); ?>
                                    </button>
                                    <div id="web-analyzer-bulk-status" style="margin-top: 10px; display: none;">
                                        <p><strong><?php _e('Job Status:', 'web-analyzer'); ?></strong> <span id="job-status-text">-</span></p>
                                        <p><strong><?php _e('Progress:', 'web-analyzer'); ?></strong> <span id="job-progress">0%</span></p>
                                        <div class="progress-bar" style="background: #f0f0f0; height: 20px; width: 100%; border-radius: 3px; margin-top: 5px;">
                                            <div id="progress-bar-inner" style="background: #2271b1; height: 100%; width: 0%; border-radius: 3px;"></div>
                                        </div>
                                        <p><strong><?php _e('Items Processed:', 'web-analyzer'); ?></strong> <span id="processed-count">0</span>/<span id="total-count">0</span></p>
                                        <p><strong><?php _e('Time Elapsed:', 'web-analyzer'); ?></strong> <span id="time-elapsed">0s</span></p>
                                        <p>
                                            <button type="button" id="web-analyzer-stop-job" class="button button-secondary">
                                                <?php _e('Stop Job', 'web-analyzer'); ?>
                                            </button>
                                            <a href="#" id="view-report-link" style="margin-left: 10px; display: none;">
                                                <?php _e('View Report', 'web-analyzer'); ?>
                                            </a>
                                        </p>
                                    </div>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div class="web-analyzer-settings-section">
                    <h2><?php _e('Connection Test', 'web-analyzer'); ?></h2>
                    <p><?php _e('Test your connection to the Web Analyzer API.', 'web-analyzer'); ?></p>
                    
                    <div class="web-analyzer-connection-test">
                        <button type="button" id="web-analyzer-test-connection" class="button button-secondary">
                            <?php _e('Test Connection', 'web-analyzer'); ?>
                        </button>
                        <span id="web-analyzer-connection-status"></span>
                    </div>
                </div>
                
                <?php submit_button(__('Save Settings', 'web-analyzer'), 'primary', 'submit', true); ?>
            </form>
        </div>
        
        <div class="web-analyzer-sidebar">
            <div class="web-analyzer-sidebar-box">
                <h3><?php _e('How It Works', 'web-analyzer'); ?></h3>
                <ol>
                    <li><?php _e('Configure your API connection settings above', 'web-analyzer'); ?></li>
                    <li><?php _e('Web Analyzer will appear in your post editor', 'web-analyzer'); ?></li>
                    <li><?php _e('Click "Analyze Content" to get link suggestions', 'web-analyzer'); ?></li>
                    <li><?php _e('Insert suggested links with one click', 'web-analyzer'); ?></li>
                </ol>
            </div>
            
            <div class="web-analyzer-sidebar-box">
                <h3><?php _e('Need Help?', 'web-analyzer'); ?></h3>
                <p><?php _e('If you need assistance with this plugin, please contact our support team.', 'web-analyzer'); ?></p>
                <a href="https://thevou.com/support" class="button button-secondary" target="_blank">
                    <?php _e('Get Support', 'web-analyzer'); ?>
                </a>
            </div>
        </div>
    </div>
</div>