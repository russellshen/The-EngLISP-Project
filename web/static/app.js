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
    
    // CodeMirror Editor Containers
    const containerEnglisp = document.getElementById('input-englisp-container');
    const containerMinimalist = document.getElementById('input-minimalist-container');
    
    const btnGenEnglisp = document.getElementById('btn-gen-englisp');
    const btnGenMinimalist = document.getElementById('btn-gen-minimalist');
    
    // Tabs
    const tabVisual = document.getElementById('tab-visual');
    const tabText = document.getElementById('tab-text');

    // Compiler Elements
    const compilerTabCl = document.getElementById('compiler-tab-cl');
    const compilerTabScheme = document.getElementById('compiler-tab-scheme');
    const compilerTabClojure = document.getElementById('compiler-tab-clojure');
    const compilerTabSql = document.getElementById('compiler-tab-sql');
    const compilerTabCypher = document.getElementById('compiler-tab-cypher');
    const compilerTabMongodb = document.getElementById('compiler-tab-mongodb');
    const compiledCodeOutput = document.getElementById('compiled-code-output');
    let currentCompilerTarget = 'common-lisp';

    // ==========================================
    // INITIALIZE CODEMIRROR INSTANCES
    // ==========================================
    const editorEnglisp = CodeMirror(containerEnglisp, {
        mode: 'commonlisp',
        theme: 'dracula',
        lineNumbers: false,
        autoCloseBrackets: true,
        matchBrackets: true,
        value: '; Waiting for input...'
    });

    const editorMinimalist = CodeMirror(containerMinimalist, {
        mode: 'commonlisp',
        theme: 'dracula',
        lineNumbers: false,
        autoCloseBrackets: true,
        matchBrackets: true,
        value: '; Waiting for input...'
    });

    // Parenthesis Matching Real-time Validator
    let toastTimeout = null;
    function checkParentheses(editor, container) {
        const val = editor.getValue();
        let openCount = 0;
        let closeCount = 0;
        for (let char of val) {
            if (char === '(') openCount++;
            else if (char === ')') closeCount++;
        }
        if (openCount !== closeCount) {
            container.classList.add('error-glow');
            if (toastTimeout) clearTimeout(toastTimeout);
            toastTimeout = setTimeout(() => {
                showToast(`Parentheses mismatch! (${openCount} open, ${closeCount} closed)`, 'error');
            }, 1200);
        } else {
            container.classList.remove('error-glow');
        }
    }

    editorEnglisp.on('change', () => {
        checkParentheses(editorEnglisp, containerEnglisp);
        fetchCompiledCode();
    });

    editorMinimalist.on('change', () => {
        checkParentheses(editorMinimalist, containerMinimalist);
    });

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
        triggerReversePipelineFromEngLISP(editorEnglisp.getValue());
    });

    btnGenMinimalist.addEventListener('click', () => {
        triggerReversePipelineFromMinimalist(editorMinimalist.getValue());
    });

    // Reset Active States on Compiler Tabs
    function resetCompilerTabs() {
        compilerTabCl.classList.remove('active');
        compilerTabScheme.classList.remove('active');
        if (compilerTabClojure) compilerTabClojure.classList.remove('active');
        compilerTabSql.classList.remove('active');
        compilerTabCypher.classList.remove('active');
        compilerTabMongodb.classList.remove('active');
    }

    // Compiler Tab Listeners
    compilerTabCl.addEventListener('click', () => {
        resetCompilerTabs();
        compilerTabCl.classList.add('active');
        currentCompilerTarget = 'common-lisp';
        fetchCompiledCode();
    });

    compilerTabScheme.addEventListener('click', () => {
        resetCompilerTabs();
        compilerTabScheme.classList.add('active');
        currentCompilerTarget = 'scheme';
        fetchCompiledCode();
    });

    compilerTabSql.addEventListener('click', () => {
        resetCompilerTabs();
        compilerTabSql.classList.add('active');
        currentCompilerTarget = 'sql';
        fetchCompiledCode();
    });

    compilerTabCypher.addEventListener('click', () => {
        resetCompilerTabs();
        compilerTabCypher.classList.add('active');
        currentCompilerTarget = 'cypher';
        fetchCompiledCode();
    });

    compilerTabMongodb.addEventListener('click', () => {
        resetCompilerTabs();
        compilerTabMongodb.classList.add('active');
        currentCompilerTarget = 'mongodb';
        fetchCompiledCode();
    });

    if (compilerTabClojure) {
        compilerTabClojure.addEventListener('click', () => {
            resetCompilerTabs();
            compilerTabClojure.classList.add('active');
            currentCompilerTarget = 'clojure';
            fetchCompiledCode();
        });
    }

    // Voice Input Setup
    const btnVoiceInput = document.getElementById('btn-voice-input');
    let voiceRecognition = null;
    let isRecording = false;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition && btnVoiceInput) {
        voiceRecognition = new SpeechRecognition();
        voiceRecognition.continuous = false;
        voiceRecognition.interimResults = false;

        voiceRecognition.onstart = () => {
            isRecording = true;
            btnVoiceInput.classList.add('recording');
        };

        voiceRecognition.onend = () => {
            isRecording = false;
            btnVoiceInput.classList.remove('recording');
        };

        voiceRecognition.onerror = (e) => {
            console.error('Speech recognition error:', e);
            isRecording = false;
            btnVoiceInput.classList.remove('recording');
            showToast('Voice input failed or was blocked.', 'error');
        };

        voiceRecognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            if (transcript) {
                inputNl.value = transcript;
                appendConsoleLog(`Speech recognized: "${transcript}"`, 'system-msg');
            }
        };

        btnVoiceInput.addEventListener('click', () => {
            if (isRecording) {
                voiceRecognition.stop();
            } else {
                const langMode = document.getElementById('select-lang').value;
                if (langMode === 'fr') {
                    voiceRecognition.lang = 'fr-FR';
                } else {
                    voiceRecognition.lang = 'en-US';
                }
                voiceRecognition.start();
            }
        });
    } else if (btnVoiceInput) {
        btnVoiceInput.style.display = 'none';
    }

    // RDF/Turtle Export
    const btnExportRdf = document.getElementById('btn-export-rdf');
    if (btnExportRdf) {
        btnExportRdf.addEventListener('click', async () => {
            try {
                const response = await fetch('/api/world/export');
                if (!response.ok) {
                    throw new Error('Failed to export world state.');
                }
                const turtleText = await response.text();
                
                const blob = new Blob([turtleText], { type: 'text/turtle' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'world_state.ttl';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                showToast('RDF/Turtle exported successfully.', 'success');
            } catch (err) {
                console.error(err);
                showToast('Failed to export RDF/Turtle database.', 'error');
            }
        });
    }

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
        editorEnglisp.setValue(pipeline.stage3_englisp);
        editorMinimalist.setValue(pipeline.stage4_minimalist);
        
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
        editorEnglisp.setValue(pipeline.stage3_englisp);
        editorMinimalist.setValue(pipeline.stage4_minimalist);
        
        if (pipeline.detected_lang) {
            document.getElementById('select-lang').value = pipeline.detected_lang;
        }
        
        // Render SVG tree
        renderSVGTree(pipeline.stage2_xbar_json);
        fetchCompiledCode();
    }

    async function fetchCompiledCode() {
        const expr = editorEnglisp.getValue().trim();
        if (!expr || expr.startsWith(';')) {
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
        xbarSvg.innerHTML = '';
        if (!rootNode) return;

        let leavesCount = 0;
        function assignCoordinates(node, depth) {
            node.depth = depth;
            if (!node.children || node.children.length === 0) {
                node.leafIndex = leavesCount;
                leavesCount++;
                return;
            }
            node.children.forEach(child => {
                assignCoordinates(child, depth + 1);
            });
        }
        assignCoordinates(rootNode, 0);

        const width = xbarVisualContainer.clientWidth || 800;
        const height = 450;
        const topMargin = 40;
        const bottomMargin = 60;
        const sideMargin = 45;
        
        const verticalSpacing = (height - topMargin - bottomMargin) / (getMaxDepth(rootNode) || 1);
        const horizontalSpacing = (width - sideMargin * 2) / Math.max(1, leavesCount - 1);

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

        xbarSvg.setAttribute('viewBox', `0 0 ${width} ${height}`);

        function drawLinks(node) {
            if (!node.children) return;
            node.children.forEach(child => {
                const link = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                const midY = (node.y + child.y) / 2;
                const pathData = `M ${node.x} ${node.y} C ${node.x} ${midY}, ${child.x} ${midY}, ${child.x} ${child.y}`;
                link.setAttribute('d', pathData);
                link.setAttribute('class', 'tree-link');
                xbarSvg.appendChild(link);
                drawLinks(child);
            });
        }
        drawLinks(rootNode);

        function drawNodes(node) {
            const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            g.setAttribute('class', 'tree-node');
            
            const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
            circle.setAttribute('cx', node.x);
            circle.setAttribute('cy', node.y);
            circle.setAttribute('r', 16);
            
            let categoryClass = 'phrase-node';
            if (node.category.endsWith("'")) {
                categoryClass = 'bar-node';
            } else if (node.category.length <= 2 && node.category === node.category.toUpperCase()) {
                categoryClass = 'head-node';
            }
            circle.setAttribute('class', `tree-node-circle ${categoryClass}`);
            
            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', node.x);
            text.setAttribute('y', node.y + 4);
            text.setAttribute('class', 'tree-node-text');
            text.textContent = node.category;

            g.appendChild(circle);
            g.appendChild(text);

            if (node.label !== undefined && node.label !== null) {
                const leafText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                leafText.setAttribute('x', node.x);
                leafText.setAttribute('y', node.y + 35);
                leafText.setAttribute('class', 'tree-leaf-text');
                leafText.textContent = node.label;
                
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
            worldFactsList.innerHTML = '<li class="empty-state">No facts in the database. Use the console or sandbox to populate.</li>';
            return;
        }

        facts.forEach(fact => {
            const li = document.createElement('li');
            const pred = fact[0];
            const args = fact.slice(1);
            li.textContent = `${pred}(${args.join(', ')})`;
            worldFactsList.appendChild(li);
        });
    }

    async function executeConsoleCommand(cmd) {
        cmd = cmd.trim();
        if (!cmd) return;

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

        await fetchWorldState();
    }

    function appendConsoleLog(text, className) {
        const div = document.createElement('div');
        div.className = `log-entry ${className}`;
        div.innerHTML = text;
        consoleLog.appendChild(div);
        consoleLog.scrollTop = consoleLog.scrollHeight;
    }

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

    fetchWorldState();

    // ==========================================
    // INTERACTIVE AGENT SANDBOX LOOP
    // ==========================================
    const btnToggleSim = document.getElementById('btn-toggle-sim');
    const simSpeed = document.getElementById('sim-speed');
    const speedVal = document.getElementById('speed-val');
    const btnClearAgentLogs = document.getElementById('btn-clear-agent-logs');
    const agentLogs = document.getElementById('agent-logs');
    
    const nodeAlice = document.getElementById('node-alice');
    const nodeBob = document.getElementById('node-bob');
    const nodeCharlie = document.getElementById('node-charlie');
    
    let simIntervalId = null;
    let simStep = 0;
    
    const aliceObservations = [
        "The dog chased the cat.",
        "The fox is lazy.",
        "The cat runs.",
        "A student read a book.",
        "Le chien aboyait.",
        "Le chat court."
    ];
    
    const bobQueries = [
        "(chased ?who cat)",
        "(lazy ?x)",
        "(runs ?x)",
        "(read ?who book)",
        "(chased dog ?who)"
    ];
    
    const charlieRules = [
        "(=> (chased ?x ?y) (scared ?y))",
        "(=> (lazy ?x) (sleeps ?x))"
    ];

    simSpeed.addEventListener('input', () => {
        speedVal.textContent = `${(simSpeed.value / 1000).toFixed(1)}s`;
        if (simIntervalId) {
            stopSimulation();
            startSimulation();
        }
    });

    btnToggleSim.addEventListener('click', () => {
        if (simIntervalId) {
            stopSimulation();
            btnToggleSim.querySelector('span').textContent = 'Start Simulation';
            btnToggleSim.classList.remove('accent-btn');
            btnToggleSim.classList.add('primary-btn');
            appendAgentLog('Simulation stopped.', 'system-msg');
        } else {
            startSimulation();
            btnToggleSim.querySelector('span').textContent = 'Stop Simulation';
            btnToggleSim.classList.remove('primary-btn');
            btnToggleSim.classList.add('accent-btn');
            appendAgentLog('Simulation started.', 'system-msg');
        }
    });

    btnClearAgentLogs.addEventListener('click', () => {
        agentLogs.innerHTML = '<div class="log-entry system-msg">Agent logs cleared.</div>';
    });

    function appendAgentLog(msg, className) {
        const div = document.createElement('div');
        div.className = `log-entry ${className}`;
        div.innerHTML = msg;
        agentLogs.appendChild(div);
        agentLogs.scrollTop = agentLogs.scrollHeight;
    }

    function startSimulation() {
        const interval = parseInt(simSpeed.value);
        simIntervalId = setInterval(runSimulationTick, interval);
    }

    function stopSimulation() {
        if (simIntervalId) {
            clearInterval(simIntervalId);
            simIntervalId = null;
        }
        resetNodeAnimations();
    }

    function resetNodeAnimations() {
        nodeAlice.className = 'agent-node';
        nodeBob.className = 'agent-node';
        nodeCharlie.className = 'agent-node';
        nodeAlice.querySelector('.node-status').textContent = 'Idle';
        nodeBob.querySelector('.node-status').textContent = 'Idle';
        nodeCharlie.querySelector('.node-status').textContent = 'Idle';
    }

    async function runSimulationTick() {
        resetNodeAnimations();
        const phase = simStep % 3;
        simStep++;
        
        if (phase === 0) {
            nodeAlice.classList.add('active-pulse-alice');
            nodeAlice.querySelector('.node-status').textContent = 'Observing & Asserting...';
            
            const randSentence = aliceObservations[Math.floor(Math.random() * aliceObservations.length)];
            appendAgentLog(`Alice observing event: "${randSentence}"`, 'agent-alice');
            
            try {
                const response = await fetch('/api/parse', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: randSentence })
                });
                const data = await response.json();
                if (response.ok && data.success) {
                    const fact_str = data.pipeline.stage4_minimalist;
                    appendAgentLog(`Alice parsed and asserted: <code>${fact_str}</code>`, 'agent-alice');
                    fetchWorldState();
                } else {
                    appendAgentLog(`Alice failed to parse observation.`, 'agent-alice');
                }
            } catch (err) {
                appendAgentLog(`Alice connection error.`, 'agent-alice');
            }
        } 
        else if (phase === 1) {
            nodeBob.classList.add('active-pulse-bob');
            nodeBob.querySelector('.node-status').textContent = 'Querying World...';
            
            const randQuery = bobQueries[Math.floor(Math.random() * bobQueries.length)];
            appendAgentLog(`Bob querying world: <code>${randQuery}</code>`, 'agent-bob');
            
            try {
                const response = await fetch('/api/interpret', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ expr: randQuery })
                });
                const data = await response.json();
                if (response.ok) {
                    if (data.bindings && data.bindings.length > 0) {
                        const bindList = data.bindings.map(b => JSON.stringify(b)).join(', ');
                        appendAgentLog(`Bob found matches: <code>${bindList}</code>`, 'agent-bob');
                    } else {
                        appendAgentLog(`Bob found no matches.`, 'agent-bob');
                    }
                } else {
                    appendAgentLog(`Bob query evaluation failed.`, 'agent-bob');
                }
            } catch (err) {
                appendAgentLog(`Bob connection error.`, 'agent-bob');
            }
        } 
        else {
            nodeCharlie.classList.add('active-pulse-charlie');
            nodeCharlie.querySelector('.node-status').textContent = 'Applying Inference Rules...';
            
            const randRule = charlieRules[Math.floor(Math.random() * charlieRules.length)];
            appendAgentLog(`Charlie asserting logic rule: <code>${randRule}</code>`, 'agent-charlie');
            
            try {
                const resRule = await fetch('/api/interpret', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ expr: randRule })
                });
                const ruleData = await resRule.json();
                if (resRule.ok && ruleData.success) {
                    appendAgentLog(`Charlie rule asserted successfully. Triggering inference...`, 'agent-charlie');
                    const triggerQuery = randRule.includes("scared") ? "(scared ?who)" : "(sleeps ?who)";
                    const resQuery = await fetch('/api/interpret', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ expr: triggerQuery })
                    });
                    const queryData = await resQuery.json();
                    if (resQuery.ok && queryData.success && queryData.bindings.length > 0) {
                        const bindings = queryData.bindings.map(b => JSON.stringify(b)).join(', ');
                        appendAgentLog(`Charlie inferred: <code>${triggerQuery}</code> matches <code>${bindings}</code>`, 'agent-charlie');
                    } else {
                        appendAgentLog(`Charlie found no matches for inferred rule.`, 'agent-charlie');
                    }
                } else {
                    appendAgentLog(`Charlie rule assertion failed.`, 'agent-charlie');
                }
            } catch (err) {
                appendAgentLog(`Charlie connection error.`, 'agent-charlie');
            }
        }
    }
});
