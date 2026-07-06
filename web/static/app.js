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
    // ==========================================
    // API FETCH WRAPPER WITH AUTHENTICATION
    // ==========================================
    const API_BASE_URL = window.ENG_LISP_API_URL || localStorage.getItem('englisp_api_base_url') || '';
    let stripeEnabled = false;

    async function apiFetch(url, options = {}) {
        options.headers = options.headers || {};
        const apiKey = localStorage.getItem('englisp_api_key');
        if (apiKey) {
            options.headers['X-API-Key'] = apiKey;
        }
        const targetUrl = url.startsWith('/') ? `${API_BASE_URL}${url}` : url;
        return fetch(targetUrl, options);
    }

    // Auth elements
    const btnAccountMenu = document.getElementById('btn-account-menu');
    const accountBtnText = document.getElementById('account-btn-text');
    const modalAccount = document.getElementById('modal-account');
    const btnCloseAccount = document.getElementById('btn-close-account');
    
    const viewLoggedOut = document.getElementById('account-logged-out-view');
    const viewLoggedIn = document.getElementById('account-logged-in-view');
    
    const tabAuthLogin = document.getElementById('tab-auth-login');
    const tabAuthSignup = document.getElementById('tab-auth-signup');
    const formAuth = document.getElementById('form-auth');
    const authEmail = document.getElementById('auth-email');
    const authPassword = document.getElementById('auth-password');
    const btnAuthSubmit = document.getElementById('btn-auth-submit');
    
    const profileEmail = document.getElementById('profile-email');
    const profileTier = document.getElementById('profile-tier');
    const profileQuota = document.getElementById('profile-quota');
    const profileApiKey = document.getElementById('profile-apikey');
    const btnCopyApiKey = document.getElementById('btn-copy-apikey');
    const btnToggleSubscription = document.getElementById('btn-toggle-subscription');
    
    const formChangePassword = document.getElementById('form-change-password');
    const pwOld = document.getElementById('pw-old');
    const pwNew = document.getElementById('pw-new');
    
    const btnAuthLogout = document.getElementById('btn-auth-logout');
    
    let currentAuthMode = 'login'; // 'login' or 'signup'

    function updateAccountUI(user) {
        const badgeLexicon = document.getElementById('badge-lexicon-status');
        if (user) {
            stripeEnabled = !!user.stripe_enabled;
            viewLoggedOut.style.display = 'none';
            viewLoggedIn.style.display = 'block';
            
            profileEmail.textContent = user.email;
            profileTier.textContent = user.tier;
            profileQuota.textContent = `${user.quota_used} / ${user.quota_limit} requests used`;
            profileApiKey.value = user.api_key;
            
            accountBtnText.textContent = user.email.split('@')[0];
            
            if (user.tier === 'paid') {
                btnToggleSubscription.textContent = 'Cancel Paid Tier';
                btnToggleSubscription.classList.remove('primary-btn');
                btnToggleSubscription.classList.add('secondary-btn');
                btnToggleSubscription.disabled = false;
                profileTier.style.color = '#10b981';
                profileTier.style.backgroundColor = 'rgba(16, 185, 129, 0.1)';
                profileTier.style.borderColor = 'rgba(16, 185, 129, 0.2)';
                
                if (badgeLexicon) {
                    badgeLexicon.textContent = 'Full Lexicon';
                    badgeLexicon.style.color = '#10b981';
                    badgeLexicon.style.backgroundColor = 'rgba(16, 185, 129, 0.1)';
                    badgeLexicon.style.borderColor = 'rgba(16, 185, 129, 0.3)';
                    badgeLexicon.style.boxShadow = '0 0 10px rgba(16, 185, 129, 0.2)';
                }
            } else if (user.tier === 'admin') {
                btnToggleSubscription.textContent = 'Admin Tier (No Limits)';
                btnToggleSubscription.disabled = true;
                profileTier.style.color = '#f59e0b';
                profileTier.style.backgroundColor = 'rgba(245, 158, 11, 0.1)';
                profileTier.style.borderColor = 'rgba(245, 158, 11, 0.2)';
                
                if (badgeLexicon) {
                    badgeLexicon.textContent = 'Full Lexicon (Admin)';
                    badgeLexicon.style.color = '#f59e0b';
                    badgeLexicon.style.backgroundColor = 'rgba(245, 158, 11, 0.1)';
                    badgeLexicon.style.borderColor = 'rgba(245, 158, 11, 0.3)';
                    badgeLexicon.style.boxShadow = '0 0 10px rgba(245, 158, 11, 0.2)';
                }
            } else {
                btnToggleSubscription.textContent = 'Upgrade to Paid Tier';
                btnToggleSubscription.classList.remove('secondary-btn');
                btnToggleSubscription.classList.add('primary-btn');
                btnToggleSubscription.disabled = false;
                profileTier.style.color = 'var(--accent-cyan)';
                profileTier.style.backgroundColor = 'rgba(34, 211, 238, 0.1)';
                profileTier.style.borderColor = 'rgba(34, 211, 238, 0.2)';
                
                if (badgeLexicon) {
                    badgeLexicon.textContent = 'Sample Lexicon';
                    badgeLexicon.style.color = 'var(--text-secondary)';
                    badgeLexicon.style.backgroundColor = 'rgba(255,255,255,0.05)';
                    badgeLexicon.style.borderColor = 'var(--glass-border)';
                    badgeLexicon.style.boxShadow = 'none';
                }
            }
        } else {
            viewLoggedOut.style.display = 'block';
            viewLoggedIn.style.display = 'none';
            accountBtnText.textContent = 'Account Portal';
            
            if (badgeLexicon) {
                badgeLexicon.textContent = 'Sample Lexicon';
                badgeLexicon.style.color = 'var(--text-secondary)';
                badgeLexicon.style.backgroundColor = 'rgba(255,255,255,0.05)';
                badgeLexicon.style.borderColor = 'var(--glass-border)';
                badgeLexicon.style.boxShadow = 'none';
            }
        }
    }

    async function checkAuthStatus() {
        const apiKey = localStorage.getItem('englisp_api_key');
        try {
            const options = {};
            if (apiKey) {
                options.headers = { 'X-API-Key': apiKey };
            }
            const res = await apiFetch('/api/auth/me', options);
            if (res.ok) {
                const user = await res.json();
                stripeEnabled = !!user.stripe_enabled;
                if (user.authenticated) {
                    updateAccountUI(user);
                } else {
                    updateAccountUI(null);
                }
            } else {
                localStorage.removeItem('englisp_api_key');
                updateAccountUI(null);
            }
        } catch (e) {
            console.error('Auth verification failed', e);
        }
    }

    // Modal view handlers
    btnAccountMenu.addEventListener('click', () => {
        modalAccount.classList.add('active');
        checkAuthStatus();
    });
    
    btnCloseAccount.addEventListener('click', () => {
        modalAccount.classList.remove('active');
    });
    
    modalAccount.addEventListener('click', (e) => {
        if (e.target === modalAccount) {
            modalAccount.classList.remove('active');
        }
    });

    // Recovery elements
    const linkForgotPw = document.getElementById('link-forgot-password');
    const panelAuthMain = document.getElementById('auth-main-panel');
    const panelAuthForgot = document.getElementById('auth-forgot-panel');
    const panelAuthReset = document.getElementById('auth-reset-panel');
    
    const formForgot = document.getElementById('form-forgot');
    const forgotEmail = document.getElementById('forgot-email');
    const btnForgotSubmit = document.getElementById('btn-forgot-submit');
    
    const formReset = document.getElementById('form-reset');
    const resetEmail = document.getElementById('reset-email');
    const resetCode = document.getElementById('reset-code');
    const resetNewPw = document.getElementById('reset-new-password');
    const btnResetSubmit = document.getElementById('btn-reset-submit');
    
    const linksBackToLogin = document.querySelectorAll('.link-back-to-login');

    tabAuthLogin.addEventListener('click', () => {
        currentAuthMode = 'login';
        tabAuthLogin.classList.add('active');
        tabAuthSignup.classList.remove('active');
        btnAuthSubmit.querySelector('span').textContent = 'Log In';
    });
    
    tabAuthSignup.addEventListener('click', () => {
        currentAuthMode = 'signup';
        tabAuthSignup.classList.add('active');
        tabAuthLogin.classList.remove('active');
        btnAuthSubmit.querySelector('span').textContent = 'Sign Up';
    });

    linkForgotPw.addEventListener('click', (e) => {
        e.preventDefault();
        panelAuthMain.style.display = 'none';
        panelAuthForgot.style.display = 'block';
        panelAuthReset.style.display = 'none';
    });
    
    linksBackToLogin.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            panelAuthMain.style.display = 'block';
            panelAuthForgot.style.display = 'none';
            panelAuthReset.style.display = 'none';
        });
    });

    formAuth.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = authEmail.value.trim();
        const password = authPassword.value;
        const endpoint = currentAuthMode === 'login' ? '/api/auth/login' : '/api/auth/register';
        
        btnAuthSubmit.disabled = true;
        try {
            const response = await apiFetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            const data = await response.json();
            if (response.ok) {
                authEmail.value = '';
                authPassword.value = '';
                if (currentAuthMode === 'login') {
                    const key = data.api_key;
                    localStorage.setItem('englisp_api_key', key);
                    showToast('Logged in successfully!', 'success');
                    await checkAuthStatus();
                } else {
                    showToast((data.message || 'Account registered! Please check email to verify.') + ' (Local Dev: Link logged to terminal & web/logs/emails/)', 'success');
                    currentAuthMode = 'login';
                    tabAuthLogin.classList.add('active');
                    tabAuthSignup.classList.remove('active');
                    btnAuthSubmit.querySelector('span').textContent = 'Log In';
                }
            } else {
                showToast(data.detail || 'Authentication failed.', 'error');
            }
        } catch (err) {
            showToast('Connection to auth server failed.', 'error');
        } finally {
            btnAuthSubmit.disabled = false;
        }
    });

    formForgot.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = forgotEmail.value.trim();
        btnForgotSubmit.disabled = true;
        try {
            const res = await apiFetch('/api/auth/forgot-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            const data = await res.json();
            if (res.ok) {
                showToast(data.message, 'success');
                resetEmail.value = email;
                panelAuthForgot.style.display = 'none';
                panelAuthReset.style.display = 'block';
            } else {
                showToast(data.detail || 'Failed to request password reset.', 'error');
            }
        } catch (err) {
            showToast('Connection error.', 'error');
        } finally {
            btnForgotSubmit.disabled = false;
        }
    });
    
    formReset.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = resetEmail.value.trim();
        const passcode = resetCode.value.trim();
        const new_password = resetNewPw.value;
        
        if (new_password.length < 6) {
            showToast('Password must be at least 6 characters.', 'error');
            return;
        }
        
        btnResetSubmit.disabled = true;
        try {
            const res = await apiFetch('/api/auth/reset-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, passcode, new_password })
            });
            const data = await res.json();
            if (res.ok) {
                showToast('Password reset successfully! You can now log in.', 'success');
                resetCode.value = '';
                resetNewPw.value = '';
                panelAuthMain.style.display = 'block';
                panelAuthReset.style.display = 'none';
            } else {
                showToast(data.detail || 'Password reset failed.', 'error');
            }
        } catch (err) {
            showToast('Connection error.', 'error');
        } finally {
            btnResetSubmit.disabled = false;
        }
    });

    btnCopyApiKey.addEventListener('click', () => {
        profileApiKey.select();
        navigator.clipboard.writeText(profileApiKey.value)
            .then(() => showToast('API Key copied to clipboard!', 'success'))
            .catch(() => showToast('Failed to copy key.', 'error'));
    });

    btnToggleSubscription.addEventListener('click', async () => {
        const apiKey = localStorage.getItem('englisp_api_key');
        if (!apiKey) return;
        
        const isCurrentlyPaid = btnToggleSubscription.textContent.includes('Cancel');
        
        if (!isCurrentlyPaid && stripeEnabled) {
            btnToggleSubscription.disabled = true;
            try {
                const res = await apiFetch('/api/auth/stripe-checkout', { method: 'POST' });
                const data = await res.json();
                if (res.ok && data.success) {
                    showToast('Redirecting to Stripe Checkout...', 'success');
                    window.location.href = data.checkout_url;
                } else {
                    showToast(data.detail || 'Failed to create checkout session.', 'error');
                }
            } catch (e) {
                showToast('Failed to connect to billing server.', 'error');
            } finally {
                btnToggleSubscription.disabled = false;
            }
            return;
        }
        
        const duration = isCurrentlyPaid ? 0 : 2592000;
        
        btnToggleSubscription.disabled = true;
        try {
            const res = await apiFetch('/api/auth/subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ duration_seconds: duration })
            });
            const data = await res.json();
            if (res.ok) {
                showToast(duration === 0 ? 'Subscription cancelled successfully.' : 'Upgraded to Paid Tier!', 'success');
                await checkAuthStatus();
            } else {
                showToast(data.detail || 'Failed to update subscription status.', 'error');
            }
        } catch (e) {
            showToast('Connection to billing system failed.', 'error');
        } finally {
            btnToggleSubscription.disabled = false;
        }
    });

    formChangePassword.addEventListener('submit', async (e) => {
        e.preventDefault();
        const old_password = pwOld.value;
        const new_password = pwNew.value;
        
        if (new_password.length < 6) {
            showToast('New password must be at least 6 characters.', 'error');
            return;
        }
        
        const btnChange = formChangePassword.querySelector('button[type="submit"]');
        btnChange.disabled = true;
        try {
            const res = await apiFetch('/api/auth/change-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ old_password, new_password })
            });
            const data = await res.json();
            if (res.ok) {
                showToast('Password updated successfully!', 'success');
                pwOld.value = '';
                pwNew.value = '';
            } else {
                showToast(data.detail || 'Failed to change password.', 'error');
            }
        } catch (err) {
            showToast('Connection to server failed.', 'error');
        } finally {
            btnChange.disabled = false;
        }
    });

    btnAuthLogout.addEventListener('click', () => {
        localStorage.removeItem('englisp_api_key');
        updateAccountUI(null);
        showToast('Logged out successfully.', 'success');
        modalAccount.classList.remove('active');
    });

    // Check auth status on page load
    checkAuthStatus();

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
                const response = await apiFetch('/api/world/export');
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
            const response = await apiFetch('/api/parse', {
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
            const response = await apiFetch('/api/generate-from-englisp', {
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
            const response = await apiFetch('/api/generate-from-minimalist', {
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
        
        const panelSql = document.getElementById('panel-db-sql');
        const panelCypher = document.getElementById('panel-db-cypher');
        if (panelSql && pipeline.compiled_sql) {
            panelSql.textContent = pipeline.compiled_sql;
        }
        if (panelCypher && pipeline.compiled_cypher) {
            panelCypher.textContent = pipeline.compiled_cypher;
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
        
        const panelSql = document.getElementById('panel-db-sql');
        const panelCypher = document.getElementById('panel-db-cypher');
        if (panelSql && pipeline.compiled_sql) {
            panelSql.textContent = pipeline.compiled_sql;
        }
        if (panelCypher && pipeline.compiled_cypher) {
            panelCypher.textContent = pipeline.compiled_cypher;
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
            const response = await apiFetch('/api/compile', {
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
            const response = await apiFetch('/api/world');
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
            const response = await apiFetch('/api/interpret', {
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
            const response = await apiFetch('/api/world/reset', { method: 'POST' });
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

    function forceStopSimulation() {
        if (simIntervalId) {
            stopSimulation();
            btnToggleSim.querySelector('span').textContent = 'Start Simulation';
            btnToggleSim.classList.remove('accent-btn');
            btnToggleSim.classList.add('primary-btn');
            appendAgentLog('Simulation auto-stopped.', 'system-msg');
        }
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
                const response = await apiFetch('/api/parse', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: randSentence })
                });
                
                if (response.status === 429) {
                    showToast('Sandbox rate limit exceeded (5 requests/minute). Please log in to bypass rate limits!', 'error');
                    forceStopSimulation();
                    return;
                } else if (response.status === 402) {
                    showToast('API quota limit exceeded. Please upgrade your subscription!', 'error');
                    forceStopSimulation();
                    return;
                }
                
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
                const response = await apiFetch('/api/interpret', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ expr: randQuery })
                });
                
                if (response.status === 429) {
                    showToast('Sandbox rate limit exceeded (5 requests/minute). Please log in to bypass rate limits!', 'error');
                    forceStopSimulation();
                    return;
                } else if (response.status === 402) {
                    showToast('API quota limit exceeded. Please upgrade your subscription!', 'error');
                    forceStopSimulation();
                    return;
                }
                
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
                const resRule = await apiFetch('/api/interpret', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ expr: randRule })
                });
                
                if (resRule.status === 429) {
                    showToast('Sandbox rate limit exceeded (5 requests/minute). Please log in to bypass rate limits!', 'error');
                    forceStopSimulation();
                    return;
                } else if (resRule.status === 402) {
                    showToast('API quota limit exceeded. Please upgrade your subscription!', 'error');
                    forceStopSimulation();
                    return;
                }
                
                const ruleData = await resRule.json();
                if (resRule.ok && ruleData.success) {
                    appendAgentLog(`Charlie rule asserted successfully. Triggering inference...`, 'agent-charlie');
                    const triggerQuery = randRule.includes("scared") ? "(scared ?who)" : "(sleeps ?who)";
                    
                    const resQuery = await apiFetch('/api/interpret', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ expr: triggerQuery })
                    });
                    
                    if (resQuery.status === 429) {
                        showToast('Sandbox rate limit exceeded (5 requests/minute). Please log in to bypass rate limits!', 'error');
                        forceStopSimulation();
                        return;
                    } else if (resQuery.status === 402) {
                        showToast('API quota limit exceeded. Please upgrade your subscription!', 'error');
                        forceStopSimulation();
                        return;
                    }
                    
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

    // DB Compiler Panel Controls
    const tabDbSql = document.getElementById('tab-db-sql');
    const tabDbCypher = document.getElementById('tab-db-cypher');
    const panelDbSql = document.getElementById('panel-db-sql');
    const panelDbCypher = document.getElementById('panel-db-cypher');

    if (tabDbSql && tabDbCypher) {
        tabDbSql.addEventListener('click', () => {
            tabDbSql.classList.add('active');
            tabDbCypher.classList.remove('active');
            panelDbSql.style.display = 'block';
            panelDbCypher.style.display = 'none';
        });

        tabDbCypher.addEventListener('click', () => {
            tabDbCypher.classList.add('active');
            tabDbSql.classList.remove('active');
            panelDbCypher.style.display = 'block';
            panelDbSql.style.display = 'none';
        });
    }

    // Text-Adventure controls
    const adventureInput = document.getElementById('adventure-input');
    const btnSubmitAdventure = document.getElementById('btn-submit-adventure');
    const btnResetAdventure = document.getElementById('btn-reset-adventure');
    const adventureConsole = document.getElementById('adventure-console');

    const badgeChest = document.getElementById('badge-chest');
    const badgeKey = document.getElementById('badge-key');
    const badgeGate = document.getElementById('badge-gate');

    function appendAdventureLog(msg, type = 'system-msg') {
        const div = document.createElement('div');
        div.className = `log-entry ${type}`;
        if (type === 'player-input') {
            div.style.color = '#38bdf8';
            div.style.fontWeight = 'bold';
            div.innerHTML = `&gt; ${msg}`;
        } else if (type === 'narrative') {
            div.style.color = '#10b981';
            div.innerHTML = msg;
        } else {
            div.style.color = '#94a3b8';
            div.innerHTML = msg;
        }
        adventureConsole.appendChild(div);
        adventureConsole.scrollTop = adventureConsole.scrollHeight;
    }

    function updateAdventureBadges(state) {
        if (!state) return;
        
        if (badgeChest) {
            if (state.chest_opened) {
                badgeChest.textContent = '📦 Chest Opened';
                badgeChest.style.color = '#10b981';
                badgeChest.style.borderColor = 'rgba(16,185,129,0.3)';
                badgeChest.style.background = 'rgba(16,185,129,0.1)';
            } else {
                badgeChest.textContent = '📦 Chest Closed';
                badgeChest.style.color = 'var(--text-secondary)';
                badgeChest.style.borderColor = 'var(--glass-border)';
                badgeChest.style.background = 'rgba(255,255,255,0.05)';
            }
        }
        
        if (badgeKey) {
            if (state.has_key) {
                badgeKey.textContent = '🔑 Has Key';
                badgeKey.style.color = '#10b981';
                badgeKey.style.borderColor = 'rgba(16,185,129,0.3)';
                badgeKey.style.background = 'rgba(16,185,129,0.1)';
            } else {
                badgeKey.textContent = '🔑 No Key';
                badgeKey.style.color = 'var(--text-secondary)';
                badgeKey.style.borderColor = 'var(--glass-border)';
                badgeKey.style.background = 'rgba(255,255,255,0.05)';
            }
        }
        
        if (badgeGate) {
            if (state.gate_unlocked) {
                badgeGate.textContent = '🚪 Gate Unlocked';
                badgeGate.style.color = '#10b981';
                badgeGate.style.borderColor = 'rgba(16,185,129,0.3)';
                badgeGate.style.background = 'rgba(16,185,129,0.1)';
            } else {
                badgeGate.textContent = '🚪 Gate Locked';
                badgeGate.style.color = 'var(--text-secondary)';
                badgeGate.style.borderColor = 'var(--glass-border)';
                badgeGate.style.background = 'rgba(255,255,255,0.05)';
            }
        }
    }

    async function sendAdventureCommand() {
        const text = adventureInput.value.trim();
        if (!text) return;
        
        appendAdventureLog(text, 'player-input');
        adventureInput.value = '';
        btnSubmitAdventure.disabled = true;
        
        try {
            const response = await apiFetch('/api/adventure/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });
            const data = await response.json();
            if (response.ok) {
                if (data.success) {
                    appendAdventureLog(data.message, 'narrative');
                    updateAdventureBadges(data.state);
                    if (data.state.escaped) {
                        appendAdventureLog('🎉 YOU ESCAPED THE CHAMBER! CONGRATULATIONS!', 'narrative');
                    }
                } else {
                    appendAdventureLog(data.message, 'error-msg');
                }
            } else {
                appendAdventureLog(data.detail || 'Error sending command.', 'error-msg');
            }
        } catch (err) {
            appendAdventureLog('Could not connect to the adventure server.', 'error-msg');
        } finally {
            btnSubmitAdventure.disabled = false;
        }
    }

    async function resetAdventureGame() {
        try {
            const response = await apiFetch('/api/adventure/reset', { method: 'POST' });
            const data = await response.json();
            if (response.ok && data.success) {
                adventureConsole.innerHTML = '';
                appendAdventureLog(data.message, 'narrative');
                updateAdventureBadges(data.state);
            }
        } catch (err) {
            appendAdventureLog('Failed to reset the game.', 'error-msg');
        }
    }

    if (btnSubmitAdventure && btnResetAdventure) {
        btnSubmitAdventure.addEventListener('click', sendAdventureCommand);
        adventureInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendAdventureCommand();
        });
        btnResetAdventure.addEventListener('click', resetAdventureGame);
        
        // Initial setup
        resetAdventureGame();
    }

    // Legal Modal Listeners
    const linkTerms = document.getElementById('link-terms');
    const linkPrivacy = document.getElementById('link-privacy');
    const modalTerms = document.getElementById('modal-terms');
    const modalPrivacy = document.getElementById('modal-privacy');
    const btnCloseTerms = document.getElementById('btn-close-terms');
    const btnClosePrivacy = document.getElementById('btn-close-privacy');
    
    if (linkTerms && modalTerms && btnCloseTerms) {
        linkTerms.addEventListener('click', (e) => {
            e.preventDefault();
            modalTerms.classList.add('active');
        });
        btnCloseTerms.addEventListener('click', () => modalTerms.classList.remove('active'));
        modalTerms.addEventListener('click', (e) => {
            if (e.target === modalTerms) modalTerms.classList.remove('active');
        });
    }
    
    if (linkPrivacy && modalPrivacy && btnClosePrivacy) {
        linkPrivacy.addEventListener('click', (e) => {
            e.preventDefault();
            modalPrivacy.classList.add('active');
        });
        btnClosePrivacy.addEventListener('click', () => modalPrivacy.classList.remove('active'));
        modalPrivacy.addEventListener('click', (e) => {
            if (e.target === modalPrivacy) modalPrivacy.classList.remove('active');
        });
    }
});
