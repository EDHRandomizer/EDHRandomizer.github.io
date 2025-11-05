/**
 * Game Mode Controller
 * Coordinates session management, commander generation, and pack code delivery
 */

import { randomizeCommanders } from '../services/commanderService.js';
import { getCardImageUrl } from '../api/scryfall.js';
import { commanderNameToUrl } from '../api/edhrec.js';

export class GameModeController {
    constructor(sessionManager, perkLoader, packConfigGenerator) {
        this.sessionManager = sessionManager;
        this.perkLoader = perkLoader;
        this.packConfigGenerator = packConfigGenerator;
        
        this.currentSession = null;
        this.currentPlayerId = null;
        this.playerCommanderData = {}; // Store generated commanders per player
        this.playerSelectedCommander = {}; // Store selected commander per player
    }

    /**
     * Generate commanders for a specific player with perk effects
     * @param {number} playerNumber - Player number (1-4)
     * @param {Object} perkEffects - perk effects object
     * @param {Object} colorSelections - Color filter selections {selected: ['W', 'U'], mode: 'include'}
     * @param {Object} gameModeOptions - Game mode settings {avatarMode: boolean}
     * @returns {Promise<Array>} Array of commander objects
     */
    async generateCommandersForPlayer(playerNumber, perkEffects, colorSelections = null, gameModeOptions = {}) {
        // Check for Avatar Mode
        const avatarMode = gameModeOptions.avatarMode || false;
        
        // Base configuration
        const timePeriod = avatarMode ? 'Weekly' : 'Monthly'; // Avatar Mode uses Weekly
        const minRank = 1;
        const maxRank = avatarMode ? 9999 : 1400; // Avatar Mode removes rank limit, default caps at 1400
        const excludePartners = true;
        
        // Avatar Mode set filtering (TLA and TLE only)
        const includeSets = avatarMode ? ['TLA', 'TLE'] : null;
        const excludeSets = null;
        
        // Calculate quantity from perk
        const baseQuantity = 3;
        const quantityModifier = perkEffects.commanderQuantity || 0;
        const quantity = baseQuantity + quantityModifier;
        
        // Create normal distribution function centered at 1000 (adjustable by perks)
        // Lower distributionCenter = stronger commanders (lower rank numbers)
        // Higher distributionCenter = weaker commanders (higher rank numbers)
        // Avatar Mode uses flatter distribution (larger sigma) for more uniform selection
        const baseDistributionCenter = 1000;
        const distributionShift = perkEffects.distributionShift || 0; // Negative = stronger, Positive = weaker
        const distributionCenter = baseDistributionCenter + distributionShift;
        const distributionWidth = avatarMode ? 800 : 350; // Avatar Mode: wider/flatter distribution, slightly flatter base
        
        // Normal distribution: exp(-((rank - mean)^2) / (2 * sigma^2))
        const distributionFunc = (rank, min, max) => {
            const exponent = -Math.pow(rank - distributionCenter, 2) / (2 * Math.pow(distributionWidth, 2));
            return Math.exp(exponent);
        };
        
        console.log(`🎲 [COMMANDER-GEN] Player ${playerNumber} - Base: ${baseQuantity}, Modifier: ${quantityModifier}, Total: ${quantity}`);
        console.log(`🎲 [COMMANDER-GEN] Distribution: Center=${distributionCenter} (base=${baseDistributionCenter}, shift=${distributionShift}), Width=${distributionWidth}${avatarMode ? ' (Avatar Mode - FLAT)' : ''}`);
        console.log(`🎲 [COMMANDER-GEN] perk effects:`, perkEffects);
        
        // Handle color filter from perk
        let colors = null;
        let colorMode = 'exactly';
        let numColors = null;
        
        if (colorSelections && colorSelections.selected && colorSelections.selected.length > 0) {
            if (colorSelections.mode === 'exclude') {
                // Exclude mode: commanders CANNOT have any of these colors
                // Use 'atmost' mode with all colors EXCEPT the excluded ones
                const allColors = ['W', 'U', 'B', 'R', 'G'];
                const included = allColors.filter(c => !colorSelections.selected.includes(c));
                colors = included.join('');
                colorMode = 'atmost'; // Commander can only use these colors (not the excluded ones)
            } else if (colorSelections.mode === 'include') {
                // Include mode: commanders MUST have these colors (but can have more)
                colors = colorSelections.selected.join('');
                colorMode = 'including';
            } else if (colorSelections.mode === 'exact') {
                // Exact mode: commanders must have EXACTLY these colors
                colors = colorSelections.selected.join('');
                colorMode = 'exactly';
            }
        }
        
        // Handle salt mode from perk
        const saltMode = perkEffects.saltMode || null;
        
        console.log(`🎮 [GAME-MODE] Avatar Mode: ${avatarMode ? 'ENABLED' : 'DISABLED'}`);
        if (avatarMode) {
            console.log(`🎮 [GAME-MODE] Using Weekly commanders, TLA/TLE sets only, no rank limit`);
        }
        
        try {
            const result = await randomizeCommanders(
                timePeriod,
                minRank,
                maxRank,
                quantity,
                colors,
                colorMode,
                numColors,
                null, // selected_color_counts
                excludePartners,
                null, // min_cmc
                null, // max_cmc
                saltMode, // salt_mode (from perk)
                distributionFunc,  // Use normal distribution centered at distributionCenter
                includeSets,  // Avatar Mode: ['TLA', 'TLE'] or null
                excludeSets   // null
            );
            
            if (!result.success) {
                throw new Error(result.error || 'Failed to generate commanders');
            }
            
            const commanders = result.commanders || [];
            console.log(`✅ [COMMANDER-GEN] Player ${playerNumber} - Generated ${commanders.length} commanders (requested ${quantity})`);
            console.log(`✅ [COMMANDER-GEN] Result:`, result);
            
            // Fetch images and URLs
            for (const commander of commanders) {
                commander.edhrec_url = commanderNameToUrl(commander.name);
                try {
                    commander.image_url = await getCardImageUrl(commander.name);
                } catch (error) {
                    console.error(`Failed to fetch image for ${commander.name}:`, error);
                    commander.image_url = null;
                }
            }
            
            // Store for this player
            this.playerCommanderData[playerNumber] = commanders;
            
            return commanders;
        } catch (error) {
            console.error('Error generating commanders:', error);
            throw error;
        }
    }

