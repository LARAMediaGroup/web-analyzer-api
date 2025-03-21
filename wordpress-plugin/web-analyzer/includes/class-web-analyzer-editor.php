<?php
/**
 * Handles integration with the WordPress editor.
 *
 * @since      1.0.0
 * @package    Web_Analyzer
 * @subpackage Web_Analyzer/includes
 */

class Web_Analyzer_Editor {

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
     * The API class instance.
     *
     * @since    1.0.0
     * @access   private
     * @var      Web_Analyzer_API    $api    The API class instance.
     */
    private $api;

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
        $this->api = new Web_Analyzer_API($plugin_name, $version);
    }
    
    /**
     * Add meta box to the classic editor.
     *
     * @since    1.0.0
     */
    public function add_meta_box() {
        // Only add to post types that support the editor
        $post_types = get_post_types_by_support('editor');
        
        // Add meta box to each supported post type
        foreach ($post_types as $post_type) {
            add_meta_box(
                'web_analyzer_metabox',
                __('Internal Link Suggestions', 'web-analyzer'),
                array($this, 'render_meta_box'),
                $post_type,
                'side',
                'high'
            );
        }
    }
    
    /**
     * Render the meta box.
     *
     * @since    1.0.0
     * @param    WP_Post    $post    The post.
     */
    public function render_meta_box($post) {
        wp_nonce_field('web_analyzer_metabox', 'web_analyzer_metabox_nonce');
        
        // Get existing suggestions
        global $wpdb;
        $table_name = $wpdb->prefix . 'web_analyzer_suggestions';
        
        $suggestions = $wpdb->get_results(
            $wpdb->prepare(
                "SELECT * FROM $table_name WHERE post_id = %d ORDER BY confidence DESC LIMIT 5",
                $post->ID
            ),
            ARRAY_A
        );
        
        ?>
        <div id="web-analyzer-classic-editor">
            <div id="web-analyzer-suggestions">
                <?php if (empty($suggestions)) : ?>
                    <p><?php _e('No link suggestions available yet.', 'web-analyzer'); ?></p>
                <?php else : ?>
                    <ul>
                        <?php foreach ($suggestions as $suggestion) : ?>
                            <li>
                                <div class="suggestion">
                                    <span class="anchor-text"><?php echo esc_html($suggestion['anchor_text']); ?></span>
                                    <span class="target-url">
                                        <a href="<?php echo esc_url($suggestion['target_url']); ?>" target="_blank">
                                            <?php echo esc_url($suggestion['target_url']); ?>
                                        </a>
                                    </span>
                                    <button class="button button-small insert-link" 
                                            data-anchor="<?php echo esc_attr($suggestion['anchor_text']); ?>"
                                            data-url="<?php echo esc_url($suggestion['target_url']); ?>"
                                            data-para-index="<?php echo esc_attr($suggestion['paragraph_index']); ?>">
                                        <?php _e('Insert', 'web-analyzer'); ?>
                                    </button>
                                </div>
                                <div class="context">
                                    <?php echo wp_kses_post($suggestion['context']); ?>
                                </div>
                            </li>
                        <?php endforeach; ?>
                    </ul>
                <?php endif; ?>
            </div>
            <div id="web-analyzer-actions">
                <button id="web-analyzer-analyze" class="button button-secondary">
                    <?php _e('Analyze Content', 'web-analyzer'); ?>
                </button>
                <span id="web-analyzer-status"></span>
            </div>
        </div>
        <?php
    }
    
    /**
     * Enqueue assets for the block editor (Gutenberg).
     *
     * @since    1.0.0
     */
    public function enqueue_block_editor_assets() {
        // Enqueue script
        wp_enqueue_script(
            'web-analyzer-block-editor',
            plugin_dir_url(dirname(__FILE__)) . 'admin/js/web-analyzer-block-editor.js',
            array('wp-blocks', 'wp-element', 'wp-editor', 'wp-components', 'wp-i18n', 'wp-data', 'wp-api-fetch'),
            $this->version,
            true
        );
        
        // Pass data to script
        wp_localize_script('web-analyzer-block-editor', 'webAnalyzerData', array(
            'apiNonce' => wp_create_nonce('wp_rest'),
            'apiUrl' => get_rest_url(null, 'web-analyzer/v1'),
            'postId' => get_the_ID(),
            'enabled' => (bool) get_option('web_analyzer_enabled', true),
            'strings' => array(
                'panelTitle' => __('Internal Link Suggestions', 'web-analyzer'),
                'analyzeButton' => __('Analyze Content', 'web-analyzer'),
                'insertButton' => __('Insert', 'web-analyzer'),
                'noSuggestions' => __('No link suggestions available yet.', 'web-analyzer'),
                'analyzing' => __('Analyzing...', 'web-analyzer'),
                'error' => __('Error during analysis', 'web-analyzer'),
                'success' => __('Analysis complete', 'web-analyzer'),
            )
        ));
        
        // Enqueue style
        wp_enqueue_style(
            'web-analyzer-block-editor',
            plugin_dir_url(dirname(__FILE__)) . 'admin/css/web-analyzer-block-editor.css',
            array('wp-edit-blocks'),
            $this->version
        );
    }
    
    /**
     * Save link suggestions when a post is saved.
     *
     * @since    1.0.0
     * @param    int       $post_id    The post ID.
     * @param    WP_Post   $post       The post object.
     * @param    bool      $update     Whether this is an existing post being updated.
     */
    public function save_post_suggestions($post_id, $post, $update) {
        // Don't analyze on autosave or revisions
        if (defined('DOING_AUTOSAVE') && DOING_AUTOSAVE) {
            return;
        }
        
        if (wp_is_post_revision($post_id)) {
            return;
        }
        
        // Check if this post type should be analyzed
        $post_types = get_post_types_by_support('editor');
        if (!in_array($post->post_type, $post_types)) {
            return;
        }
        
        // Get existing suggestions
        global $wpdb;
        $table_name = $wpdb->prefix . 'web_analyzer_suggestions';
        
        $count = $wpdb->get_var(
            $wpdb->prepare(
                "SELECT COUNT(*) FROM $table_name WHERE post_id = %d",
                $post_id
            )
        );
        
        // If no suggestions exist and content is not empty, analyze the post
        if ($count == 0 && !empty($post->post_content) && get_option('web_analyzer_enabled', true)) {
            // Queue analysis using WP Cron
            wp_schedule_single_event(
                time() + 10, // 10 seconds delay
                'web_analyzer_analyze_post',
                array($post_id)
            );
        }
    }
}