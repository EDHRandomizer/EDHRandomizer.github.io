/**
 * Session Manager Module
 * Handles API calls for session management and real-time polling for updates
 */

class SessionManager {
    constructor() {
        this.apiBase = 'https://edhrandomizer-api.vercel.app/api/sessions';
        this.currentSession = null;
        this.currentPlayerId = null;
        this.pollingInterval = null;
        this.pollingRate = 5000; // Reduced from 2s to 5s to reduce server load
        this.updateCallbacks = [];
        this.consecutiveErrors = 0;
        this.maxConsecutiveErrors = 5;
        this.lastSessionState = null;
    }

    /**
     * Fetch with timeout and retry logic
     * @param {string} url - URL to fetch
     * @param {Object} options - Fetch options
     * @param {number} timeout - Timeout in milliseconds
     * @param {number} maxRetries - Maximum retry attempts
     * @returns {Promise<Response>}
     */
    async fetchWithRetry(url, options = {}, timeout = 10000, maxRetries = 3) {
        const startTime = Date.now();
        
        for (let attempt = 0; attempt < maxRetries; attempt++) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), timeout);
                
                console.log(`🌐 [FETCH] ${options.method || 'GET'} ${url} (attempt ${attempt + 1}/${maxRetries})`);
                
                const response = await fetch(url, {
                    ...options,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId);
                
                const duration = Date.now() - startTime;
                
                // Success - return response
                if (response.ok) {
                    console.log(`✅ [FETCH] ${response.status} ${url} (${duration}ms)`);
                    return response;
                }
                
                // Handle rate limiting
                if (response.status === 429) {
                    const retryAfter = response.headers.get('Retry-After');
                    const delay = retryAfter ? parseInt(retryAfter) * 1000 : Math.min(1000 * Math.pow(2, attempt), 10000);
                    console.warn(`⏳ [FETCH] 429 Rate Limited - waiting ${delay}ms (attempt ${attempt + 1}/${maxRetries})`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                    continue;
                }
                
                // Don't retry 4xx errors (except 429)
                if (response.status >= 400 && response.status < 500) {
                    console.error(`❌ [FETCH] ${response.status} ${url} - Client error, not retrying (${duration}ms)`);
                    return response; // Let caller handle the error
                }
                
                // Retry 5xx errors with exponential backoff
                if (attempt < maxRetries - 1) {
                    const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
                    console.warn(`⚠️ [FETCH] ${response.status} ${url} - Server error, retrying in ${delay}ms (${duration}ms elapsed)`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                }
                
            } catch (error) {
                const duration = Date.now() - startTime;
                
                // Check if it was a timeout
                if (error.name === 'AbortError') {
                    console.error(`⏱️ [FETCH] Timeout after ${duration}ms - ${url} (attempt ${attempt + 1}/${maxRetries})`);
                } else {
                    console.error(`💥 [FETCH] Network error - ${error.message} (attempt ${attempt + 1}/${maxRetries}, ${duration}ms)`);
                }
                
                // Timeout or network error
                if (attempt < maxRetries - 1) {
                    const delay = Math.min(1000 * Math.pow(2, attempt), 10000);
                    console.warn(`🔄 [FETCH] Retrying in ${delay}ms...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                } else {
                    throw error;
                }
            }
        }
        
        throw new Error(`Failed after ${maxRetries} attempts`);
    }

    /**
     * Create a new game session
     * @param {string} playerName - Player's display name
     * @param {number} perksCount - Number of perks per player (default 3)
     * @returns {Promise<Object>} - { sessionCode, playerId, sessionData }
     */
    async createSession(playerName = '', perksCount = 3) {
        try {
            const response = await this.fetchWithRetry(`${this.apiBase}/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    playerName: playerName.trim(),
                    perksCount: parseInt(perksCount) || 3
                })
            });

            if (!response.ok) {
                throw new Error(`Failed to create session: ${response.statusText}`);
            }

            const data = await response.json();
            this.currentSession = data.sessionCode;
            this.currentPlayerId = data.playerId;

            // Start polling for updates
            this.startPolling();

            return data;
        } catch (error) {
            console.error('Error creating session:', error);
            throw error;
        }
    }

    /**
     * Join an existing session
     * @param {string} sessionCode - 5-character session code
     * @param {string} playerName - Player's display name
     * @returns {Promise<Object>} - { playerId, sessionData }
     */
    async joinSession(sessionCode, playerName = '') {
        try {
            const response = await this.fetchWithRetry(`${this.apiBase}/join`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    sessionCode: sessionCode.toUpperCase(),
                    playerName: playerName.trim()
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `Failed to join session: ${response.statusText}`);
            }

            const data = await response.json();
            this.currentSession = sessionCode.toUpperCase();
            this.currentPlayerId = data.playerId;

            // Start polling for updates
            this.startPolling();

            return data;
        } catch (error) {
            console.error('Error joining session:', error);
            throw error;
        }
    }

    /**
     * Update player name in session
     * @param {string} playerName - New player name
     * @returns {Promise<Object>} - Updated session data
     */
    async updatePlayerName(playerName) {
        if (!this.currentSession || !this.currentPlayerId) {
            throw new Error('No active session');
        }

        try {
            const response = await this.fetchWithRetry(`${this.apiBase}/update-name`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sessionCode: this.currentSession,
                    playerId: this.currentPlayerId,
                    playerName: playerName
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `Failed to update name: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error updating player name:', error);
            throw error;
        }
    }

    /**
     * Get current session data
     * @returns {Promise<Object>} - Full session data
     */
    async getSession() {
        if (!this.currentSession) {
            throw new Error('No active session');
        }

        try {
            const response = await this.fetchWithRetry(`${this.apiBase}/${this.currentSession}`);

            if (!response.ok) {
                throw new Error(`Failed to get session: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting session:', error);
            throw error;
        }
    }

    /**
     * Roll perks for all players (host only)
     * @returns {Promise<Object>} - Updated session data with perks
     */
    async rollPerks() {
        if (!this.currentSession) {
            throw new Error('No active session');
        }

        try {
            const response = await this.fetchWithRetry(`${this.apiBase}/roll-perks`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sessionCode: this.currentSession,
                    playerId: this.currentPlayerId
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `Failed to roll perks: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error rolling perks:', error);
            throw error;
        }
    }

    /**
     * Lock in commander selection
     * @param {string} commanderUrl - EDHRec or Scryfall URL
     * @param {Object} commanderData - Commander metadata (name, colors, etc.)
     * @returns {Promise<Object>} - Updated session data
     */
    async lockCommander(commanderUrl, commanderData) {
        if (!this.currentSession || !this.currentPlayerId) {
            throw new Error('No active session');
        }

        try {
            const response = await this.fetchWithRetry(`${this.apiBase}/lock-commander`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sessionCode: this.currentSession,
                    playerId: this.currentPlayerId,
                    commanderUrl: commanderUrl,
                    commanderData: commanderData
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `Failed to lock commander: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error locking commander:', error);
            throw error;
        }
    }

    /**
     * Update generated commanders for current player
     * @param {Array} commanders - Array of commander objects
     * @returns {Promise<Object>} - Updated session data
     */
    async updateCommanders(commanders) {
        if (!this.currentSession || !this.currentPlayerId) {
            throw new Error('No active session');
        }

        try {
            const response = await this.fetchWithRetry(`${this.apiBase}/update-commanders`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sessionCode: this.currentSession,
                    playerId: this.currentPlayerId,
                    commanders: commanders
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `Failed to update commanders: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error updating commanders:', error);
            throw error;
        }
    }

    /**
     * Generate pack codes for all players (when all locked in)
     * @returns {Promise<Object>} - { players: [...pack codes...] }
     */
    async generatePackCodes() {
        if (!this.currentSession) {
            throw new Error('No active session');
        }

        try {
            const response = await this.fetchWithRetry(`${this.apiBase}/generate-pack-codes`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    sessionCode: this.currentSession,
                    playerId: this.currentPlayerId
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `Failed to generate pack codes: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error generating pack codes:', error);
            throw error;
        }
    }

    /**
     * Get pack configuration by code
     * @param {string} packCode - Pack code to retrieve
     * @returns {Promise<Object>} - Pack configuration
     */
    async getPackByCode(packCode) {
        try {
            const response = await this.fetchWithRetry(`${this.apiBase}/pack/${packCode}`);

            if (!response.ok) {
                throw new Error(`Failed to get pack: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error getting pack:', error);
            throw error;
        }
    }

    /**
     * Start polling for session updates with circuit breaker
     */
    startPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }

        this.consecutiveErrors = 0;
        const pollStartTime = Date.now();
        let pollCount = 0;

        this.pollingInterval = setInterval(async () => {
            pollCount++;
            const pollId = `poll-${pollCount}`;
            
            try {
                console.log(`📡 [${pollId}] Polling session ${this.currentSession} (rate: ${this.pollingRate}ms, errors: ${this.consecutiveErrors})`);
                
                const sessionData = await this.getSession();
                this.consecutiveErrors = 0; // Reset on success
                
                console.log(`✅ [${pollId}] Session retrieved - state: ${sessionData.state}, players: ${sessionData.players.length}`);
                
                // Adaptive polling: faster when state is changing
                if (sessionData.state === 'selecting' && this.pollingRate > 3000) {
                    console.log('🔄 [POLLING] Speeding up polling (selecting commanders) - 3s interval');
                    this.pollingRate = 3000;
                    this.startPolling(); // Restart with new rate
                } else if (sessionData.state !== 'selecting' && this.pollingRate < 8000) {
                    console.log('🔄 [POLLING] Slowing down polling (stable state) - 8s interval');
                    this.pollingRate = 8000;
                    this.startPolling(); // Restart with new rate
                }
                
                this.notifyUpdateCallbacks(sessionData);
            } catch (error) {
                this.consecutiveErrors++;
                const uptime = ((Date.now() - pollStartTime) / 1000).toFixed(1);
                console.error(`❌ [${pollId}] Polling error ${this.consecutiveErrors}/${this.maxConsecutiveErrors} (uptime: ${uptime}s):`, error);
                
                // Circuit breaker: stop polling after too many failures
                if (this.consecutiveErrors >= this.maxConsecutiveErrors) {
                    console.error(`🔴 [POLLING] Circuit breaker triggered - ${this.maxConsecutiveErrors} consecutive failures. Stopping polling.`);
                    console.error(`📊 [POLLING] Session stats - Total polls: ${pollCount}, Uptime: ${uptime}s, Success rate: ${((pollCount - this.maxConsecutiveErrors) / pollCount * 100).toFixed(1)}%`);
                    this.stopPolling();
                    this.notifyUpdateCallbacks({ 
                        error: 'connection_lost',
                        message: 'Lost connection to server. Please refresh the page.'
                    });
                }
            }
        }, this.pollingRate);
        
        console.log(`✅ [POLLING] Started - session: ${this.currentSession}, rate: ${this.pollingRate}ms, max errors: ${this.maxConsecutiveErrors}`);
    }

    /**
     * Stop polling for updates
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    /**
     * Register callback for session updates
     * @param {Function} callback - Function to call when session updates
     */
    onUpdate(callback) {
        this.updateCallbacks.push(callback);
    }

    /**
     * Notify all update callbacks
     */
    notifyUpdateCallbacks(sessionData) {
        this.updateCallbacks.forEach(callback => {
            try {
                callback(sessionData);
            } catch (error) {
                console.error('Error in update callback:', error);
            }
        });
    }

    /**
     * Leave current session and clean up
     */
    leaveSession() {
        this.stopPolling();
        this.currentSession = null;
        this.currentPlayerId = null;
        this.updateCallbacks = [];
    }

    /**
     * Get current player data from session
     */
    getCurrentPlayer(sessionData) {
        if (!sessionData || !this.currentPlayerId) {
            return null;
        }

        return sessionData.players.find(p => p.id === this.currentPlayerId);
    }

    /**
     * Check if current player is host
     */
    isHost(sessionData) {
        if (!sessionData || !this.currentPlayerId) {
            return false;
        }

        return sessionData.hostId === this.currentPlayerId;
    }
}

// Export both the class and singleton instance
export { SessionManager };
export const sessionManager = new SessionManager();