    /**
     * Select a commander for a player
     * @param {number} playerNumber - Player number
     * @param {number} commanderIndex - Index in the commander array
     */
    selectCommander(playerNumber, commanderIndex) {
        const commanders = this.playerCommanderData[playerNumber];
        if (!commanders || !commanders[commanderIndex]) {
            throw new Error('Invalid commander selection');
        }
        
        this.playerSelectedCommander[playerNumber] = commanderIndex;
    }

    /**
     * Lock in commander for current player
     * @param {number} playerNumber - Player number
     * @returns {Promise<Object>} Updated session data
     */
    async lockCommanderForPlayer(playerNumber) {
        const commanderIndex = this.playerSelectedCommander[playerNumber];
        if (commanderIndex === undefined) {
            throw new Error('No commander selected');
        }
        
        const commanders = this.playerCommanderData[playerNumber];
        const commander = commanders[commanderIndex];
        if (!commander) {
            throw new Error('Invalid commander selection');
        }
        
        const player = this.currentSession.players.find(p => p.number === playerNumber);
        if (!player || player.id !== this.currentPlayerId) {
            throw new Error('Can only lock commander for yourself');
        }
        
        try {
            const session = await this.sessionManager.lockCommander(
                commander.edhrec_url,
                {
                    name: commander.name,
                    rank: commander.rank,
                    image_url: commander.image_url,
                    selectedCommanderIndex: commanderIndex
                }
            );
            
            this.currentSession = session;
            return session;
        } catch (error) {
            console.error('Error locking commander:', error);
            throw error;
        }
    }

    /**
     * Get pack code for a player
     * @param {number} playerNumber - Player number
     * @returns {string|null} Pack code or null if not generated
     */
    getPackCodeForPlayer(playerNumber) {
        const player = this.currentSession.players.find(p => p.number === playerNumber);
        return player ? player.packCode : null;
    }

    /**
     * Check if all players have locked in
     * @returns {boolean}
     */
    allPlayersLocked() {
        if (!this.currentSession) return false;
        return this.currentSession.players.every(p => p.commanderLocked);
    }

    /**
     * Parse color filter selections from perk effects and UI state
     * @param {HTMLElement} colorFilterContainer - Container with color checkboxes
     * @returns {Object|null} {selected: ['W', 'U'], mode: 'include'} or null
     */
    getColorSelectionsFromUI(colorFilterContainer) {
        if (!colorFilterContainer) return null;
        
        const mode = colorFilterContainer.dataset.mode;
        if (!mode) return null;
        
        const selectedColors = [];
        const checkedInputs = colorFilterContainer.querySelectorAll('.color-input:checked');
        checkedInputs.forEach(input => {
            selectedColors.push(input.value);
        });
        
        if (selectedColors.length === 0 && mode !== 'exact') {
            return null; // No colors selected
        }
        
        return {
            selected: selectedColors,
            mode: mode
        };
    }
}

