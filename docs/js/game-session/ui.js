/**
 * Game UI Module
 * Manages the UI state and user interactions for the game mode
 */

import { perkLoader } from './perkLoader.js';
import { configGenerator } from './configGenerator.js';
import { sessionManager } from './sessionManager.js';

class GameUI {
    constructor() {
        this.currentScreen = 'initial';
        this.sessionData = null;
    }

    /**
     * Initialize UI
     */
    async init() {
        try {
            // Load perks data
            await perkLoader.loadPerks();
            console.log('Perks loaded successfully');

            // Register session update callback
            sessionManager.onUpdate(this.handleSessionUpdate.bind(this));

            // Show initial screen
            this.showScreen('initial');
        } catch (error) {
            this.showError('Failed to initialize game: ' + error.message);
        }
    }

    /**
     * Create new game
     */
    async createGame() {
        this.showLoading(true);
        try {
            const result = await sessionManager.createSession();
            this.sessionData = result.sessionData;
            
            // Show lobby screen
            this.showScreen('lobby');
            this.updateLobbyUI(this.sessionData);
            
            this.showLoading(false);
        } catch (error) {
            this.showLoading(false);
            this.showError('Failed to create game: ' + error.message);
        }
    }

    /**
     * Join existing game
     */
    async joinGame() {
        const sessionCode = document.getElementById('joinSessionCode').value.trim().toUpperCase();
        
        if (!sessionCode || sessionCode.length !== 5) {
            this.showError('Please enter a valid 5-character session code');
            return;
        }

        this.showLoading(true);
        try {
            const result = await sessionManager.joinSession(sessionCode);
            this.sessionData = result.sessionData;
            
            // Determine which screen to show based on session state
            if (this.sessionData.state === 'waiting') {
                this.showScreen('lobby');
                this.updateLobbyUI(this.sessionData);
            } else if (this.sessionData.state === 'rolling' || this.sessionData.state === 'selecting') {
                this.showScreen('selection');
                this.updateSelectionUI(this.sessionData);
            } else if (this.sessionData.state === 'complete') {
                this.showScreen('packCodes');
                this.updatePackCodesUI(this.sessionData);
            }
            
            this.showLoading(false);
        } catch (error) {
            this.showLoading(false);
            this.showError('Failed to join game: ' + error.message);
        }
    }

    /**
     * Leave current game
     */
    leaveGame() {
        sessionManager.leaveSession();
        this.sessionData = null;
        this.showScreen('initial');
    }

    /**
     * Roll perks (host only)
     */
    async rollPerks() {
        this.showLoading(true);
        try {
            const result = await sessionManager.rollPerks();
            this.sessionData = result;
            
            // Transition to selection screen
            this.showScreen('selection');
            this.updateSelectionUI(this.sessionData);
            
            this.showLoading(false);
        } catch (error) {
            this.showLoading(false);
            this.showError('Failed to Roll perks: ' + error.message);
        }
    }

    /**
     * Lock in commander selection
     */
    async lockCommander() {
        const commanderUrl = document.getElementById('commanderUrl').value.trim();
        
        if (!commanderUrl) {
            this.showError('Please enter a commander URL');
            return;
        }

        // TODO: Fetch commander data from EDHRec/Scryfall API
        // For now, use placeholder data
        const commanderData = {
            name: 'Commander Name', // Will be populated from API
            colors: ['W', 'U'],
            rank: 50,
            saltScore: 1.5,
            tribal: false,
            partner: false
        };

        // Validate against perk restrictions
        const currentPlayer = sessionManager.getCurrentPlayer(this.sessionData);
        const perk = perkLoader.getPerkById(currentPlayer.perk.id);
        const validation = configGenerator.validateCommander(perk, commanderData);

        if (!validation.valid) {
            this.showError(validation.reason);
            return;
        }

        this.showLoading(true);
        try {
            const result = await sessionManager.lockCommander(commanderUrl, commanderData);
            this.sessionData = result;
            
            // Update UI
            this.updateSelectionUI(this.sessionData);
            
            this.showLoading(false);
        } catch (error) {
            this.showLoading(false);
            this.showError('Failed to lock commander: ' + error.message);
        }
    }

    /**
     * Handle session updates from polling
     */
    handleSessionUpdate(sessionData) {
        this.sessionData = sessionData;

        // Update UI based on current screen
        if (this.currentScreen === 'lobby') {
            this.updateLobbyUI(sessionData);
        } else if (this.currentScreen === 'selection') {
            this.updateSelectionUI(sessionData);
            
            // Check if all players locked in
            if (sessionData.state === 'complete') {
                this.showScreen('packCodes');
                this.updatePackCodesUI(sessionData);
            }
        } else if (this.currentScreen === 'packCodes') {
            this.updatePackCodesUI(sessionData);
        }
    }

    /**
     * Update lobby UI
     */
    updateLobbyUI(sessionData) {
        // Update session code
        document.getElementById('sessionCode').textContent = sessionData.sessionCode;

        // Update player grid
        const playerGrid = document.getElementById('playerGrid');
        playerGrid.innerHTML = '';

        for (let i = 0; i < 4; i++) {
            const player = sessionData.players[i];
            const playerCard = document.createElement('div');
            playerCard.className = 'player-card';
            
            if (player) {
                const isCurrentPlayer = player.id === sessionManager.currentPlayerId;
                if (isCurrentPlayer) {
                    playerCard.classList.add('current-player');
                }

                playerCard.innerHTML = `
                    <div class="player-number">${i + 1}</div>
                    <h3>Player ${i + 1}</h3>
                    <div class="player-status">Ready</div>
                `;
            } else {
                playerCard.innerHTML = `
                    <div class="player-number">${i + 1}</div>
                    <h3>Waiting...</h3>
                    <div class="player-status">Open slot</div>
                `;
            }

            playerGrid.appendChild(playerCard);
        }

        // Enable/disable roll button (only host can roll, need at least 2 players)
        const rollBtn = document.getElementById('rollPerksBtn');
        const isHost = sessionManager.isHost(sessionData);
        const hasEnoughPlayers = sessionData.players.length >= 2;
        rollBtn.disabled = !isHost || !hasEnoughPlayers;
    }

