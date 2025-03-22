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
    const { PanelBody, Button, Spinner, Notice, TextHighlight } = wp.components;
    const { withSelect, withDispatch } = wp.data;
    const { compose } = wp.compose;
    const { Component, Fragment } = wp.element;
    const apiFetch = wp.apiFetch;
    const { create, toHTMLString, registerFormatType } = wp.richText;
    
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
                loaded: false,
                contextSearchResults: {},
                selectedSuggestion: null
            };
            
            this.analyzeContent = this.analyzeContent.bind( this );
            this.insertLink = this.insertLink.bind( this );
            this.loadSuggestions = this.loadSuggestions.bind( this );
            this.findTextInBlocks = this.findTextInBlocks.bind( this );
            this.highlightSuggestion = this.highlightSuggestion.bind( this );
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
            const { postId, content, title } = this.props;
            
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
                    post_id: postId,
                    content: content,
                    title: title
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
         * Find text matches in blocks for context-aware link insertion
         */
        findTextInBlocks(searchText) {
            const { blocks } = this.props;
            const results = [];
            
            if (!blocks || !searchText) return results;
            
            // Search for exact text in paragraph blocks
            blocks.forEach((block, blockIndex) => {
                if (block.name === 'core/paragraph' && block.attributes.content) {
                    // Create a temporary div to parse HTML content
                    const div = document.createElement('div');
                    div.innerHTML = block.attributes.content;
                    const textContent = div.textContent;
                    
                    if (textContent.includes(searchText)) {
                        results.push({
                            blockIndex,
                            blockClientId: block.clientId,
                            text: searchText,
                            type: 'exact'
                        });
                    }
                }
            });
            
            // If no exact matches, find fuzzy matches (substrings)
            if (results.length === 0) {
                const words = searchText.split(' ');
                if (words.length > 2) {
                    // Try with the first 3 words if search text is long
                    const shorterSearch = words.slice(0, 3).join(' ');
                    
                    blocks.forEach((block, blockIndex) => {
                        if (block.name === 'core/paragraph' && block.attributes.content) {
                            const div = document.createElement('div');
                            div.innerHTML = block.attributes.content;
                            const textContent = div.textContent;
                            
                            if (textContent.includes(shorterSearch)) {
                                results.push({
                                    blockIndex,
                                    blockClientId: block.clientId,
                                    text: shorterSearch,
                                    type: 'partial'
                                });
                            }
                        }
                    });
                }
            }
            
            return results;
        }
        
        /**
         * Highlight a suggestion in the editor
         */
        highlightSuggestion(suggestion) {
            const { selectBlock } = this.props;
            const contextSearchResults = this.findTextInBlocks(suggestion.anchor_text);
            
            this.setState({ 
                contextSearchResults,
                selectedSuggestion: suggestion
            });
            
            // If we found matching blocks, select the first one
            if (contextSearchResults.length > 0) {
                selectBlock(contextSearchResults[0].blockClientId);
            }
        }
        
        /**
         * Insert a link into the editor
         */
        insertLink(suggestion) {
            const { replaceBlock, getBlock } = this.props;
            const { contextSearchResults } = this.state;
            
            // If no search results, try to find matches now
            let searchResults = contextSearchResults;
            if (!searchResults || Object.keys(searchResults).length === 0) {
                searchResults = this.findTextInBlocks(suggestion.anchor_text);
            }
            
            if (searchResults.length === 0) {
                // No exact match found, show error with guidance
                this.setState({
                    error: __('Could not find exact text to link. Try placing your cursor where you want the link and click "Insert at Cursor" instead.', 'web-analyzer')
                });
                return;
            }
            
            // We found at least one match, use the first one
            const match = searchResults[0];
            const block = getBlock(match.blockClientId);
            
            if (!block) {
                this.setState({
                    error: __('Block not found. Please try again.', 'web-analyzer')
                });
                return;
            }
            
            // Get the content and replace the text with a link
            let content = block.attributes.content;
            const linkHtml = `<a href="${suggestion.target_url}">${match.text}</a>`;
            
            // Handle exact and partial matches differently
            if (match.type === 'exact') {
                content = content.replace(match.text, linkHtml);
            } else {
                // For partial matches, we need to be more careful
                const div = document.createElement('div');
                div.innerHTML = content;
                const textContent = div.textContent;
                
                const startPos = textContent.indexOf(match.text);
                if (startPos >= 0) {
                    // Extract HTML carefully to preserve all tags
                    const beforeText = content.substring(0, startPos);
                    const afterText = content.substring(startPos + match.text.length);
                    content = beforeText + linkHtml + afterText;
                }
            }
            
            // Create updated block
            const newAttributes = {
                ...block.attributes,
                content: content
            };
            
            // Replace the block with updated content
            replaceBlock(match.blockClientId, {
                ...block,
                attributes: newAttributes
            });
            
            // Mark as applied in the database
            apiFetch({
                path: `/wp/v2/web-analyzer/apply-suggestion/${suggestion.id}`,
                method: 'POST'
            }).catch(error => {
                console.error('Failed to mark suggestion as applied', error);
            });
            
            // Clear search results
            this.setState({
                contextSearchResults: {},
                selectedSuggestion: null
            });
        }
        
        /**
         * Insert link at current cursor position
         */
        insertLinkAtCursor(suggestion) {
            const { insertLinkAtCursor } = this.props;
            
            if (!insertLinkAtCursor) {
                this.setState({
                    error: __('Cannot insert link - editor not ready', 'web-analyzer')
                });
                return;
            }
            
            insertLinkAtCursor(suggestion.anchor_text, suggestion.target_url);
            
            // Mark as applied in the database
            apiFetch({
                path: `/wp/v2/web-analyzer/apply-suggestion/${suggestion.id}`,
                method: 'POST'
            }).catch(error => {
                console.error('Failed to mark suggestion as applied', error);
            });
        }
        
        /**
         * Render the component
         */
        render() {
            const { isAnalyzing, error, suggestions, loaded, selectedSuggestion, contextSearchResults } = this.state;
            
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
                                                <div 
                                                    key={ suggestion.id } 
                                                    className={`suggestion-item ${selectedSuggestion && selectedSuggestion.id === suggestion.id ? 'selected' : ''}`}
                                                >
                                                    <div className="suggestion-header">
                                                        <span className="anchor-text">{ suggestion.anchor_text }</span>
                                                        <div className="suggestion-actions">
                                                            <Button
                                                                isSmall
                                                                isSecondary
                                                                onClick={ () => this.highlightSuggestion(suggestion) }
                                                                title={ __('Find text in editor', 'web-analyzer') }
                                                            >
                                                                { __('Find', 'web-analyzer') }
                                                            </Button>
                                                            <Button
                                                                isSmall
                                                                isPrimary
                                                                onClick={ () => this.insertLink(suggestion) }
                                                                title={ __('Insert link at found text location', 'web-analyzer') }
                                                            >
                                                                { __('Insert', 'web-analyzer') }
                                                            </Button>
                                                            <Button
                                                                isSmall
                                                                variant="tertiary"
                                                                onClick={ () => this.insertLinkAtCursor(suggestion) }
                                                                title={ __('Insert at current cursor position', 'web-analyzer') }
                                                            >
                                                                { __('At Cursor', 'web-analyzer') }
                                                            </Button>
                                                        </div>
                                                    </div>
                                                    <div className="suggestion-content">
                                                        <div className="confidence">
                                                            <span className="label">{ __('Confidence', 'web-analyzer') }: </span>
                                                            <span className="value">{ Math.round(suggestion.confidence * 100) }%</span>
                                                        </div>
                                                        <div className="context" dangerouslySetInnerHTML={{ __html: suggestion.context }}></div>
                                                        <div className="target-url">
                                                            <a href={ suggestion.target_url } target="_blank" rel="noopener noreferrer">
                                                                { suggestion.target_title || suggestion.target_url }
                                                            </a>
                                                        </div>
                                                    </div>
                                                    
                                                    { selectedSuggestion && selectedSuggestion.id === suggestion.id && contextSearchResults.length > 0 && (
                                                        <div className="search-results">
                                                            <p className="search-results-heading">{ __('Found in', 'web-analyzer') } { contextSearchResults.length } { contextSearchResults.length === 1 ? __('location', 'web-analyzer') : __('locations', 'web-analyzer') }</p>
                                                        </div>
                                                    ) }
                                                    
                                                    { selectedSuggestion && selectedSuggestion.id === suggestion.id && contextSearchResults.length === 0 && (
                                                        <div className="search-results">
                                                            <p className="search-results-heading">{ __('Text not found in content', 'web-analyzer') }</p>
                                                        </div>
                                                    ) }
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
        const { getCurrentPostId, getEditedPostContent, getEditedPostAttribute, getBlocks } = select( 'core/editor' );
        
        return {
            postId: getCurrentPostId(),
            content: getEditedPostContent(),
            title: getEditedPostAttribute('title'),
            blocks: getBlocks()
        };
    };
    
    /**
     * Map dispatch actions to component props
     */
    const mapDispatchToProps = ( dispatch ) => {
        const { replaceBlock, insertBlock, selectBlock } = dispatch( 'core/block-editor' );
        const { getBlock } = select( 'core/block-editor' );
        
        return {
            replaceBlock,
            insertBlock,
            selectBlock,
            getBlock,
            insertLinkAtCursor: ( text, url ) => {
                const { insertText, applyFormat } = dispatch( 'core/rich-text' );
                
                // Insert the text and apply link format
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