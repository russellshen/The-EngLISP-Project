/*
 * Copyright (c) 2026 Russell Shen. All rights reserved.
 *
 * This source code is licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
 * 4.0 International (CC BY-NC-ND 4.0) license.
 *
 * Commercial use, proprietary use, or use in closed-source or revenue-generating projects 
 * is strictly prohibited under this license.
 *
 * For commercial licensing inquiries, please contact:
 * Russell Shen (russellshen7@gmail.com)
 *
 * Licensing terms, scope, and compensation are subject to separate negotiation.
 */

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const inputNl = document.getElementById('input-nl-text');
    const btnParseNl = document.getElementById('btn-parse-nl');
    
    const xbarSvg = document.getElementById('xbar-svg');
    const xbarTreeText = document.getElementById('xbar-tree-text');
    const xbarVisualContainer = document.getElementById('xbar-visual-container');
    
    const inputEnglisp = document.getElementById('input-englisp-text');
    const btnGenEnglisp = document.getElementById('btn-gen-englisp');
    
    const inputMinimalist = document.getElementById('input-minimalist-text');
    const btnGenMinimalist = document.getElementById('btn-gen-minimalist');
    
    // Tabs
    const tabVisual = document.getElementById('tab-visual');
    const tabText = document.getElementById('tab-text');

    // Compiler Elements
    const compilerTabCl = document.getElementById('compiler-tab-cl');
    const compilerTabScheme = document.getElementById('compiler-tab-scheme');
    const compiledCodeOutput = document.getElementById('compiled-code-output');
    let currentCompilerTarget = 'common-lisp';

    
    // Sample Buttons
    document.querySelectorAll('.sample-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const sentence = btn.getAttribute('data-sentence');
            inputNl.value = sentence;
            triggerForwardPipeline(sentence);
        });
    });

    // Tab Switching Logic
    tabVisual.addEventListener('click', () => {
        tabVisual.classList.add('active');
        tabText.classList.remove('active');
        xbarVisualContainer.classList.remove('hidden');
        xbarTreeText.classList.add('hidden');
    });

    tabText.addEventListener('click', () => {
        tabText.classList.add('active');
        tabVisual.classList.remove('active');
        xbarVisualContainer.classList.add('hidden');
        xbarTreeText.classList.remove('hidden');
    });

    // Pipeline Action Listeners
    btnParseNl.addEventListener('click', () => {
        triggerForwardPipeline(inputNl.value);
    });

    btnGenEnglisp.addEventListener('click', () => {
        triggerReversePipelineFromEngLISP(inputEnglisp.value);
    });

    btnGenMinimalist.addEventListener('click', () => {
        triggerReversePipelineFromMinimalist(inputMinimalist.value);
    });

    // Compiler Tab Listeners
    compilerTabCl.addEventListener('click', () => {
        compilerTabCl.classList.add('active');
        compilerTabScheme.classList.remove('active');
        currentCompilerTarget = 'common-lisp';
        fetchCompiledCode();
    });

    compilerTabScheme.addEventListener('click', () => {
        compilerTabScheme.classList.add('active');
        compilerTabCl.classList.remove('active');
        currentCompilerTarget = 'scheme';
        fetchCompiledCode();
    });

    inputEnglisp.addEventListener('input', fetchCompiledCode);

    // Initial load
    triggerForwardPipeline(inputNl.value);


    // ==========================================
    // API CALLS
    // ==========================================

    async function triggerForwardPipeline(text) {
        setLoadingState(true);
        const lang = document.getElementById('select-lang').value;
        try {
            const response = await fetch('/api/parse', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, lang })
            });
            const data = await response.json();
            if (response.ok && data.success) {
                updateUIForward(data.pipeline);
            } else {
                showError(data.detail || 'An error occurred during parsing.');
            }
        } catch (err) {
            showError('Could not connect to the backend server. Make sure it is running.');
        } finally {
            setLoadingState(false);
        }
    }

    async function triggerReversePipelineFromEngLISP(englisp) {
        setLoadingState(true);
        const lang = document.getElementById('select-lang').value;
        try {
            const response = await fetch('/api/generate-from-englisp', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ englisp, lang })
            });
            const data = await response.json();
            if (response.ok && data.success) {
                updateUIReverse(data.pipeline);
            } else {
                showError(data.detail || 'An error occurred during generation.');
            }
        } catch (err) {
            showError('Could not connect to the backend server.');
        } finally {
            setLoadingState(false);
        }
    }

    async function triggerReversePipelineFromMinimalist(minimalist) {
        setLoadingState(true);
        const lang = document.getElementById('select-lang').value;
        try {
            const response = await fetch('/api/generate-from-minimalist', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ minimalist, lang })
            });
            const data = await response.json();
            if (response.ok && data.success) {
                updateUIReverse(data.pipeline);
            } else {
                showError(data.detail || 'An error occurred during generation.');
            }
        } catch (err) {
            showError('Could not connect to the backend server.');
        } finally {
            setLoadingState(false);
        }
    }

    // ==========================================
    // UI UPDATES
    // ==========================================

    function updateUIForward(pipeline) {
        inputNl.value = pipeline.stage1_nl;
        xbarTreeText.textContent = pipeline.stage2_xbar_text;
        inputEnglisp.value = pipeline.stage3_englisp;
        inputMinimalist.value = pipeline.stage4_minimalist;
        
        if (pipeline.detected_lang) {
            document.getElementById('select-lang').value = pipeline.detected_lang;
        }
        
        // Render the interactive SVG tree
        renderSVGTree(pipeline.stage2_xbar_json);
        fetchCompiledCode();
    }

    function updateUIReverse(pipeline) {
        if (pipeline.stage1_nl) {
            inputNl.value = pipeline.stage1_nl;
        }
        xbarTreeText.textContent = pipeline.stage2_xbar_text;
        inputEnglisp.value = pipeline.stage3_englisp;
        inputMinimalist.value = pipeline.stage4_minimalist;
        
        if (pipeline.detected_lang) {
            document.getElementById('select-lang').value = pipeline.detected_lang;
        }
        
        // Render SVG tree
        renderSVGTree(pipeline.stage2_xbar_json);
        fetchCompiledCode();
    }

    async function fetchCompiledCode() {
        const expr = inputEnglisp.value.trim();
        if (!expr) {
            compiledCodeOutput.textContent = 'Waiting for S-expression...';
            return;
        }
        try {
            const response = await fetch('/api/compile', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ expr, target: currentCompilerTarget })
            });
            const data = await response.json();
            if (response.ok && data.success) {
                compiledCodeOutput.textContent = data.code;
            } else {
                compiledCodeOutput.textContent = `; Error compiling: ${data.detail || 'unknown error'}`;
            }
        } catch (err) {
            compiledCodeOutput.textContent = '; Error: Could not connect to compilation server.';
        }
    }


    function setLoadingState(isLoading) {
        if (isLoading) {
            btnParseNl.disabled = true;
            btnGenEnglisp.disabled = true;
            btnGenMinimalist.disabled = true;
            xbarTreeText.textContent = 'Processing...';
        } else {
            btnParseNl.disabled = false;
            btnGenEnglisp.disabled = false;
            btnGenMinimalist.disabled = false;
        }
    }

    function showToast(msg, type = 'error') {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const textSpan = document.createElement('span');
        textSpan.textContent = msg;
        toast.appendChild(textSpan);
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'toast-close';
        closeBtn.innerHTML = '&times;';
        closeBtn.addEventListener('click', () => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 400);
        });
        toast.appendChild(closeBtn);
        
        container.appendChild(toast);
        
        // Trigger reflow
        toast.offsetHeight;
        
        toast.classList.add('show');
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 400);
            }
        }, 5000);
    }

    function showError(msg) {
        showToast(msg, 'error');
        xbarTreeText.textContent = `Error: ${msg}`;
    }


    // ==========================================
    // DYNAMIC SVG TREE RENDERER
    // ==========================================

    function renderSVGTree(rootNode) {
        // Clear SVG
        xbarSvg.innerHTML = '';
        
        if (!rootNode) return;

        // 1. Traverse tree to compute layout depth and calculate leaf positions
        let leavesCount = 0;
        
        function assignCoordinates(node, depth) {
            node.depth = depth;
            if (!node.children || node.children.length === 0) {
                // Leaf/terminal node
                node.leafIndex = leavesCount;
                leavesCount++;
                return;
            }
            
            node.children.forEach(child => {
                assignCoordinates(child, depth + 1);
            });
        }
        
        assignCoordinates(rootNode, 0);

        // Grid parameters
        const width = xbarVisualContainer.clientWidth || 800;
        const height = 450;
        const topMargin = 40;
        const bottomMargin = 60;
        const sideMargin = 45;
        
        const verticalSpacing = (height - topMargin - bottomMargin) / (getMaxDepth(rootNode) || 1);
        const horizontalSpacing = (width - sideMargin * 2) / Math.max(1, leavesCount - 1);

        // 2. Set X positions for nodes
        // Leaves: directly from leafIndex. Parents: average of children's X.
        function computeXPositions(node) {
            if (!node.children || node.children.length === 0) {
                node.x = sideMargin + node.leafIndex * horizontalSpacing;
                node.y = topMargin + node.depth * verticalSpacing;
                return node.x;
            }
            
            let sumX = 0;
            node.children.forEach(child => {
                sumX += computeXPositions(child);
            });
            node.x = sumX / node.children.length;
            node.y = topMargin + node.depth * verticalSpacing;
            return node.x;
        }
        
        computeXPositions(rootNode);

        // Make sure SVG viewBox matches container size
        xbarSvg.setAttribute('viewBox', `0 0 ${width} ${height}`);

        // 3. Draw connection links
        function drawLinks(node) {
            if (!node.children) return;
            node.children.forEach(child => {
                // Draw curve using cubic bezier path or simple line
                const link = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                const midY = (node.y + child.y) / 2;
                
                // Beautiful smooth curves
                const pathData = `M ${node.x} ${node.y} C ${node.x} ${midY}, ${child.x} ${midY}, ${child.x} ${child.y}`;
                
                link.setAttribute('d', pathData);
                link.setAttribute('class', 'tree-link');
                xbarSvg.appendChild(link);
                
                drawLinks(child);
            });
        }
        drawLinks(rootNode);

        // 4. Draw nodes (so they stack above links)
        function drawNodes(node) {
            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            g.setAttribute('class', 'tree-node');
            
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', node.x);
            circle.setAttribute('cy', node.y);
            circle.setAttribute('r', 16);
            
            // Apply category-specific class for colors
            let categoryClass = 'phrase-node';
            if (node.category.endsWith("'")) {
                categoryClass = 'bar-node';
            } else if (node.category.length <= 2 && node.category === node.category.toUpperCase()) {
                categoryClass = 'head-node';
            }
            circle.setAttribute('class', `tree-node-circle ${categoryClass}`);
            
            // Label text in circle
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', node.x);
            text.setAttribute('y', node.y + 4);
            text.setAttribute('class', 'tree-node-text');
            text.textContent = node.category;

            g.appendChild(circle);
            g.appendChild(text);

            // If it's a leaf node with a terminal label, display it below the node
            if (node.label !== undefined && node.label !== null) {
                const leafText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                leafText.setAttribute('x', node.x);
                leafText.setAttribute('y', node.y + 35);
                leafText.setAttribute('class', 'tree-leaf-text');
                leafText.textContent = node.label;
                
                // Add a dashed vertical guide line to terminal word
                const guide = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                guide.setAttribute('x1', node.x);
                guide.setAttribute('y1', node.y + 16);
                guide.setAttribute('x2', node.x);
                guide.setAttribute('y2', node.y + 24);
                guide.setAttribute('stroke', 'rgba(6, 182, 212, 0.4)');
                guide.setAttribute('stroke-width', '1');
                guide.setAttribute('stroke-dasharray', '2,2');
                
                g.appendChild(guide);
                g.appendChild(leafText);
            }

            xbarSvg.appendChild(g);

            if (node.children) {
                node.children.forEach(child => drawNodes(child));
            }
        }
        drawNodes(rootNode);
    }

    function getMaxDepth(node) {
        if (!node.children || node.children.length === 0) return 0;
        let max = 0;
        node.children.forEach(child => {
            const d = getMaxDepth(child);
            if (d > max) max = d;
        });
        return max + 1;
    }

    // ==========================================
    // INTERPRETER & WORLD STATE CONTROLLER
    // ==========================================
    const worldFactsList = document.getElementById('world-facts-list');
    const btnResetWorld = document.getElementById('btn-reset-world');
    const consoleLog = document.getElementById('console-log');
    const consoleInput = document.getElementById('console-input');
    const btnSubmitConsole = document.getElementById('btn-submit-console');

    // Fetch and display world state
    async function fetchWorldState() {
        try {
            const response = await fetch('/api/world');
            const data = await response.json();
            if (response.ok && data.facts) {
                renderWorldFacts(data.facts);
            }
        } catch (err) {
            console.error('Failed to fetch world facts:', err);
        }
    }

    function renderWorldFacts(facts) {
        worldFactsList.innerHTML = '';
        if (facts.length === 0) {
            worldFactsList.innerHTML = '<li class="empty-state">No facts in the database. Use the console to populate.</li>';
            return;
        }

        facts.forEach(fact => {
            const li = document.createElement('li');
            // Format fact as: predicate(arg1, arg2, ...)
            const pred = fact[0];
            const args = fact.slice(1);
            li.textContent = `${pred}(${args.join(', ')})`;
            worldFactsList.appendChild(li);
        });
    }

    // Submit interpreter console command
    async function executeConsoleCommand(cmd) {
        cmd = cmd.trim();
        if (!cmd) return;

        // Log user command
        appendConsoleLog(cmd, 'user-cmd');
        consoleInput.value = '';

        try {
            const response = await fetch('/api/interpret', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ expr: cmd })
            });
            const data = await response.json();

            if (response.ok) {
                if (data.type === 'assertion') {
                    appendConsoleLog(data.message, 'success-msg');
                } else if (data.type === 'query') {
                    if (data.variables) {
                        if (data.success && data.bindings.length > 0) {
                            let matchStr = 'Matches found:<br>';
                            data.bindings.forEach((binding, idx) => {
                                const bindingsList = Object.entries(binding).map(([k, v]) => `${k} = ${v}`).join(', ');
                                matchStr += `  [${idx + 1}] { ${bindingsList} }<br>`;
                            });
                            appendConsoleLog(matchStr, 'success-msg');
                        } else {
                            appendConsoleLog('Query returned no matches.', 'error-msg');
                        }
                    } else {
                        appendConsoleLog(data.message, data.success ? 'success-msg' : 'error-msg');
                    }
                } else {
                    appendConsoleLog(JSON.stringify(data), 'info-msg');
                }
            } else {
                appendConsoleLog(`Error: ${data.detail || 'Execution failed.'}`, 'error-msg');
            }
        } catch (err) {
            appendConsoleLog('Could not connect to the interpreter endpoint.', 'error-msg');
        }

        // Refresh world state
        await fetchWorldState();
    }

    function appendConsoleLog(text, className) {
        const div = document.createElement('div');
        div.className = `log-entry ${className}`;
        div.innerHTML = text;
        consoleLog.appendChild(div);
        // Scroll to bottom
        consoleLog.scrollTop = consoleLog.scrollHeight;
    }

    // Bind Console events
    btnSubmitConsole.addEventListener('click', () => {
        executeConsoleCommand(consoleInput.value);
    });

    consoleInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            executeConsoleCommand(consoleInput.value);
        }
    });

    btnResetWorld.addEventListener('click', async () => {
        try {
            const response = await fetch('/api/world/reset', { method: 'POST' });
            const data = await response.json();
            if (response.ok && data.success) {
                appendConsoleLog(data.message, 'system-msg');
                fetchWorldState();
            }
        } catch (err) {
            appendConsoleLog('Failed to reset world database.', 'error-msg');
        }
    });

    // Hook into triggerForwardPipeline to sync the facts list when user parses a sentence
    const originalTriggerForward = triggerForwardPipeline;
    triggerForwardPipeline = async function(text) {
        await originalTriggerForward(text);
        await fetchWorldState();
    };

    // Initial load of facts list
    fetchWorldState();
});