    /**
     * Update selection UI
     */
    updateSelectionUI(sessionData) {
        // Update session code
        document.getElementById('sessionCode2').textContent = sessionData.sessionCode;

        // Get current player
        const currentPlayer = sessionManager.getCurrentPlayer(sessionData);
        if (!currentPlayer || !currentPlayer.perk) {
            return;
        }

        // Display perk
        const perk = perkLoader.getPerkById(currentPlayer.perk.id);
        const powerupContainer = document.getElementById('yourPerk');
        powerupContainer.innerHTML = `
            <div class="perk-card ${perk.rarity}">
                <div class="perk-name">${perk.name}</div>
                <div class="perk-description">${perk.description}</div>
                <div class="perk-flavor">${perk.flavor}</div>
            </div>
        `;

        // Display restrictions
        const restrictionText = configGenerator.getRestrictionText(perk);
        document.getElementById('restrictionText').textContent = restrictionText;

        // Update lock button state
        const lockBtn = document.getElementById('lockCommanderBtn');
        lockBtn.disabled = currentPlayer.commanderLocked;
        lockBtn.textContent = currentPlayer.commanderLocked ? 'Commander Locked ✓' : 'Lock In Commander';

        // Update other players
        const otherPlayersGrid = document.getElementById('otherPlayersGrid');
        otherPlayersGrid.innerHTML = '';

        sessionData.players.forEach((player, index) => {
            if (player.id === sessionManager.currentPlayerId) {
                return; // Skip current player
            }

            const playerCard = document.createElement('div');
            playerCard.className = 'player-card';
            if (player.commanderLocked) {
                playerCard.classList.add('locked');
            }

            const perkName = player.perk ? perkLoader.getPerkById(player.perk.id).name : 'Unknown';
            const status = player.commanderLocked ? '✓ Commander Locked' : 'Selecting commander...';

            playerCard.innerHTML = `
                <div class="player-number">${index + 1}</div>
                <h3>Player ${index + 1}</h3>
                <div style="font-size: 0.9rem; margin: 0.5rem 0;">${perkName}</div>
                <div class="player-status">${status}</div>
            `;

            otherPlayersGrid.appendChild(playerCard);
        });
    }

    /**
     * Update pack codes UI
     */
    updatePackCodesUI(sessionData) {
        const currentPlayer = sessionManager.getCurrentPlayer(sessionData);
        if (!currentPlayer || !currentPlayer.packCode) {
            return;
        }

        // Display current player's pack code
        document.getElementById('yourPackCode').textContent = currentPlayer.packCode;

        // Display all players status
        const allPlayersStatus = document.getElementById('allPlayersStatus');
        allPlayersStatus.innerHTML = '';

        sessionData.players.forEach((player, index) => {
            const playerDiv = document.createElement('div');
            playerDiv.style.cssText = 'padding: 1rem; margin: 0.5rem 0; background: var(--input-bg, #1a1a1a); border-radius: 6px;';
            
            const perkName = perkLoader.getPerkById(player.perk.id).name;
            playerDiv.innerHTML = `
                <strong>Player ${index + 1}</strong><br>
                Perk: ${perkName}<br>
                Commander: ${player.commanderData?.name || 'Unknown'}<br>
                Pack Code: <code>${player.packCode}</code>
            `;

            allPlayersStatus.appendChild(playerDiv);
        });
    }

    /**
     * Copy pack code to clipboard
     */
    async copyPackCode() {
        const packCode = document.getElementById('yourPackCode').textContent;
        try {
            await navigator.clipboard.writeText(packCode);
            // Show brief confirmation
            const btn = event.target;
            const originalText = btn.textContent;
            btn.textContent = 'Copied!';
            setTimeout(() => {
                btn.textContent = originalText;
            }, 2000);
        } catch (error) {
            this.showError('Failed to copy to clipboard');
        }
    }

    /**
     * Start new game
     */
    startNewGame() {
        this.leaveGame();
    }

    /**
     * Show specific screen
     */
    showScreen(screenName) {
        // Hide all screens
        document.getElementById('initialScreen').classList.add('hidden');
        document.getElementById('lobbyScreen').classList.add('hidden');
        document.getElementById('selectionScreen').classList.add('hidden');
        document.getElementById('packCodesScreen').classList.add('hidden');

        // Show requested screen
        if (screenName === 'initial') {
            document.getElementById('initialScreen').classList.remove('hidden');
        } else if (screenName === 'lobby') {
            document.getElementById('lobbyScreen').classList.remove('hidden');
        } else if (screenName === 'selection') {
            document.getElementById('selectionScreen').classList.remove('hidden');
        } else if (screenName === 'packCodes') {
            document.getElementById('packCodesScreen').classList.remove('hidden');
        }

        this.currentScreen = screenName;
    }

    /**
     * Show/hide loading overlay
     */
    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        if (show) {
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        const errorDisplay = document.getElementById('errorDisplay');
        const errorMessage = document.getElementById('errorMessage');
        
        errorMessage.textContent = message;
        errorDisplay.classList.remove('hidden');

        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorDisplay.classList.add('hidden');
        }, 5000);
    }
}

// Export singleton instance
export const gameUI = new GameUI();
