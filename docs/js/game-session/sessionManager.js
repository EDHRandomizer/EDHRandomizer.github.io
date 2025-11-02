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
        this.pollingRate = 2000; // Poll every 2 seconds for real-time feel
        this.updateCallbacks = [];
    }

    /**
     * Create a new game session
     * @param {string} playerName - Player's display name
     * @param {number} powerupsCount - Number of powerups per player (default 3)
     * @returns {Promise<Object>} - { sessionCode, playerId, sessionData }
     */
    async createSession(playerName = '', powerupsCount = 3) {
        try {
            const response = await fetch(`${this.apiBase}/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    playerName: playerName.trim(),
                    powerupsCount: parseInt(powerupsCount) || 3
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
            const response = await fetch(`${this.apiBase}/join`, {
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
            const response = await fetch(`${this.apiBase}/update-name`, {
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
            const response = await fetch(`${this.apiBase}/${this.currentSession}`);

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
     * Roll powerups for all players (host only)
     * @returns {Promise<Object>} - Updated session data with powerups
     */
    async rollPowerups() {
        if (!this.currentSession) {
            throw new Error('No active session');
        }

        try {
            const response = await fetch(`${this.apiBase}/roll-powerups`, {
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
                throw new Error(error.message || `Failed to roll powerups: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Error rolling powerups:', error);
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
            const response = await fetch(`${this.apiBase}/lock-commander`, {
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
            const response = await fetch(`${this.apiBase}/update-commanders`, {
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
            const response = await fetch(`${this.apiBase}/generate-pack-codes`, {
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
            const response = await fetch(`${this.apiBase}/pack/${packCode}`);

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
     * Start polling for session updates
     */
    startPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }

        this.pollingInterval = setInterval(async () => {
            try {
                const sessionData = await this.getSession();
                this.notifyUpdateCallbacks(sessionData);
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, this.pollingRate);
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
