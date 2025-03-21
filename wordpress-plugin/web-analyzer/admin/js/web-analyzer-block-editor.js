/**
 * Web Analyzer - Block Editor Integration
 * 
 * This script provides integration with the WordPress Block Editor (Gutenberg)
 * for the Web Analyzer plugin.
 */

(function( wp ) {
    'use strict';
    
    // Extract required components
    const { __ } = wp.i18n;
    const { registerPlugin } = wp.plugins;
    const { PluginSidebar, PluginSidebarMoreMenuItem } = wp.editPost;
    const { PanelBody, Button, Spinner, Notice } = wp.components;
    const { withSelect, withDispatch } = wp.data;
    const { compose } = wp.compose;
    const { Component, Fragment } = wp.element;
    const apiFetch = wp.apiFetch;
    
    /**
     * Web Analyzer Sidebar Component
     */
    class WebAnalyzerSidebar extends Component {
        constructor() {
            super( ...arguments );
            
            this.state = {
                isAnalyzing: false,
                error: null,
                suggestions: [],
                loaded: false
            };
            
            this.analyzeContent = this.analyzeContent.bind( this );
            this.insertLink = this.insertLink.bind( this );
            this.loadSuggestions = this.loadSuggestions.bind( this );
        }
        
        /**
         * When component mounts, load suggestions if they exist
         */
        componentDidMount() {
            this.loadSuggestions();
        }
        
        /**
         * Load existing suggestions for the current post
         */
        loadSuggestions() {
            const { postId } = this.props;
            
            if ( !postId ) {
                return;
            }
            
            this.setState({ loaded: false });
            
            apiFetch( {
                path: `${webAnalyzerData.apiUrl}/suggestions/${postId}`,
                method: 'GET'
            } ).then( response => {
                if ( response.success && response.suggestions ) {
                    this.setState({
                        suggestions: response.suggestions,
                        loaded: true
                    });
                } else {
                    this.setState({
                        suggestions: [],
                        loaded: true
                    });
                }
            } ).catch( error => {
                this.setState({
                    error: error.message,
                    loaded: true
                });
            } );
        }
        
        /**
         * Analyze the content of the current post
         */
        analyzeContent() {
            const { postId, content } = this.props;
            
            if ( !postId || !content ) {
                this.setState({
                    error: __( 'No content to analyze', 'web-analyzer' )
                });
                return;
            }
            
            this.setState({
                isAnalyzing: true,
                error: null
            });
            
            apiFetch( {
                path: `${webAnalyzerData.apiUrl}/analyze`,
                method: 'POST',
                data: {
                    post_id: postId
                }
            } ).then( response => {
                if ( response.success ) {
                    this.setState({
                        suggestions: response.suggestions,
                        isAnalyzing: false
                    });
                } else {
                    this.setState({
                        error: response.message || __( 'Unknown error', 'web-analyzer' ),
                        isAnalyzing: false
                    });
                }
            } ).catch( error => {
                this.setState({
                    error: error.message,
                    isAnalyzing: false
                });
            } );
        }
        
        /**
         * Insert a link into the editor
         */
        insertLink( suggestion ) {
            const { insertLink } = this.props;
            
            if ( !insertLink ) {
                this.setState({
                    error: __( 'Cannot insert link - editor not ready', 'web-analyzer' )
                });
                return;
            }
            
            insertLink( suggestion.anchor_text, suggestion.target_url );
            
            // Mark as applied in the database
            apiFetch( {
                path: `/wp/v2/web-analyzer/apply-suggestion/${suggestion.id}`,
                method: 'POST'
            } ).catch( error => {
                console.error( 'Failed to mark suggestion as applied', error );
            } );
        }
        
        /**
         * Render the component
         */
        render() {
            const { isAnalyzing, error, suggestions, loaded } = this.state;
            
            return (
                <Fragment>
                    <PluginSidebarMoreMenuItem
                        target="web-analyzer-sidebar"
                    >
                        { webAnalyzerData.strings.panelTitle }
                    </PluginSidebarMoreMenuItem>
                    <PluginSidebar
                        name="web-analyzer-sidebar"
                        title={ webAnalyzerData.strings.panelTitle }
                    >
                        <PanelBody>
                            <div className="web-analyzer-sidebar-content">
                                { error && (
                                    <Notice status="error" isDismissible={ true } onRemove={ () => this.setState({ error: null }) }>
                                        { error }
                                    </Notice>
                                ) }
                                
                                <div className="web-analyzer-actions">
                                    <Button
                                        isPrimary
                                        onClick={ this.analyzeContent }
                                        disabled={ isAnalyzing }
                                    >
                                        { isAnalyzing ? webAnalyzerData.strings.analyzing : webAnalyzerData.strings.analyzeButton }
                                        { isAnalyzing && <Spinner /> }
                                    </Button>
                                </div>
                                
                                <div className="web-analyzer-suggestions">
                                    { !loaded && <Spinner /> }
                                    
                                    { loaded && suggestions.length === 0 && (
                                        <p>{ webAnalyzerData.strings.noSuggestions }</p>
                                    ) }
                                    
                                    { loaded && suggestions.length > 0 && (
                                        <div className="suggestions-list">
                                            { suggestions.map( suggestion => (
                                                <div key={ suggestion.id } className="suggestion-item">
                                                    <div className="suggestion-header">
                                                        <span className="anchor-text">{ suggestion.anchor_text }</span>
                                                        <Button
                                                            isSmall
                                                            isSecondary
                                                            onClick={ () => this.insertLink( suggestion ) }
                                                        >
                                                            { webAnalyzerData.strings.insertButton }
                                                        </Button>
                                                    </div>
                                                    <div className="suggestion-content">
                                                        <div className="context" dangerouslySetInnerHTML={{ __html: suggestion.context }}></div>
                                                        <div className="target-url">
                                                            <a href={ suggestion.target_url } target="_blank" rel="noopener noreferrer">
                                                                { suggestion.target_url }
                                                            </a>
                                                        </div>
                                                    </div>
                                                </div>
                                            ) ) }
                                        </div>
                                    ) }
                                </div>
                            </div>
                        </PanelBody>
                    </PluginSidebar>
                </Fragment>
            );
        }
    }
    
    /**
     * Map editor data to component props
     */
    const mapStateToProps = ( select ) => {
        const { getCurrentPostId, getEditedPostContent } = select( 'core/editor' );
        
        return {
            postId: getCurrentPostId(),
            content: getEditedPostContent()
        };
    };
    
    /**
     * Map dispatch actions to component props
     */
    const mapDispatchToProps = ( dispatch ) => {
        return {
            insertLink: ( text, url ) => {
                const { insertText, applyFormat } = dispatch( 'core/rich-text' );
                
                // This is a simplified version. In reality, you would need to:
                // 1. Find the appropriate blocks and ranges where to insert links
                // 2. Check if the text exists in those blocks
                // 3. Apply the link format only to the matching text
                
                // Since this is complex and requires deep editor integration,
                // for now we'll create a basic function that tries to insert links
                
                insertText( text );
                applyFormat( {
                    type: 'core/link',
                    attributes: {
                        url: url
                    }
                } );
            }
        };
    };
    
    // Create the connected component
    const ConnectedWebAnalyzerSidebar = compose(
        withSelect( mapStateToProps ),
        withDispatch( mapDispatchToProps )
    )( WebAnalyzerSidebar );
    
    // Register the plugin
    registerPlugin( 'web-analyzer-sidebar', {
        render: ConnectedWebAnalyzerSidebar,
        icon: 'admin-links'
    } );
    
})( window.wp );